"""Shared freshness check for cache-through services."""
from datetime import datetime, timedelta, timezone


def is_fresh(latest_fetched_at: datetime | None, ttl_seconds: int) -> bool:
    if latest_fetched_at is None:
        return False
    if latest_fetched_at.tzinfo is None:
        latest_fetched_at = latest_fetched_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - latest_fetched_at < timedelta(seconds=ttl_seconds)
