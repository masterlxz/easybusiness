"""CoinMetrics Community API client (ETH cycle-top indicators).

Confirmed live against the real API (2026-08-29): `community-api.coinmetrics.io` needs no key,
no registration, and serves full daily history for Ethereum back to 2015-08-08 (~4048 points) for
every metric used here — `CapMrktCurUSD`/`CapMVRVCur`/`AdrActCnt`/`IssTotUSD`/`FlowInExUSD`/
`FlowOutExUSD` all confirmed unblocked on the free tier (some other metrics, e.g. `CapRealUSD`
itself, come back `403 forbidden` on this tier — not needed here since `CapMVRVCur` already gives
the ratio pre-computed). Rate limit: 1000 requests/10min per IP, far above what a periodic
refresh needs.

Feeds 4 of the 9 ETH score indicators (Fase 3) that had no free source until now — MVRV Z-Score,
Puell Multiple, Exchange Netflow and Active Addresses Trend were manual-only since Sessions 5/6/21
(Glassnode/CryptoQuant/Etherscan Pro/stakingrewards.com, all paid). Staking Yield still has no
free source (beaconcha.in's free API access ended in 2026; CoinMetrics has no staked-ETH metric
on the community tier) and stays manual.
"""
from __future__ import annotations

import statistics

import requests

from app.sources.crypto_common import CryptoDataError

COINMETRICS_BASE_URL = "https://community-api.coinmetrics.io/v4"
REQUEST_TIMEOUT_SECONDS = 15

# 10000 is the community tier's hard cap (confirmed live — anything above
# gets a 400 "Must be at most 10000"), comfortably more than ETH's ~4048
# daily points today (growing by 365/year) — no pagination needed for years.
FULL_HISTORY_PAGE_SIZE = 10000
TREND_LOOKBACK_DAYS = 30
PUELL_MA_WINDOW_DAYS = 365
NETFLOW_WINDOW_DAYS = 30


def _fetch_metrics(metrics: list[str], page_size: int = FULL_HISTORY_PAGE_SIZE) -> list[dict]:
    """Rows for `metrics`, oldest first (confirmed live — same convention as
    `cripto_defillama`/`cripto_ultrasound`). Each row has `time` (ISO string)
    plus one raw string value per metric — CoinMetrics returns numbers as
    strings to preserve precision.
    """
    try:
        response = requests.get(
            f"{COINMETRICS_BASE_URL}/timeseries/asset-metrics",
            params={
                "assets": "eth",
                "metrics": ",".join(metrics),
                "frequency": "1d",
                "page_size": page_size,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["data"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise CryptoDataError(f"CoinMetrics request failed for {metrics}: {exc}") from exc


def fetch_mvrv_z_score() -> float:
    """MVRV Z-Score: `(MarketCap - RealizedCap) / stddev(MarketCap)`, same
    classic definition the Fase 3 thresholds (green <= 0, red >= 7) were
    already chosen against. `CapRealUSD` itself is blocked on the free
    tier, but `CapMVRVCur` (= MarketCap / RealizedCap) isn't — RealizedCap
    is derived from the two free series instead.
    """
    try:
        rows = _fetch_metrics(["CapMrktCurUSD", "CapMVRVCur"])
        market_caps = [float(r["CapMrktCurUSD"]) for r in rows]
        realized_caps = [
            float(r["CapMrktCurUSD"]) / float(r["CapMVRVCur"]) for r in rows
        ]
    except (ValueError, KeyError, ZeroDivisionError) as exc:
        raise CryptoDataError(f"CoinMetrics MVRV Z-Score parsing failed: {exc}") from exc

    stddev = statistics.pstdev(market_caps)
    if stddev == 0:
        raise CryptoDataError("CoinMetrics MVRV Z-Score: zero market cap stddev")

    return (market_caps[-1] - realized_caps[-1]) / stddev


def fetch_puell_multiple() -> float:
    """Puell Multiple: today's gross issuance (USD) over the 365-day moving
    average of daily gross issuance (USD) — same shape as the classic
    Bitcoin mining-revenue indicator, applied to ETH's own issuance
    (Fase 3 thresholds: green <= 0.5, red >= 4.0)."""
    try:
        rows = _fetch_metrics(["IssTotUSD"])
        issuance = [float(r["IssTotUSD"]) for r in rows]
    except (ValueError, KeyError) as exc:
        raise CryptoDataError(f"CoinMetrics Puell Multiple parsing failed: {exc}") from exc

    if len(issuance) < PUELL_MA_WINDOW_DAYS:
        raise CryptoDataError("CoinMetrics Puell Multiple: not enough issuance history")

    window = issuance[-PUELL_MA_WINDOW_DAYS:]
    moving_average = sum(window) / PUELL_MA_WINDOW_DAYS
    if moving_average == 0:
        raise CryptoDataError("CoinMetrics Puell Multiple: zero issuance moving average")

    return issuance[-1] / moving_average


def fetch_active_addresses_trend_mom() -> float:
    """Percent change in ETH active addresses between today and ~30 days
    ago — same formula as `cripto_defillama.fetch_tvl_trend_mom`, applied
    to `AdrActCnt` instead of TVL, for consistency."""
    try:
        rows = _fetch_metrics(["AdrActCnt"], page_size=TREND_LOOKBACK_DAYS + 5)
        latest = float(rows[-1]["AdrActCnt"])
        previous = float(rows[-1 - TREND_LOOKBACK_DAYS]["AdrActCnt"])
    except (ValueError, KeyError, IndexError) as exc:
        raise CryptoDataError(f"CoinMetrics active addresses trend failed: {exc}") from exc

    if previous == 0:
        raise CryptoDataError("CoinMetrics active addresses trend: zero baseline")

    return (latest - previous) / previous * 100


def fetch_exchange_netflow_ratio() -> float:
    """Net exchange flow ratio over the last 30 days: `sum(inflow - outflow)
    / sum(inflow + outflow)`, bounded to [-1, 1] — negative means net
    outflow dominates (accumulation, green per the Fase 3 spec), positive
    means net inflow dominates (selling pressure, red). A ratio instead of
    a single day's raw USD flow smooths out the day-to-day noise these
    "flash" (revisable) CoinMetrics figures already carry.
    """
    try:
        rows = _fetch_metrics(
            ["FlowInExUSD", "FlowOutExUSD"], page_size=NETFLOW_WINDOW_DAYS + 5
        )
        window = rows[-NETFLOW_WINDOW_DAYS:]
        inflow = sum(float(r["FlowInExUSD"]) for r in window)
        outflow = sum(float(r["FlowOutExUSD"]) for r in window)
    except (ValueError, KeyError) as exc:
        raise CryptoDataError(f"CoinMetrics exchange netflow failed: {exc}") from exc

    total = inflow + outflow
    if total == 0:
        raise CryptoDataError("CoinMetrics exchange netflow: zero total flow")

    return (inflow - outflow) / total
