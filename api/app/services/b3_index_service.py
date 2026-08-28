"""Cache-through orchestration for B3 index history — append-only list per
index code (a past trading day never changes once recorded), same pattern
as stock/crypto price history."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.b3_index import B3IndexHistory
from app.services.append_only_list_cache import get_or_refresh_list
from app.sources.b3_index_catalog import get_index_info
from app.sources.b3_index_stats import B3IndexStatsError, fetch_index_history

SOURCE_NAME = "b3_index_stats"


class UnknownIndexError(ValueError):
    """Raised when `index_code` isn't in the known B3 index catalog."""


def get_or_refresh_index_history(db: Session, index_code: str, ttl_seconds: int) -> dict:
    index_info = get_index_info(index_code)
    if index_info is None:
        raise UnknownIndexError(index_code)

    rows, cached, stale = get_or_refresh_list(
        db,
        B3IndexHistory,
        B3IndexHistory.index_code,
        index_code,
        B3IndexHistory.price_date,
        ttl_seconds,
        lambda _code: fetch_index_history(index_info.b3_code, index_info.start_year),
        lambda code, item, now: {
            "index_code": code,
            "price_date": item["price_date"],
            "close_price": item["close_price"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        },
        SOURCE_NAME,
        B3IndexStatsError,
    )
    return {
        "index_code": index_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
