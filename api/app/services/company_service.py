"""Cache-through orchestration for CVM company fundamentals (ROE, payout,
DCF fields) — all "1 row per cvm_code, overwritten on refresh" (see
app/services/single_row_cache.py), since the source only ever returns the
most recent fiscal year available, never a historical series.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company import CompanyDcfFundamentals, CompanyPayoutAvg, CompanyRoe
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.cvm_dfp import CvmDataError, fetch_dcf_fundamentals, fetch_payout, fetch_roe

SOURCE_NAME = "cvm_dfp"


class CompanyNotFoundError(ValueError):
    """Raised when a CVM code has no data of the requested kind and no
    cache exists — a legitimate absence of data, not a source failure."""


def get_or_refresh_roe(db: Session, cvm_code: int, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, CompanyRoe, CompanyRoe.cvm_code, cvm_code, ttl_seconds, fetch_roe, SOURCE_NAME,
        CvmDataError, CompanyNotFoundError,
    )
    return {
        "cvm_code": cvm_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "reference_year": row.reference_year,
        "roe": row.roe,
    }


def get_or_refresh_payout(db: Session, cvm_code: int, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, CompanyPayoutAvg, CompanyPayoutAvg.cvm_code, cvm_code, ttl_seconds, fetch_payout,
        SOURCE_NAME, CvmDataError, CompanyNotFoundError,
    )
    return {
        "cvm_code": cvm_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "payout_avg_5y": row.payout_avg_5y,
    }


def get_or_refresh_dcf_fundamentals(db: Session, cvm_code: int, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, CompanyDcfFundamentals, CompanyDcfFundamentals.cvm_code, cvm_code, ttl_seconds,
        fetch_dcf_fundamentals, SOURCE_NAME, CvmDataError, CompanyNotFoundError,
    )
    return {
        "cvm_code": cvm_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "reference_year": row.reference_year,
        "ebit": row.ebit,
        "tax_rate": row.tax_rate,
        "depreciation_amortization": row.depreciation_amortization,
        "capex": row.capex,
        "nwc_change": row.nwc_change,
        "total_debt": row.total_debt,
        "cash": row.cash,
        "revenue": row.revenue,
        "inventory": row.inventory,
    }
