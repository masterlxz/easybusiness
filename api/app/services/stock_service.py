"""Cache-through orchestration for stock data (quote, technicals, dividend
average, price history, dividend payments).

Two shapes repeat across the 5 resources — see the two orchestrator
functions below (`_get_or_refresh_single_row`, `_get_or_refresh_list`), each
called once per resource with resource-specific fetch/model/upsert glue:

- "single row per ticker" (quote, technicals, dividends-avg): overwritten on
  every refresh via `ON CONFLICT DO UPDATE` — same pattern as
  `macro_series_service.get_or_refresh_series`, just one row instead of a
  time series.
- "append-only list" (price history, dividend payments): historical facts
  that never change once recorded, so refreshing just adds new rows via
  `ON CONFLICT DO NOTHING` (a past trading day/payment is immutable).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.stock import (
    StockDividendPayment,
    StockDividendsAvg,
    StockPriceHistory,
    StockQuote,
    StockTechnicals,
)
from app.services.freshness import is_fresh
from app.sources.acoes_yahoo import (
    YahooFinanceError,
    fetch_dividend_payments,
    fetch_dividends_avg,
    fetch_price_history,
    fetch_quote,
    fetch_technicals,
)

logger = logging.getLogger(__name__)

SOURCE_NAME = "yahoo_finance"


class NoDividendDataError(ValueError):
    """Raised when a ticker has no dividend history and no cache exists —
    a legitimate absence of data, not a source failure."""


def _get_or_refresh_single_row(db: Session, model, ticker: str, ttl_seconds: int, fetch_fn):
    row = db.get(model, ticker)
    cached, stale = True, False

    if not is_fresh(row.fetched_at if row else None, ttl_seconds):
        try:
            fields = fetch_fn(ticker)
            now = datetime.now(timezone.utc)
            values = {"ticker": ticker, "source": SOURCE_NAME, "fetched_at": now, **fields}
            stmt = insert(model).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[model.ticker],
                set_={
                    **{k: getattr(stmt.excluded, k) for k in fields},
                    "source": SOURCE_NAME,
                    "fetched_at": now,
                },
            )
            db.execute(stmt)
            db.commit()
            cached = False
            row = db.get(model, ticker)
        except YahooFinanceError:
            if row is None:
                raise
            logger.warning("Yahoo Finance unavailable for %s, serving stale cache", ticker)
            stale = True

    return row, cached, stale


def get_or_refresh_quote(db: Session, ticker: str, ttl_seconds: int) -> dict:
    row, cached, stale = _get_or_refresh_single_row(
        db, StockQuote, ticker, ttl_seconds, fetch_quote
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
    row, cached, stale = _get_or_refresh_single_row(
        db, StockTechnicals, ticker, ttl_seconds, fetch_technicals
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
    row = db.get(StockDividendsAvg, ticker)
    cached, stale = True, False

    if not is_fresh(row.fetched_at if row else None, ttl_seconds):
        try:
            fields = fetch_dividends_avg(ticker)
            if fields is None:
                # Source reachable, ticker genuinely has no dividend history
                # — not an error, but nothing to (over)write either.
                if row is None:
                    raise NoDividendDataError(ticker)
            else:
                now = datetime.now(timezone.utc)
                stmt = insert(StockDividendsAvg).values(
                    ticker=ticker, source=SOURCE_NAME, fetched_at=now, **fields
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[StockDividendsAvg.ticker],
                    set_={
                        "avg_dividend_5y": stmt.excluded.avg_dividend_5y,
                        "source": SOURCE_NAME,
                        "fetched_at": now,
                    },
                )
                db.execute(stmt)
                db.commit()
                cached = False
                row = db.get(StockDividendsAvg, ticker)
        except YahooFinanceError:
            if row is None:
                raise
            logger.warning("Yahoo Finance unavailable for %s, serving stale cache", ticker)
            stale = True

    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "avg_dividend_5y": row.avg_dividend_5y,
    }


def _get_or_refresh_list(
    db: Session,
    model,
    date_column,
    ticker: str,
    ttl_seconds: int,
    fetch_fn,
    row_from_item,
):
    latest_fetched_at = db.execute(
        select(model.fetched_at).where(model.ticker == ticker).order_by(model.fetched_at.desc())
    ).scalars().first()

    cached, stale = True, False
    if not is_fresh(latest_fetched_at, ttl_seconds):
        try:
            items = fetch_fn(ticker)
            now = datetime.now(timezone.utc)
            rows = [row_from_item(ticker, item, now) for item in items]
            if rows:
                stmt = insert(model).values(rows)
                stmt = stmt.on_conflict_do_nothing(index_elements=[model.ticker, date_column])
                db.execute(stmt)
                db.commit()
            cached = False
        except YahooFinanceError:
            if latest_fetched_at is None:
                raise
            logger.warning("Yahoo Finance unavailable for %s, serving stale cache", ticker)
            stale = True

    rows = db.scalars(
        select(model).where(model.ticker == ticker).order_by(date_column)
    ).all()

    return {
        "ticker": ticker,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }


def get_or_refresh_price_history(db: Session, ticker: str, ttl_seconds: int) -> dict:
    return _get_or_refresh_list(
        db,
        StockPriceHistory,
        StockPriceHistory.price_date,
        ticker,
        ttl_seconds,
        fetch_price_history,
        lambda ticker, item, now: {
            "ticker": ticker,
            "price_date": item["price_date"],
            "close_price": item["close_price"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
    )


def get_or_refresh_dividend_payments(db: Session, ticker: str, ttl_seconds: int) -> dict:
    return _get_or_refresh_list(
        db,
        StockDividendPayment,
        StockDividendPayment.payment_date,
        ticker,
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
    )
