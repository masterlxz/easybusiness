from datetime import date
from unittest.mock import patch

import pytest

from app.services.macro_series_service import (
    UnknownSeriesError,
    get_or_refresh_series,
)
from app.sources.bcb_sgs import BcbSgsError


def test_unknown_series_raises(db_session):
    with pytest.raises(UnknownSeriesError):
        get_or_refresh_series(db_session, "selic", ttl_seconds=3600)


def test_first_call_fetches_and_caches(db_session):
    points = [{"reference_month": date(2026, 1, 1), "value_pct": 0.9}]
    with patch(
        "app.services.macro_series_service.fetch_monthly_series", return_value=points
    ) as mock_fetch:
        result = get_or_refresh_series(db_session, "cdi", ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cached"] is False
    assert result["stale"] is False
    assert len(result["data"]) == 1
    assert float(result["data"][0].value_pct) == 0.9


def test_second_call_within_ttl_uses_cache(db_session):
    points = [{"reference_month": date(2026, 1, 1), "value_pct": 0.9}]
    with patch(
        "app.services.macro_series_service.fetch_monthly_series", return_value=points
    ) as mock_fetch:
        get_or_refresh_series(db_session, "cdi", ttl_seconds=3600)
        result = get_or_refresh_series(db_session, "cdi", ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True
    assert result["stale"] is False


def test_upsert_updates_existing_point_instead_of_duplicating(db_session):
    original = [{"reference_month": date(2026, 1, 1), "value_pct": 0.9}]
    revised = [{"reference_month": date(2026, 1, 1), "value_pct": 1.1}]

    with patch(
        "app.services.macro_series_service.fetch_monthly_series", return_value=original
    ):
        get_or_refresh_series(db_session, "cdi", ttl_seconds=0)

    with patch(
        "app.services.macro_series_service.fetch_monthly_series", return_value=revised
    ):
        result = get_or_refresh_series(db_session, "cdi", ttl_seconds=0)

    assert len(result["data"]) == 1
    assert float(result["data"][0].value_pct) == 1.1


def test_source_error_without_cache_propagates(db_session):
    with patch(
        "app.services.macro_series_service.fetch_monthly_series",
        side_effect=BcbSgsError("down"),
    ):
        with pytest.raises(BcbSgsError):
            get_or_refresh_series(db_session, "cdi", ttl_seconds=3600)


def test_source_error_with_cache_serves_stale(db_session):
    points = [{"reference_month": date(2026, 1, 1), "value_pct": 0.9}]
    with patch(
        "app.services.macro_series_service.fetch_monthly_series", return_value=points
    ):
        get_or_refresh_series(db_session, "cdi", ttl_seconds=0)

    with patch(
        "app.services.macro_series_service.fetch_monthly_series",
        side_effect=BcbSgsError("down"),
    ):
        result = get_or_refresh_series(db_session, "cdi", ttl_seconds=0)

    assert result["stale"] is True
    assert len(result["data"]) == 1
