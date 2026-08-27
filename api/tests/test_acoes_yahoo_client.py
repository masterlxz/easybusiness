from datetime import date
from unittest.mock import patch

import pytest
import requests

from app.sources.acoes_yahoo import (
    YahooFinanceError,
    fetch_dividend_payments,
    fetch_dividends_avg,
    fetch_price_history,
    fetch_quote,
    fetch_technicals,
)


def _fake_response(payload):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return FakeResponse()


def _chart_payload(result):
    return {"chart": {"result": [result]}}


def test_fetch_quote_parses_payload():
    payload = _chart_payload(
        {
            "meta": {
                "regularMarketPrice": 38.5,
                "longName": "Petrobras",
                "fullExchangeName": "Sao Paulo",
                "currency": "BRL",
            }
        }
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        result = fetch_quote("PETR4")

    assert result == {
        "price": 38.5,
        "name": "Petrobras",
        "exchange": "Sao Paulo",
        "currency": "BRL",
    }


def test_fetch_quote_wraps_network_error():
    with patch(
        "app.sources.acoes_yahoo.requests.get", side_effect=requests.ConnectionError("boom")
    ):
        with pytest.raises(YahooFinanceError):
            fetch_quote("PETR4")


def test_fetch_quote_wraps_missing_price():
    payload = _chart_payload({"meta": {}})
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        with pytest.raises(YahooFinanceError):
            fetch_quote("PETR4")


def test_fetch_price_history_skips_non_trading_days():
    payload = _chart_payload(
        {
            "timestamp": [1717200000, 1717286400],
            "indicators": {"quote": [{"close": [10.0, None]}]},
        }
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        result = fetch_price_history("PETR4")

    assert len(result) == 1
    assert result[0]["close_price"] == 10.0
    assert isinstance(result[0]["price_date"], date)


def test_fetch_dividends_avg_averages_complete_years():
    # 2020/2021 — safely in the past regardless of when this test runs, no
    # need to mock `datetime.now()`.
    payload = _chart_payload(
        {
            "events": {
                "dividends": {
                    "1": {"date": 1577836800, "amount": 1.0},  # 2020
                    "2": {"date": 1609459200, "amount": 2.0},  # 2021
                }
            }
        }
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        result = fetch_dividends_avg("PETR4")

    assert result == {"avg_dividend_5y": 1.5}


def test_fetch_dividends_avg_returns_none_without_dividends():
    payload = _chart_payload({"events": {}})
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        assert fetch_dividends_avg("MGLU3") is None


def test_fetch_technicals_computes_sma_and_cagr():
    closes = [float(i) for i in range(1, 21)]
    timestamps = [1600000000 + i * 86400 for i in range(20)]
    payload = _chart_payload(
        {"timestamp": timestamps, "indicators": {"quote": [{"close": closes}]}}
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        result = fetch_technicals("PETR4")

    assert result["sma_50"] is None  # not enough candles
    assert result["cagr_5y"] is None  # not enough history


def test_fetch_technicals_raises_without_trading_data():
    payload = _chart_payload({"timestamp": [1], "indicators": {"quote": [{"close": [None]}]}})
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        with pytest.raises(YahooFinanceError):
            fetch_technicals("PETR4")


def test_fetch_dividend_payments_computes_yield():
    payload = _chart_payload(
        {
            "timestamp": [1600000000],
            "indicators": {"quote": [{"close": [20.0]}]},
            "events": {"dividends": {"1": {"date": 1600000000, "amount": 1.0}}},
        }
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        result = fetch_dividend_payments("PETR4")

    assert len(result) == 1
    assert result[0]["amount"] == 1.0
    assert result[0]["price_at_payment"] == 20.0
    assert result[0]["yield_pct"] == 5.0


def test_fetch_dividend_payments_empty_without_dividends():
    payload = _chart_payload(
        {"timestamp": [1600000000], "indicators": {"quote": [{"close": [20.0]}]}, "events": {}}
    )
    with patch("app.sources.acoes_yahoo.requests.get", return_value=_fake_response(payload)):
        assert fetch_dividend_payments("PETR4") == []
