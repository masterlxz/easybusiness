"""alternative.me API client (Crypto Fear & Greed Index).

Reimplementation of anchor/data-collector/sources/cripto_feargreed.py's
behavior (see project/CONTEXT.md for the full source catalog). Confirmed
live against the real API by the Anchor project — public, no key: GET
/fng/?limit=1 returns `data: [{value, value_classification, timestamp,
time_until_update}]`, always the most recent reading when `limit=1`. Global
market index, not per-coin — no coin parameter, unlike the other 3 crypto
sources.
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.sources.crypto_common import CryptoDataError

FEAR_GREED_URL = "https://api.alternative.me/fng/"
REQUEST_TIMEOUT_SECONDS = 15


def fetch_latest() -> dict:
    """Returns `{"value": int, "classification": str, "reading_date": date}`."""
    try:
        response = requests.get(
            FEAR_GREED_URL, params={"limit": 1}, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        entry = response.json()["data"][0]
        reading_date = datetime.fromtimestamp(int(entry["timestamp"]), tz=timezone.utc).date()
        value = int(entry["value"])
        classification = entry["value_classification"]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise CryptoDataError(f"alternative.me Fear & Greed request failed: {exc}") from exc

    return {"value": value, "classification": classification, "reading_date": reading_date}
