from datetime import date
from unittest.mock import patch

import pytest

from app.services.us_stock_service import (
    NoDividendDataError,
    NoFundamentalsDataError,
    TickerNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_fundamentals,
    get_or_refresh_payout,
    get_or_refresh_reit_fundamentals,
    get_or_refresh_us_dividend_payments,
    get_or_refresh_us_dividends_avg,
    get_or_refresh_us_price_history,
    get_or_refresh_us_quote,
    get_or_refresh_us_technicals,
)
from app.sources.acoes_yahoo import YahooFinanceError
from app.sources.sec_edgar import SecEdgarError

CONTACT_EMAIL = "test@example.com"


def _fundamentals():
    return {"lpa": 5.0, "vpa": 10.0, "roe": 20.0, "shares_outstanding": 100.0}


def test_fundamentals_resolves_cik_then_caches(db_session):
    with patch(
        "app.services.us_stock_service.resolve_cik", return_value=320193
    ) as mock_resolve:
        with patch(
            "app.services.us_stock_service.fetch_fundamentals", return_value=_fundamentals()
        ):
            result = get_or_refresh_fundamentals(
                db_session, "aapl", resolution_ttl_seconds=3600, ttl_seconds=3600,
                contact_email=CONTACT_EMAIL,
            )

    assert mock_resolve.called
    assert result["ticker"] == "AAPL"
    assert float(result["lpa"]) == 5.0


def test_fundamentals_reuses_cached_cik_across_endpoints(db_session):
    with patch(
        "app.services.us_stock_service.resolve_cik", return_value=320193
    ) as mock_resolve:
        with patch(
            "app.services.us_stock_service.fetch_fundamentals", return_value=_fundamentals()
        ):
            get_or_refresh_fundamentals(
                db_session, "AAPL", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )
        with patch(
            "app.services.us_stock_service.fetch_payout",
            return_value={"payout_avg_5y": 20.0},
        ):
            get_or_refresh_payout(
                db_session, "AAPL", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )

    assert mock_resolve.call_count == 1


def test_fundamentals_unknown_ticker_without_cache_raises(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=None):
        with pytest.raises(TickerNotFoundError):
            get_or_refresh_fundamentals(
                db_session, "NOTATICKER", resolution_ttl_seconds=3600, ttl_seconds=3600,
                contact_email=CONTACT_EMAIL,
            )


def test_dcf_fundamentals_no_data_without_cache_raises(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=19617):
        with patch(
            "app.services.us_stock_service.fetch_dcf_fundamentals", return_value=None
        ):
            with pytest.raises(NoFundamentalsDataError):
                get_or_refresh_dcf_fundamentals(
                    db_session, "JPM", resolution_ttl_seconds=3600, ttl_seconds=3600,
                    contact_email=CONTACT_EMAIL,
                )


def test_payout_source_error_with_cache_serves_stale(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=320193):
        with patch(
            "app.services.us_stock_service.fetch_payout",
            return_value={"payout_avg_5y": 20.0},
        ):
            get_or_refresh_payout(
                db_session, "AAPL", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )
        with patch(
            "app.services.us_stock_service.fetch_payout", side_effect=SecEdgarError("down")
        ):
            result = get_or_refresh_payout(
                db_session, "AAPL", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )

    assert result["stale"] is True


# --- REIT fundamentals: time-series (append-only), not single-row ---------


def _reit_fields(reference_year=2025, revenue=900.0):
    return {
        "reference_year": reference_year,
        "revenue": revenue,
        "real_estate_property_net": 5000.0,
        "real_estate_property_at_cost": 6000.0,
        "stockholders_equity": 1000.0,
        "net_income": 200.0,
        "eps_diluted": 2.5,
    }


def test_reit_fundamentals_first_call_fetches_and_caches(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=1048286):
        with patch(
            "app.services.us_stock_service.fetch_reit_fundamentals",
            return_value=_reit_fields(),
        ) as mock_fetch:
            result = get_or_refresh_reit_fundamentals(
                db_session, "O", resolution_ttl_seconds=3600, ttl_seconds=3600,
                contact_email=CONTACT_EMAIL,
            )

    assert mock_fetch.called
    assert result["cached"] is False
    assert len(result["data"]) == 1
    assert float(result["data"][0].revenue) == 900.0


def test_reit_fundamentals_rerun_accumulates_new_fiscal_year(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=1048286):
        with patch(
            "app.services.us_stock_service.fetch_reit_fundamentals",
            return_value=_reit_fields(reference_year=2024, revenue=800.0),
        ):
            get_or_refresh_reit_fundamentals(
                db_session, "O", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )
        with patch(
            "app.services.us_stock_service.fetch_reit_fundamentals",
            return_value=_reit_fields(reference_year=2025, revenue=900.0),
        ):
            result = get_or_refresh_reit_fundamentals(
                db_session, "O", resolution_ttl_seconds=3600, ttl_seconds=0,
                contact_email=CONTACT_EMAIL,
            )

    assert len(result["data"]) == 2


def test_reit_fundamentals_ticker_not_found_without_cache_raises(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=None):
        with pytest.raises(TickerNotFoundError):
            get_or_refresh_reit_fundamentals(
                db_session, "NOTATICKER", resolution_ttl_seconds=3600, ttl_seconds=3600,
                contact_email=CONTACT_EMAIL,
            )


def test_reit_fundamentals_no_data_returns_empty_list(db_session):
    with patch("app.services.us_stock_service.resolve_cik", return_value=320193):
        with patch(
            "app.services.us_stock_service.fetch_reit_fundamentals", return_value=None
        ):
            result = get_or_refresh_reit_fundamentals(
                db_session, "AAPL", resolution_ttl_seconds=3600, ttl_seconds=3600,
                contact_email=CONTACT_EMAIL,
            )

    assert result["data"] == []


# --- Yahoo Finance without ".SA" (Fase 1.11.1) -----------------------------


def test_us_quote_first_call_fetches_and_caches(db_session):
    quote = {"price": 150.0, "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"}
    with patch(
        "app.services.us_stock_service.fetch_quote", return_value=quote
    ) as mock_fetch:
        result = get_or_refresh_us_quote(db_session, "AAPL", ttl_seconds=3600)

    mock_fetch.assert_called_with("AAPL", suffix="")
    assert result["cached"] is False
    assert float(result["price"]) == 150.0


def test_us_quote_source_error_without_cache_propagates(db_session):
    with patch(
        "app.services.us_stock_service.fetch_quote", side_effect=YahooFinanceError("down")
    ):
        with pytest.raises(YahooFinanceError):
            get_or_refresh_us_quote(db_session, "AAPL", ttl_seconds=3600)


def test_us_quote_works_for_no_suffix_index_ticker(db_session):
    """`^BVSP` (IBOV) goes through the exact same no-suffix path as a US
    stock — no dedicated index handling, same decision as the Anchor
    project's own data-collector."""
    quote = {"price": 120000.0, "name": "IBOVESPA", "exchange": None, "currency": "BRL"}
    with patch("app.services.us_stock_service.fetch_quote", return_value=quote) as mock_fetch:
        result = get_or_refresh_us_quote(db_session, "^BVSP", ttl_seconds=3600)

    mock_fetch.assert_called_with("^BVSP", suffix="")
    assert float(result["price"]) == 120000.0


def test_us_technicals_happy_path(db_session):
    technicals = {"sma_50": None, "sma_100": None, "sma_200": None, "cagr_5y": None, "cagr_10y": None}
    with patch("app.services.us_stock_service.fetch_technicals", return_value=technicals):
        result = get_or_refresh_us_technicals(db_session, "AAPL", ttl_seconds=3600)

    assert result["cached"] is False
    assert result["sma_50"] is None


def test_us_dividends_avg_no_data_without_cache_raises(db_session):
    with patch("app.services.us_stock_service.fetch_dividends_avg", return_value=None):
        with pytest.raises(NoDividendDataError):
            get_or_refresh_us_dividends_avg(db_session, "GROWTHCO", ttl_seconds=3600)


def test_us_price_history_rerun_does_not_duplicate_existing_day(db_session):
    points = [{"price_date": date(2026, 1, 2), "close_price": 150.0}]
    with patch("app.services.us_stock_service.fetch_price_history", return_value=points):
        get_or_refresh_us_price_history(db_session, "AAPL", ttl_seconds=0)

    more_points = points + [{"price_date": date(2026, 1, 3), "close_price": 151.0}]
    with patch(
        "app.services.us_stock_service.fetch_price_history", return_value=more_points
    ):
        result = get_or_refresh_us_price_history(db_session, "AAPL", ttl_seconds=0)

    assert len(result["data"]) == 2
    assert float(result["data"][0].close_price) == 150.0


def test_us_dividend_payments_happy_path(db_session):
    payments = [
        {
            "payment_date": date(2026, 1, 2),
            "amount": 0.25,
            "price_at_payment": 150.0,
            "yield_pct": 0.17,
        }
    ]
    with patch(
        "app.services.us_stock_service.fetch_dividend_payments", return_value=payments
    ):
        result = get_or_refresh_us_dividend_payments(db_session, "AAPL", ttl_seconds=3600)

    assert len(result["data"]) == 1
    assert float(result["data"][0].amount) == 0.25
