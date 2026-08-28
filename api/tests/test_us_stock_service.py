from unittest.mock import patch

import pytest

from app.services.us_stock_service import (
    NoFundamentalsDataError,
    TickerNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_fundamentals,
    get_or_refresh_payout,
)
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
