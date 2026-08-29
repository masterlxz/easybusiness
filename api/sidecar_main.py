"""Standalone entrypoint for the compiled "free/local" sidecar binary (Fase 1.10).

Separate from the normal `uvicorn app.main:app` dev/Docker path (unchanged) — this is what gets
compiled with PyInstaller and bundled into a consumer app (Anchor first, others later) as a
long-running local process. Reads `DATABASE_URL`/`API_KEYS` from env exactly like the normal
path (`app/config.py`/`app/auth.py` need zero changes for this — a `sqlite:///...` URL never
touches the Postgres driver, there's no unconditional `import psycopg` anywhere), but additionally:

- Runs Alembic migrations to `head` programmatically before serving, against the *same* migration
  history used by the Postgres path (single source of truth for schema) — this correctly evolves
  an existing local db across consumer-app upgrades, unlike `Base.metadata.create_all()`, which
  only creates missing tables and would silently skip new columns added to already-created ones.
- Starts uvicorn by passing the FastAPI app object directly (not the `"app.main:app"` import
  string) — a PyInstaller-frozen binary can't reliably resolve dynamic import strings the way
  `uvicorn.run("module:attr")`'s reload/multi-worker machinery expects.
- Binds `PORT` from env if set, else lets the OS assign a free port, and announces it as the
  first stdout line (`SIDECAR_PORT=<port>`) before serving — the readiness signal Anchor's Rust
  sidecar lifecycle (Fase 14.2, `desktop/src-tauri/src/finance_api/sidecar.rs`) parses instead of
  guessing a fixed port that might collide with something else on the user's machine.

Building the `--onefile` binary needs two extra `--add-data` flags beyond a bare
`pyinstaller --onefile sidecar_main.py` — found live in Anchor's Fase 14.2 (the compiled binary
built without them crashed on startup with `CommandError: Path doesn't exist: .../migrations`,
because `_run_migrations` reads `migrations/`/`alembic.ini` straight off disk via `__file__`,
not through a Python `import` that PyInstaller's static analysis would follow into the bundle):

    pyinstaller --onefile --name <name> \\
        --add-data "$(pwd)/migrations:migrations" --add-data "$(pwd)/alembic.ini:." \\
        sidecar_main.py

(paths passed to `--add-data` must be absolute, or resolved relative to `--specpath`, not to the
current working directory — a bare relative `migrations:migrations` fails to resolve).
"""
from __future__ import annotations

import os
import socket
import sys

import uvicorn
from alembic import command
from alembic.config import Config


def _run_migrations() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = Config(os.path.join(base_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))
    command.upgrade(cfg, "head")


def _resolve_port() -> int:
    env_port = os.environ.get("PORT")
    if env_port:
        return int(env_port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main() -> None:
    _run_migrations()

    from app.main import app

    port = _resolve_port()
    print(f"SIDECAR_PORT={port}", flush=True)
    sys.stdout.flush()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
