"""Cache-through orchestration for stock data (quote, technicals, dividend
average, price history, dividend payments).

Two shapes repeat across the 5 resources:

- "single row per ticker" (quote, technicals, dividends-avg): overwritten on
  every refresh via `ON CONFLICT DO UPDATE` — handled by the shared
  `app.services.single_row_cache.get_or_refresh_single_row`.
- "append-only list" (price history, dividend payments): historical facts
  that never change once recorded, so refreshing just adds new rows via
  `ON CONFLICT DO NOTHING` (a past trading day/payment is immutable) —
  handled by the shared `app.services.append_only_list_cache.get_or_refresh_list`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.stock import (
    StockDividendPayment,
    StockDividendsAvg,
    StockPriceHistory,
    StockQuote,
    StockTechnicals,
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

SOURCE_NAME = "yahoo_finance"


class NoDividendDataError(ValueError):
    """Raised when a ticker has no dividend history and no cache exists —
    a legitimate absence of data, not a source failure."""


def get_or_refresh_quote(db: Session, ticker: str, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, StockQuote, StockQuote.ticker, ticker, ttl_seconds, fetch_quote, SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "price": row.price,
        "name": row.name,
        "exchange": row.exchange,
        "currency": row.currency,
    }


def get_or_refresh_technicals(db: Session, ticker: str, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, StockTechnicals, StockTechnicals.ticker, ticker, ttl_seconds, fetch_technicals,
        SOURCE_NAME, YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "sma_50": row.sma_50,
        "sma_100": row.sma_100,
        "sma_200": row.sma_200,
        "cagr_5y": row.cagr_5y,
        "cagr_10y": row.cagr_10y,
    }


def get_or_refresh_dividends_avg(db: Session, ticker: str, ttl_seconds: int) -> dict:
    row, cached, stale = get_or_refresh_single_row(
        db, StockDividendsAvg, StockDividendsAvg.ticker, ticker, ttl_seconds,
        fetch_dividends_avg, SOURCE_NAME, YahooFinanceError, NoDividendDataError,
    )
    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "avg_dividend_5y": row.avg_dividend_5y,
    }


def get_or_refresh_price_history(db: Session, ticker: str, ttl_seconds: int) -> dict:
    rows, cached, stale = get_or_refresh_list(
        db,
        StockPriceHistory,
        StockPriceHistory.ticker,
        ticker,
        StockPriceHistory.price_date,
        ttl_seconds,
        fetch_price_history,
        lambda ticker, item, now: {
            "ticker": ticker,
            "price_date": item["price_date"],
            "close_price": item["close_price"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
        SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }


def get_or_refresh_dividend_payments(db: Session, ticker: str, ttl_seconds: int) -> dict:
    rows, cached, stale = get_or_refresh_list(
        db,
        StockDividendPayment,
        StockDividendPayment.ticker,
        ticker,
        StockDividendPayment.payment_date,
        ttl_seconds,
        fetch_dividend_payments,
        lambda ticker, item, now: {
            "ticker": ticker,
            "payment_date": item["payment_date"],
            "amount": item["amount"],
            "price_at_payment": item["price_at_payment"],
            "yield_pct": item["yield_pct"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
        SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
