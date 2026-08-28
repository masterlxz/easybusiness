"""Cache-through orchestration for precious metal quotes/price history.

Reuses app.sources.acoes_yahoo directly (metals are just Yahoo Finance
quotes with no `.SA` suffix, see app/sources/metals_catalog.py) — no
dedicated HTTP client for this domain.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.metal import MetalPriceHistory, MetalQuote
from app.services.append_only_list_cache import get_or_refresh_list
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.acoes_yahoo import YahooFinanceError, fetch_price_history, fetch_quote
from app.sources.metals_catalog import get_metal_info

SOURCE_NAME = "yahoo_finance"


class UnknownMetalError(ValueError):
    """Raised when `metal_code` isn't in the known metals catalog."""


def get_or_refresh_quote(db: Session, metal_code: str, ttl_seconds: int) -> dict:
    metal_info = get_metal_info(metal_code)
    if metal_info is None:
        raise UnknownMetalError(metal_code)

    def _fetch(_code):
        quote = fetch_quote(metal_info.yahoo_symbol, suffix="")
        return {"price": quote["price"], "name": metal_info.name}

    row, cached, stale = get_or_refresh_single_row(
        db, MetalQuote, MetalQuote.metal_code, metal_code, ttl_seconds, _fetch, SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "metal_code": metal_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "name": row.name,
        "price": row.price,
    }


def get_or_refresh_price_history(db: Session, metal_code: str, ttl_seconds: int) -> dict:
    metal_info = get_metal_info(metal_code)
    if metal_info is None:
        raise UnknownMetalError(metal_code)

    rows, cached, stale = get_or_refresh_list(
        db,
        MetalPriceHistory,
        MetalPriceHistory.metal_code,
        metal_code,
        MetalPriceHistory.price_date,
        ttl_seconds,
        lambda _code: fetch_price_history(metal_info.yahoo_symbol, suffix=""),
        lambda code, item, now: {
            "metal_code": code,
            "price_date": item["price_date"],
            "close_price": item["close_price"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
        SOURCE_NAME,
        YahooFinanceError,
    )
    return {
        "metal_code": metal_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
