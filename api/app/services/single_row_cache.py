"""Generic "1 row per identifier, overwritten on refresh" cache-through.

Shared by any resource where the source only ever gives you the latest known
value for an identifier (a stock quote, a company's ROE, a fund's monthly
indicator) — as opposed to an accumulating time series (see
`macro_series_service`/`stock_service`'s list helper for that shape).

Also handles the case where `fetch_fn` can legitimately return `None` (the
identifier exists but has no data of this kind, e.g. a growth stock with no
dividend history) by accepting an optional `not_found_error_type`: raised
only when there's no cached row to fall back on, otherwise the existing
cache keeps being served untouched.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.services.freshness import is_fresh

logger = logging.getLogger(__name__)


def get_or_refresh_single_row(
    db: Session,
    model,
    pk_column,
    pk_value,
    ttl_seconds: int,
    fetch_fn,
    source_name: str,
    error_type: type[Exception],
    not_found_error_type: type[Exception] | None = None,
):
    row = db.get(model, pk_value)
    cached, stale = True, False

    if not is_fresh(row.fetched_at if row else None, ttl_seconds):
        try:
            fields = fetch_fn(pk_value)
            if fields is None:
                if row is None:
                    raise not_found_error_type(pk_value)
                # else: source reachable but genuinely has no data for this
                # identifier right now — keep serving the existing cache.
            else:
                now = datetime.now(timezone.utc)
                values = {pk_column.key: pk_value, "source": source_name, "fetched_at": now, **fields}
                stmt = insert(model).values(**values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[pk_column],
                    set_={
                        **{k: getattr(stmt.excluded, k) for k in fields},
                        "source": source_name,
                        "fetched_at": now,
                    },
                )
                db.execute(stmt)
                db.commit()
                cached = False
                row = db.get(model, pk_value)
        except error_type:
            if row is None:
                raise
            logger.warning("%s unavailable for %s, serving stale cache", source_name, pk_value)
            stale = True

    return row, cached, stale
