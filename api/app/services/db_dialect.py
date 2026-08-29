"""Dialect-portable `INSERT ... ON CONFLICT` — the 3 upsert call sites (single-row cache,
append-only list cache, macro series) are written against Postgres's `insert()` construct, but
SQLite exposes the identical `.on_conflict_do_update()`/`.on_conflict_do_nothing()` API (same
kwargs, same `.excluded` mechanics — SQLite >=3.24 supports native `INSERT ... ON CONFLICT`).
This picks the right one at call time so the same upsert code runs against either backend,
needed for the "free/local" SQLite sidecar mode (Fase 1.10) without forking the 3 services.
"""
from __future__ import annotations

from sqlalchemy.engine import Connection


def upsert_insert(bind: Connection):
    from sqlalchemy.dialects import postgresql, sqlite

    return sqlite.insert if bind.dialect.name == "sqlite" else postgresql.insert
