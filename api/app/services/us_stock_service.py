"""Cache-through orchestration for US-market data: SEC EDGAR fundamentals
(fundamentals/DCF/payout/REIT) and Yahoo Finance without the ".SA" suffix
(quote/technicals/dividends/price-history/dividend-payments — Fase 1.11.1,
also covers no-suffix indices such as IBOV/^BVSP, same as the Anchor
project's own data-collector already did).

Same "resolve identifier, then fetch" shape as crypto_service.py's
symbol->coin_id resolution: a ticker's CIK is resolved once (long TTL,
essentially permanent) and reused by the SEC EDGAR endpoints below.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.us_stock import (
    ReitFundamentals,
    SecEdgarCikResolution,
    UsStockDcfFundamentals,
    UsStockDividendPayment,
    UsStockDividendsAvg,
    UsStockFundamentals,
    UsStockPayoutAvg,
    UsStockPriceHistory,
    UsStockQuote,
    UsStockTechnicals,
)
from app.services.append_only_list_cache import get_or_refresh_list
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.acoes_yahoo import (
    YahooFinanceError,
    fetch_dividend_payments,
    fetch_dividends_avg,
    fetch_price_history,
    fetch_quote,
    fetch_technicals,
)
from app.sources.sec_edgar import (
    SecEdgarError,
    fetch_dcf_fundamentals,
    fetch_fundamentals,
    fetch_payout,
    fetch_reit_fundamentals,
    resolve_cik,
)

SOURCE_NAME = "sec_edgar"
YAHOO_SOURCE_NAME = "yahoo_finance"
NO_SUFFIX = ""


class TickerNotFoundError(ValueError):
    """Raised when a ticker can't be resolved to a SEC CIK and no cache
    exists — a legitimate absence of data, not a source failure."""


class NoFundamentalsDataError(ValueError):
    """Raised when a resolved CIK has no fundamentals/DCF/payout/REIT data
    of the requested kind and no cache exists (e.g. a bank missing EBIT/
    inventory tags — see app/sources/sec_edgar.py)."""


class NoDividendDataError(ValueError):
    """Raised when a no-suffix ticker has no dividend history and no cache
    exists — a legitimate absence of data, not a source failure. Same role
    as stock_service.NoDividendDataError for ".SA" tickers."""


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


def get_or_refresh_reit_fundamentals(
    db: Session, ticker: str, resolution_ttl_seconds: int, ttl_seconds: int, contact_email: str
) -> dict:
    """Fase 1.11.2 — REIT indicators, time-series (append-only, keyed by
    (ticker, reference_year)) rather than single-row: `fetch_fn` returns 0
    or 1 item per call (only the latest completed fiscal year is ever
    available from SEC EDGAR), and the response is the full accumulated
    history, matching how the Anchor project's Rust side already reads this
    table (`reit_fundamentals::Entity::find().order_by_desc(FetchedAt)`)."""
    ticker_upper = ticker.upper()
    cik = _resolve_cik(db, ticker_upper, resolution_ttl_seconds, contact_email)

    def _fetch(_ticker):
        fields = fetch_reit_fundamentals(cik, contact_email)
        return [] if fields is None else [fields]

    rows, cached, stale = get_or_refresh_list(
        db,
        ReitFundamentals,
        ReitFundamentals.ticker,
        ticker_upper,
        ReitFundamentals.reference_year,
        ttl_seconds,
        _fetch,
        lambda ticker, item, now: {
            "ticker": ticker,
            "reference_year": item["reference_year"],
            "revenue": item["revenue"],
            "real_estate_property_net": item["real_estate_property_net"],
            "real_estate_property_at_cost": item["real_estate_property_at_cost"],
            "stockholders_equity": item["stockholders_equity"],
            "net_income": item["net_income"],
            "eps_diluted": item["eps_diluted"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
        SOURCE_NAME,
        SecEdgarError,
    )
    return {
        "ticker": ticker_upper,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }


# --- Fase 1.11.1 — Yahoo Finance without the ".SA" suffix ------------------
# Same shapes as app.services.stock_service, just with suffix="" and a
# separate table namespace (a no-suffix ticker never collides with a B3
# ticker, but keeping the data apart matches the existing /v1/us-stocks/
# grouping for SEC EDGAR above). No dedicated IBOV handling — `^BVSP` is
# just another no-suffix ticker through these same functions, same decision
# the Anchor project's data-collector already made.


def get_or_refresh_us_quote(db: Session, ticker: str, ttl_seconds: int) -> dict:
    def _fetch(_ticker):
        return fetch_quote(_ticker, suffix=NO_SUFFIX)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockQuote, UsStockQuote.ticker, ticker, ttl_seconds, _fetch, YAHOO_SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": YAHOO_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "price": row.price,
        "name": row.name,
        "exchange": row.exchange,
        "currency": row.currency,
    }


def get_or_refresh_us_technicals(db: Session, ticker: str, ttl_seconds: int) -> dict:
    def _fetch(_ticker):
        return fetch_technicals(_ticker, suffix=NO_SUFFIX)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockTechnicals, UsStockTechnicals.ticker, ticker, ttl_seconds, _fetch,
        YAHOO_SOURCE_NAME, YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": YAHOO_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "sma_50": row.sma_50,
        "sma_100": row.sma_100,
        "sma_200": row.sma_200,
        "cagr_5y": row.cagr_5y,
        "cagr_10y": row.cagr_10y,
    }


def get_or_refresh_us_dividends_avg(db: Session, ticker: str, ttl_seconds: int) -> dict:
    def _fetch(_ticker):
        return fetch_dividends_avg(_ticker, suffix=NO_SUFFIX)

    row, cached, stale = get_or_refresh_single_row(
        db, UsStockDividendsAvg, UsStockDividendsAvg.ticker, ticker, ttl_seconds, _fetch,
        YAHOO_SOURCE_NAME, YahooFinanceError, NoDividendDataError,
    )
    return {
        "ticker": ticker,
        "source": YAHOO_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "avg_dividend_5y": row.avg_dividend_5y,
    }


def get_or_refresh_us_price_history(db: Session, ticker: str, ttl_seconds: int) -> dict:
    def _fetch(_ticker):
        return fetch_price_history(_ticker, suffix=NO_SUFFIX)

    rows, cached, stale = get_or_refresh_list(
        db,
        UsStockPriceHistory,
        UsStockPriceHistory.ticker,
        ticker,
        UsStockPriceHistory.price_date,
        ttl_seconds,
        _fetch,
        lambda ticker, item, now: {
            "ticker": ticker,
            "price_date": item["price_date"],
            "close_price": item["close_price"],
            "source": YAHOO_SOURCE_NAME,
            "fetched_at": now,
        },
        YAHOO_SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": YAHOO_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }


def get_or_refresh_us_dividend_payments(db: Session, ticker: str, ttl_seconds: int) -> dict:
    def _fetch(_ticker):
        return fetch_dividend_payments(_ticker, suffix=NO_SUFFIX)

    rows, cached, stale = get_or_refresh_list(
        db,
        UsStockDividendPayment,
        UsStockDividendPayment.ticker,
        ticker,
        UsStockDividendPayment.payment_date,
        ttl_seconds,
        _fetch,
        lambda ticker, item, now: {
            "ticker": ticker,
            "payment_date": item["payment_date"],
            "amount": item["amount"],
            "price_at_payment": item["price_at_payment"],
            "yield_pct": item["yield_pct"],
            "source": YAHOO_SOURCE_NAME,
            "fetched_at": now,
        },
        YAHOO_SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": YAHOO_SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
