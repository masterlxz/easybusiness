"""DefiLlama API client (TVL of chains/protocols).

Reimplementation of anchor/data-collector/sources/cripto_defillama.py's
behavior (see project/CONTEXT.md for the full source catalog). Endpoint
confirmed live against the real API by the Anchor project — public, no key,
no registration: GET /v2/historicalChainTvl/{chain} returns a daily series
`[{"date": <unix seconds>, "tvl": <float>}, ...]`, oldest first.

Feeds the `tvl-trend` entry in `app/sources/crypto_indicator_catalog.py`.
"""
from __future__ import annotations

import requests

from app.sources.crypto_common import CryptoDataError

DEFILLAMA_BASE_URL = "https://api.llama.fi"
REQUEST_TIMEOUT_SECONDS = 15

# The series is daily (confirmed against the real API — consecutive dates
# are exactly 86400s apart), so "30 days ago" is just counting back 30
# positions from the end, no date comparison needed.
TVL_TREND_LOOKBACK_DAYS = 30


def fetch_tvl_trend_mom(chain: str = "Ethereum") -> float:
    """Percent change in `chain`'s TVL between today and ~30 days ago."""
    try:
        response = requests.get(
            f"{DEFILLAMA_BASE_URL}/v2/historicalChainTvl/{chain}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        history = response.json()
        latest_tvl = history[-1]["tvl"]
        previous_tvl = history[-1 - TVL_TREND_LOOKBACK_DAYS]["tvl"]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise CryptoDataError(f"DefiLlama TVL trend request failed for {chain}: {exc}") from exc

    return (latest_tvl - previous_tvl) / previous_tvl * 100
