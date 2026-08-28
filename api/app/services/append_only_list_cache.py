"""Generic "append-only list per identifier" cache-through.

Shared by any resource where each item, once recorded, never changes (a
trading day's close, a dividend payment, a crypto price point) — refreshing
just adds new rows via `ON CONFLICT DO NOTHING`, never overwrites. Contrast
with `app.services.single_row_cache`, for resources where the source only
ever gives you the latest known value.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.services.freshness import is_fresh

logger = logging.getLogger(__name__)


def get_or_refresh_list(
    db: Session,
    model,
    id_column,
    id_value,
    date_column,
    ttl_seconds: int,
    fetch_fn,
    row_from_item,
    source_name: str,
    error_type: type[Exception],
):
    latest_fetched_at = db.execute(
        select(model.fetched_at).where(id_column == id_value).order_by(model.fetched_at.desc())
    ).scalars().first()

    cached, stale = True, False
    if not is_fresh(latest_fetched_at, ttl_seconds):
        try:
            items = fetch_fn(id_value)
            now = datetime.now(timezone.utc)
            rows = [row_from_item(id_value, item, now) for item in items]
            if rows:
                stmt = insert(model).values(rows)
                stmt = stmt.on_conflict_do_nothing(index_elements=[id_column, date_column])
                db.execute(stmt)
                db.commit()
            cached = False
        except error_type:
            if latest_fetched_at is None:
                raise
            logger.warning("%s unavailable for %s, serving stale cache", source_name, id_value)
            stale = True

    rows = db.scalars(select(model).where(id_column == id_value).order_by(date_column)).all()

    return rows, cached, stale
