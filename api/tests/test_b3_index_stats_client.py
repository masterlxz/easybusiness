from datetime import date
from unittest.mock import patch

import pytest
import requests

from app.sources.b3_index_stats import B3IndexStatsError, fetch_index_history


def _fake_response(payload):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return FakeResponse()


def test_fetch_index_history_parses_grid_and_skips_empty():
    payload = {
        "results": [
            {"day": 1, "rateValue1": "3,314.09"},
            {"day": 2, "rateValue1": ""},  # no trading day, skipped
            {"day": 31, "rateValue2": "100.00"},  # Feb 31 doesn't exist, skipped
        ]
    }
    with patch("app.sources.b3_index_stats.requests.get", return_value=_fake_response(payload)):
        result = fetch_index_history("IFIX", 2026, 2026)

    assert result == [{"price_date": date(2026, 1, 1), "close_price": 3314.09}]


def test_fetch_index_history_covers_year_range():
    payload = {"results": [{"day": 1, "rateValue1": "100.00"}]}
    with patch(
        "app.sources.b3_index_stats.requests.get", return_value=_fake_response(payload)
    ) as mock_get:
        result = fetch_index_history("IFIX", 2024, 2026)

    assert mock_get.call_count == 3
    assert len(result) == 3


def test_fetch_index_history_wraps_network_error():
    with patch(
        "app.sources.b3_index_stats.requests.get", side_effect=requests.ConnectionError("boom")
    ):
        with pytest.raises(B3IndexStatsError):
            fetch_index_history("IFIX", 2026, 2026)
