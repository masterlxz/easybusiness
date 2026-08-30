"""Cache-through orchestration for CVM company fundamentals (ROE, payout,
DCF fields) — all "1 row per cvm_code, overwritten on refresh" (see
app/services/single_row_cache.py), since the source only ever returns the
most recent fiscal year available, never a historical series.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company import (
    CompanyDcfFundamentals,
    CompanyDividendNotice,
    CompanyPayoutAvg,
    CompanyRoe,
)
from app.services.append_only_list_cache import get_or_refresh_list
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.cvm_dfp import CvmDataError, fetch_dcf_fundamentals, fetch_payout, fetch_roe
from app.sources.cvm_ipe import CvmIpeError, fetch_dividend_notices

SOURCE_NAME = "cvm_dfp"
IPE_SOURCE_NAME = "cvm_ipe"


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


def get_or_refresh_dividend_notices(db: Session, cvm_code: int, ttl_seconds: int) -> dict:
    rows, cached, stale = get_or_refresh_list(
        db,
        CompanyDividendNotice,
        CompanyDividendNotice.cvm_code,
        cvm_code,
        # Not a date column despite the parameter name — `Protocolo_Entrega`
        # is CVM's own unique document id, the real natural key alongside
        # `cvm_code` (2 filings can share the same `data_entrega`). Ordering
        # by it happens to roughly track filing order too (it embeds the
        # filing date), which is good enough here — nothing downstream
        # depends on exact chronological order.
        CompanyDividendNotice.protocolo_entrega,
        ttl_seconds,
        fetch_dividend_notices,
        lambda cvm_code, item, now: {
            "cvm_code": cvm_code,
            "protocolo_entrega": item["protocolo_entrega"],
            "data_entrega": item["data_entrega"],
            "link_download": item["link_download"],
            "source": IPE_SOURCE_NAME,
            "fetched_at": now,
        },
        IPE_SOURCE_NAME,
        CvmIpeError,
    )
    return {
        "cvm_code": cvm_code,
        "source": IPE_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
