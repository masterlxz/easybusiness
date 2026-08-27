"""Static API key auth (MVP — see project/ARCHITECTURE.md for the decision:
no per-consumer key table/admin yet, just a comma-separated allowlist read
from the `API_KEYS` environment variable).
"""
from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    if not x_api_key or x_api_key not in settings.api_keys_set:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return x_api_key
