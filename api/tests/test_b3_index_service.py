from datetime import date
from unittest.mock import patch

import pytest

from app.services.b3_index_service import UnknownIndexError, get_or_refresh_index_history
from app.sources.b3_index_stats import B3IndexStatsError


def test_unknown_index_raises(db_session):
    with pytest.raises(UnknownIndexError):
        get_or_refresh_index_history(db_session, "unknown", ttl_seconds=3600)


def test_first_call_fetches_and_caches(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 3000.0}]
    with patch(
        "app.services.b3_index_service.fetch_index_history", return_value=points
    ) as mock_fetch:
        result = get_or_refresh_index_history(db_session, "ifix", ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cached"] is False
    assert len(result["data"]) == 1


def test_second_call_within_ttl_uses_cache(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 3000.0}]
    with patch(
        "app.services.b3_index_service.fetch_index_history", return_value=points
    ) as mock_fetch:
        get_or_refresh_index_history(db_session, "ifix", ttl_seconds=3600)
        result = get_or_refresh_index_history(db_session, "ifix", ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_rerun_does_not_duplicate_existing_day(db_session):
    with patch(
        "app.services.b3_index_service.fetch_index_history",
        return_value=[{"price_date": date(2026, 1, 2), "close_price": 3000.0}],
    ):
        get_or_refresh_index_history(db_session, "ifix", ttl_seconds=0)

    with patch(
        "app.services.b3_index_service.fetch_index_history",
        return_value=[
            {"price_date": date(2026, 1, 2), "close_price": 3000.0},
            {"price_date": date(2026, 1, 3), "close_price": 3010.0},
        ],
    ):
        result = get_or_refresh_index_history(db_session, "ifix", ttl_seconds=0)

    assert len(result["data"]) == 2


def test_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.services.b3_index_service.fetch_index_history",
        return_value=[{"price_date": date(2026, 1, 2), "close_price": 3000.0}],
    ):
        get_or_refresh_index_history(db_session, "ifix", ttl_seconds=0)
    with patch(
        "app.services.b3_index_service.fetch_index_history",
        side_effect=B3IndexStatsError("down"),
    ):
        result = get_or_refresh_index_history(db_session, "ifix", ttl_seconds=0)

    assert result["stale"] is True
    assert len(result["data"]) == 1
