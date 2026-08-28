"""ultrasound.money API client (ETH supply, for net issuance).

Reimplementation of anchor/data-collector/sources/cripto_ultrasound.py's
behavior (see project/CONTEXT.md for the full source catalog). Confirmed
live against the real API by the Anchor project — public, no key. Backend
is open source (github.com/ultrasoundmoney/eth-analysis-rs), exposes real
REST routes under ultrasound.money/api/v2/fees/*.

GET /api/v2/fees/supply-over-time returns several ETH total-supply windows
(m5, h1, d1, d7, d30, since_merge, since_burn), each already cut to the
right period server-side. `d30` (last 30 days) feeds the `net-issuance`
catalog entry: % change in supply over that window, annualized.

GET /api/v2/fees/burn-sums has the same window shape, but sums of ETH/USD
burned (post-EIP-1559 fees) in each. Feeds `fees-vs-emission`: the API
doesn't return gross issuance directly, only net supply (issuance - burn)
and burn separately — gross issuance is reconstructed as
`net_supply_change + burn`.
"""
from __future__ import annotations

import requests

from app.sources.crypto_common import CryptoDataError

ULTRASOUND_BASE_URL = "https://ultrasound.money/api/v2/fees"
REQUEST_TIMEOUT_SECONDS = 15

DAYS_IN_WINDOW = 30
DAYS_IN_YEAR = 365


def fetch_net_issuance_annualized_pct() -> float:
    """Annualized % change in ETH supply over the last 30 days.

    Positive = supply growing (issuance > burn); negative = "ultra sound"
    (burn > issuance).
    """
    try:
        response = requests.get(
            f"{ULTRASOUND_BASE_URL}/supply-over-time", timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        window = response.json()["d30"]
        supply_start = window[0]["supply"]
        supply_end = window[-1]["supply"]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise CryptoDataError(f"ultrasound.money supply request failed: {exc}") from exc

    pct_over_window = (supply_end - supply_start) / supply_start * 100
    return pct_over_window * (DAYS_IN_YEAR / DAYS_IN_WINDOW)


def fetch_fees_vs_emission_ratio() -> float:
    """Burn (fees) ÷ gross ETH issuance over the 30-day window.

    <0.1 = burn covers little of new issuance (inflation-dependent network).
    >0.5 = burn covers most of issuance (near-deflationary).
    """
    try:
        supply_response = requests.get(
            f"{ULTRASOUND_BASE_URL}/supply-over-time", timeout=REQUEST_TIMEOUT_SECONDS
        )
        supply_response.raise_for_status()
        window = supply_response.json()["d30"]
        net_change_eth = window[-1]["supply"] - window[0]["supply"]

        burn_response = requests.get(
            f"{ULTRASOUND_BASE_URL}/burn-sums", timeout=REQUEST_TIMEOUT_SECONDS
        )
        burn_response.raise_for_status()
        burn_eth = burn_response.json()["d30"]["sum"]["eth"]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise CryptoDataError(f"ultrasound.money fees/emission request failed: {exc}") from exc

    gross_issuance_eth = net_change_eth + burn_eth
    return burn_eth / gross_issuance_eth
