from datetime import date
from unittest.mock import patch

import pytest

from app.services.stock_service import (
    BolsaiTickerNotFoundError,
    NoDividendDataError,
    get_or_refresh_bolsai_fundamentals,
    get_or_refresh_dividend_payments,
    get_or_refresh_dividends_avg,
    get_or_refresh_price_history,
    get_or_refresh_quote,
    get_or_refresh_technicals,
)
from app.sources.acoes_bolsai import BolsaiError
from app.sources.acoes_yahoo import YahooFinanceError


# --- single-row pattern (represented by "quote") --------------------------


def test_quote_first_call_fetches_and_caches(db_session):
    quote = {"price": 38.5, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}
    with patch(
        "app.services.stock_service.fetch_quote", return_value=quote
    ) as mock_fetch:
        result = get_or_refresh_quote(db_session, "PETR4", ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cached"] is False
    assert float(result["price"]) == 38.5


def test_quote_second_call_within_ttl_uses_cache(db_session):
    quote = {"price": 38.5, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}
    with patch(
        "app.services.stock_service.fetch_quote", return_value=quote
    ) as mock_fetch:
        get_or_refresh_quote(db_session, "PETR4", ttl_seconds=3600)
        result = get_or_refresh_quote(db_session, "PETR4", ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_quote_upsert_overwrites_previous_value(db_session):
    original = {"price": 38.5, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}
    revised = {"price": 40.0, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}

    with patch("app.services.stock_service.fetch_quote", return_value=original):
        get_or_refresh_quote(db_session, "PETR4", ttl_seconds=0)
    with patch("app.services.stock_service.fetch_quote", return_value=revised):
        result = get_or_refresh_quote(db_session, "PETR4", ttl_seconds=0)

    assert float(result["price"]) == 40.0


def test_quote_source_error_without_cache_propagates(db_session):
    with patch(
        "app.services.stock_service.fetch_quote", side_effect=YahooFinanceError("down")
    ):
        with pytest.raises(YahooFinanceError):
            get_or_refresh_quote(db_session, "PETR4", ttl_seconds=3600)


def test_quote_source_error_with_cache_serves_stale(db_session):
    quote = {"price": 38.5, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}
    with patch("app.services.stock_service.fetch_quote", return_value=quote):
        get_or_refresh_quote(db_session, "PETR4", ttl_seconds=0)
    with patch(
        "app.services.stock_service.fetch_quote", side_effect=YahooFinanceError("down")
    ):
        result = get_or_refresh_quote(db_session, "PETR4", ttl_seconds=0)

    assert result["stale"] is True
    assert float(result["price"]) == 38.5


# --- append-only list pattern (represented by "price-history") ------------


def test_price_history_first_call_fetches_and_caches(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 10.0}]
    with patch(
        "app.services.stock_service.fetch_price_history", return_value=points
    ) as mock_fetch:
        result = get_or_refresh_price_history(db_session, "PETR4", ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cached"] is False
    assert len(result["data"]) == 1


def test_price_history_rerun_does_not_duplicate_existing_day(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 10.0}]
    with patch("app.services.stock_service.fetch_price_history", return_value=points):
        get_or_refresh_price_history(db_session, "PETR4", ttl_seconds=0)

    more_points = points + [{"price_date": date(2026, 1, 3), "close_price": 10.5}]
    with patch("app.services.stock_service.fetch_price_history", return_value=more_points):
        result = get_or_refresh_price_history(db_session, "PETR4", ttl_seconds=0)

    assert len(result["data"]) == 2
    assert float(result["data"][0].close_price) == 10.0  # unchanged, not overwritten


def test_price_history_source_error_with_cache_serves_stale(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 10.0}]
    with patch("app.services.stock_service.fetch_price_history", return_value=points):
        get_or_refresh_price_history(db_session, "PETR4", ttl_seconds=0)
    with patch(
        "app.services.stock_service.fetch_price_history",
        side_effect=YahooFinanceError("down"),
    ):
        result = get_or_refresh_price_history(db_session, "PETR4", ttl_seconds=0)

    assert result["stale"] is True
    assert len(result["data"]) == 1


# --- technicals / dividend-payments: happy-path smoke tests ---------------


def test_technicals_happy_path(db_session):
    technicals = {"sma_50": None, "sma_100": None, "sma_200": None, "cagr_5y": None, "cagr_10y": None}
    with patch("app.services.stock_service.fetch_technicals", return_value=technicals):
        result = get_or_refresh_technicals(db_session, "PETR4", ttl_seconds=3600)

    assert result["cached"] is False
    assert result["sma_50"] is None


def test_dividend_payments_happy_path(db_session):
    payments = [
        {
            "payment_date": date(2026, 1, 2),
            "amount": 1.0,
            "price_at_payment": 20.0,
            "yield_pct": 5.0,
        }
    ]
    with patch(
        "app.services.stock_service.fetch_dividend_payments", return_value=payments
    ):
        result = get_or_refresh_dividend_payments(db_session, "PETR4", ttl_seconds=3600)

    assert len(result["data"]) == 1
    assert float(result["data"][0].yield_pct) == 5.0


# --- dividends-avg: happy path + "no data" case ----------------------------


def test_dividends_avg_happy_path(db_session):
    with patch(
        "app.services.stock_service.fetch_dividends_avg",
        return_value={"avg_dividend_5y": 1.5},
    ):
        result = get_or_refresh_dividends_avg(db_session, "PETR4", ttl_seconds=3600)

    assert float(result["avg_dividend_5y"]) == 1.5


def test_dividends_avg_no_data_without_cache_raises(db_session):
    with patch("app.services.stock_service.fetch_dividends_avg", return_value=None):
        with pytest.raises(NoDividendDataError):
            get_or_refresh_dividends_avg(db_session, "MGLU3", ttl_seconds=3600)


def test_dividends_avg_no_data_with_existing_cache_keeps_serving_it(db_session):
    with patch(
        "app.services.stock_service.fetch_dividends_avg",
        return_value={"avg_dividend_5y": 1.5},
    ):
        get_or_refresh_dividends_avg(db_session, "PETR4", ttl_seconds=0)

    with patch("app.services.stock_service.fetch_dividends_avg", return_value=None):
        result = get_or_refresh_dividends_avg(db_session, "PETR4", ttl_seconds=0)

    assert float(result["avg_dividend_5y"]) == 1.5


# --- bolsai fundamentals ----------------------------------------------


def _bolsai_fields():
    return {"lpa": 2.5, "vpa": 15.0, "roe": 20.0, "shares_outstanding": 1_000_000.0, "cvm_code": "9512"}


def test_bolsai_fundamentals_first_call_fetches_and_caches(db_session):
    with patch(
        "app.services.stock_service.fetch_bolsai_fundamentals", return_value=_bolsai_fields()
    ) as mock_fetch:
        result = get_or_refresh_bolsai_fundamentals(
            db_session, "PETR4", ttl_seconds=3600, api_key="fake-key"
        )

    mock_fetch.assert_called_with("PETR4", "fake-key")
    assert result["cached"] is False
    assert result["cvm_code"] == "9512"


def test_bolsai_fundamentals_second_call_within_ttl_uses_cache(db_session):
    with patch(
        "app.services.stock_service.fetch_bolsai_fundamentals", return_value=_bolsai_fields()
    ) as mock_fetch:
        get_or_refresh_bolsai_fundamentals(db_session, "PETR4", ttl_seconds=3600, api_key="k")
        result = get_or_refresh_bolsai_fundamentals(
            db_session, "PETR4", ttl_seconds=3600, api_key="k"
        )

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_bolsai_fundamentals_unknown_ticker_without_cache_raises(db_session):
    with patch("app.services.stock_service.fetch_bolsai_fundamentals", return_value=None):
        with pytest.raises(BolsaiTickerNotFoundError):
            get_or_refresh_bolsai_fundamentals(
                db_session, "UNKNOWN1", ttl_seconds=3600, api_key="k"
            )


def test_bolsai_fundamentals_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.services.stock_service.fetch_bolsai_fundamentals", return_value=_bolsai_fields()
    ):
        get_or_refresh_bolsai_fundamentals(db_session, "PETR4", ttl_seconds=0, api_key="k")
    with patch(
        "app.services.stock_service.fetch_bolsai_fundamentals",
        side_effect=BolsaiError("down"),
    ):
        result = get_or_refresh_bolsai_fundamentals(
            db_session, "PETR4", ttl_seconds=0, api_key="k"
        )

    assert result["stale"] is True
