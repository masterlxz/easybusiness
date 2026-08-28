"""Cache-through orchestration for SEC EDGAR (US stock fundamentals).

Same "resolve identifier, then fetch" shape as crypto_service.py's
symbol->coin_id resolution: a ticker's CIK is resolved once (long TTL,
essentially permanent) and reused by all 3 capability endpoints below.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.us_stock import (
    SecEdgarCikResolution,
    UsStockDcfFundamentals,
    UsStockFundamentals,
    UsStockPayoutAvg,
)
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.sec_edgar import (
    SecEdgarError,
    fetch_dcf_fundamentals,
    fetch_fundamentals,
    fetch_payout,
    resolve_cik,
)

SOURCE_NAME = "sec_edgar"


class TickerNotFoundError(ValueError):
    """Raised when a ticker can't be resolved to a SEC CIK and no cache
    exists — a legitimate absence of data, not a source failure."""


class NoFundamentalsDataError(ValueError):
    """Raised when a resolved CIK has no fundamentals/DCF/payout data of
    the requested kind and no cache exists (e.g. a bank missing EBIT/
    inventory tags — see app/sources/sec_edgar.py)."""


def _resolve_cik(db: Session, ticker: str, resolution_ttl_seconds: int, contact_email: str) -> int:
    ticker_upper = ticker.upper()

    def _fetch(_ticker):
        cik = resolve_cik(ticker_upper, contact_email)
        return None if cik is None else {"cik": cik}

    row, _cached, _stale = get_or_refresh_single_row(
        db, SecEdgarCikResolution, SecEdgarCikResolution.ticker, ticker_upper,
        resolution_ttl_seconds, _fetch, SOURCE_NAME, SecEdgarError, TickerNotFoundError,
    )
    return row.cik


def get_or_refresh_fundamentals(
    db: Session, ticker: str, resolution_ttl_seconds: int, ttl_seconds: int, contact_email: str
) -> dict:
    ticker_upper = ticker.upper()
    cik = _resolve_cik(db, ticker_upper, resolution_ttl_seconds, contact_email)

    def _fetch(_ticker):
        return fetch_fundamentals(cik, contact_email)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockFundamentals, UsStockFundamentals.ticker, ticker_upper, ttl_seconds, _fetch,
        SOURCE_NAME, SecEdgarError, NoFundamentalsDataError,
    )
    return {
        "ticker": ticker_upper,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "lpa": row.lpa,
        "vpa": row.vpa,
        "roe": row.roe,
        "shares_outstanding": row.shares_outstanding,
    }


def get_or_refresh_dcf_fundamentals(
    db: Session, ticker: str, resolution_ttl_seconds: int, ttl_seconds: int, contact_email: str
) -> dict:
    ticker_upper = ticker.upper()
    cik = _resolve_cik(db, ticker_upper, resolution_ttl_seconds, contact_email)

    def _fetch(_ticker):
        return fetch_dcf_fundamentals(cik, contact_email)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockDcfFundamentals, UsStockDcfFundamentals.ticker, ticker_upper, ttl_seconds,
        _fetch, SOURCE_NAME, SecEdgarError, NoFundamentalsDataError,
    )
    return {
        "ticker": ticker_upper,
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


def get_or_refresh_payout(
    db: Session, ticker: str, resolution_ttl_seconds: int, ttl_seconds: int, contact_email: str
) -> dict:
    ticker_upper = ticker.upper()
    cik = _resolve_cik(db, ticker_upper, resolution_ttl_seconds, contact_email)

    def _fetch(_ticker):
        return fetch_payout(cik, contact_email)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockPayoutAvg, UsStockPayoutAvg.ticker, ticker_upper, ttl_seconds, _fetch,
        SOURCE_NAME, SecEdgarError, NoFundamentalsDataError,
    )
    return {
        "ticker": ticker_upper,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "payout_avg_5y": row.payout_avg_5y,
    }
