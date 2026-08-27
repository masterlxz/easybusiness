"""Cache-through orchestration for macro series.

Serves cached data from Postgres when it's still within the freshness
window (`cache_ttl_seconds`); otherwise fetches fresh data from the source,
upserts it, and serves the updated data. If the source is unavailable and
there's no cached data at all, the error propagates — but if some cache
already exists, it's served with `stale=True` rather than failing the
request (same "degrade gracefully" behavior BCB SGS availability warrants).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.macro_series import MacroSeriesMonthly
from app.sources.bcb_sgs import BcbSgsError, fetch_monthly_series
from app.sources.catalog import get_series_info

logger = logging.getLogger(__name__)

SOURCE_NAME = "bcb_sgs"


class UnknownSeriesError(ValueError):
    """Raised when `series_code` isn't in the known series catalog."""


def _is_fresh(latest_fetched_at: datetime | None, ttl_seconds: int) -> bool:
    if latest_fetched_at is None:
        return False
    if latest_fetched_at.tzinfo is None:
        latest_fetched_at = latest_fetched_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - latest_fetched_at < timedelta(seconds=ttl_seconds)


def _upsert_points(db: Session, series_code: str, points: list[dict]) -> None:
    if not points:
        return

    now = datetime.now(timezone.utc)
    rows = [
        {
            "series_code": series_code,
            "reference_month": point["reference_month"],
            "value_pct": point["value_pct"],
            "source": SOURCE_NAME,
            "fetched_at": now,
        }
        for point in points
    ]

    stmt = insert(MacroSeriesMonthly).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[MacroSeriesMonthly.series_code, MacroSeriesMonthly.reference_month],
        set_={
            "value_pct": stmt.excluded.value_pct,
            "source": stmt.excluded.source,
            "fetched_at": stmt.excluded.fetched_at,
        },
    )
    db.execute(stmt)
    db.commit()


def get_or_refresh_series(db: Session, series_code: str, ttl_seconds: int) -> dict:
    series_info = get_series_info(series_code)
    if series_info is None:
        raise UnknownSeriesError(series_code)

    latest_fetched_at = db.scalar(
        select(func.max(MacroSeriesMonthly.fetched_at)).where(
            MacroSeriesMonthly.series_code == series_code
        )
    )

    cached, stale = True, False
    if not _is_fresh(latest_fetched_at, ttl_seconds):
        try:
            points = fetch_monthly_series(series_info.bcb_code)
            _upsert_points(db, series_code, points)
            cached = False
        except BcbSgsError:
            if latest_fetched_at is None:
                raise
            logger.warning("BCB SGS unavailable for %s, serving stale cache", series_code)
            stale = True

    rows = db.scalars(
        select(MacroSeriesMonthly)
        .where(MacroSeriesMonthly.series_code == series_code)
        .order_by(MacroSeriesMonthly.reference_month)
    ).all()

    return {
        "series_code": series_code,
        "source": SOURCE_NAME,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((row.fetched_at for row in rows), default=None),
        "data": rows,
    }
