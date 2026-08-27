from datetime import date
from unittest.mock import patch

import pytest
import requests

from app.sources.bcb_sgs import BcbSgsError, fetch_monthly_series


def _fake_response(payload):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return FakeResponse()


def test_fetch_monthly_series_parses_payload():
    payload = [
        {"data": "01/06/2003", "valor": "1.14"},
        {"data": "01/07/2003", "valor": "1.35"},
    ]
    with patch("app.sources.bcb_sgs.requests.get", return_value=_fake_response(payload)):
        result = fetch_monthly_series(4391)

    assert result == [
        {"reference_month": date(2003, 6, 1), "value_pct": 1.14},
        {"reference_month": date(2003, 7, 1), "value_pct": 1.35},
    ]


def test_fetch_monthly_series_wraps_network_error():
    with patch(
        "app.sources.bcb_sgs.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(BcbSgsError):
            fetch_monthly_series(4391)


def test_fetch_monthly_series_wraps_malformed_json():
    with patch("app.sources.bcb_sgs.requests.get", return_value=_fake_response([{"bad": "shape"}])):
        with pytest.raises(BcbSgsError):
            fetch_monthly_series(4391)
