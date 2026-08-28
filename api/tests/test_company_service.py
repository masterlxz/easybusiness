from unittest.mock import patch

import pytest

from app.services.company_service import (
    CompanyNotFoundError,
    get_or_refresh_dcf_fundamentals,
    get_or_refresh_payout,
    get_or_refresh_roe,
)
from app.sources.cvm_dfp import CvmDataError


def test_roe_first_call_fetches_and_caches(db_session):
    with patch(
        "app.services.company_service.fetch_roe",
        return_value={"reference_year": 2025, "roe": 20.0},
    ) as mock_fetch:
        result = get_or_refresh_roe(db_session, 4170, ttl_seconds=3600)

    assert mock_fetch.called
    assert result["cached"] is False
    assert float(result["roe"]) == 20.0


def test_roe_second_call_within_ttl_uses_cache(db_session):
    with patch(
        "app.services.company_service.fetch_roe",
        return_value={"reference_year": 2025, "roe": 20.0},
    ) as mock_fetch:
        get_or_refresh_roe(db_session, 4170, ttl_seconds=3600)
        result = get_or_refresh_roe(db_session, 4170, ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_roe_unknown_company_without_cache_raises_404_error(db_session):
    with patch("app.services.company_service.fetch_roe", return_value=None):
        with pytest.raises(CompanyNotFoundError):
            get_or_refresh_roe(db_session, 999999, ttl_seconds=3600)


def test_roe_source_error_without_cache_propagates(db_session):
    with patch(
        "app.services.company_service.fetch_roe", side_effect=CvmDataError("down")
    ):
        with pytest.raises(CvmDataError):
            get_or_refresh_roe(db_session, 4170, ttl_seconds=3600)


def test_roe_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.services.company_service.fetch_roe",
        return_value={"reference_year": 2025, "roe": 20.0},
    ):
        get_or_refresh_roe(db_session, 4170, ttl_seconds=0)
    with patch(
        "app.services.company_service.fetch_roe", side_effect=CvmDataError("down")
    ):
        result = get_or_refresh_roe(db_session, 4170, ttl_seconds=0)

    assert result["stale"] is True
    assert float(result["roe"]) == 20.0


def test_payout_happy_path(db_session):
    with patch(
        "app.services.company_service.fetch_payout", return_value={"payout_avg_5y": 35.5}
    ):
        result = get_or_refresh_payout(db_session, 4170, ttl_seconds=3600)

    assert float(result["payout_avg_5y"]) == 35.5


def test_dcf_fundamentals_happy_path(db_session):
    fields = {
        "reference_year": 2025,
        "ebit": 50.0,
        "tax_rate": 25.0,
        "depreciation_amortization": 3.0,
        "capex": 4.0,
        "nwc_change": 1.0,
        "total_debt": 40.0,
        "cash": 25.0,
        "revenue": 100.0,
        "inventory": 8.0,
    }
    with patch(
        "app.services.company_service.fetch_dcf_fundamentals", return_value=fields
    ):
        result = get_or_refresh_dcf_fundamentals(db_session, 4170, ttl_seconds=3600)

    assert float(result["ebit"]) == 50.0
    assert result["tax_rate"] is not None and float(result["tax_rate"]) == 25.0


def test_dcf_fundamentals_unknown_company_raises_404_error(db_session):
    with patch(
        "app.services.company_service.fetch_dcf_fundamentals", return_value=None
    ):
        with pytest.raises(CompanyNotFoundError):
            get_or_refresh_dcf_fundamentals(db_session, 999999, ttl_seconds=3600)
