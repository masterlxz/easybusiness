"""CoinGecko API client (market data: price, market cap, volume).

Reimplementation of anchor/data-collector/sources/cripto_coingecko.py's
behavior (see project/CONTEXT.md for the full source catalog). Endpoint
confirmed live against the real API by the Anchor project — public, no key:
GET /api/v3/coins/{id}/market_chart returns daily market-cap/volume series
(same shape, `[[timestamp_ms, value], ...]`).
"""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.sources.crypto_common import CryptoDataError

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT_SECONDS = 15

NVT_MA_WINDOW_DAYS = 90
PRICE_HISTORY_DAYS = 365


def fetch_nvt_ratio_vs_ma90(coin_id: str = "ethereum") -> float:
    """Today's NVT divided by the trailing-90-day moving average.

    <1.0 = today's NVT below average (network "cheap" relative to volume) —
    good. >1.0 = above average (network "expensive") — a warning sign.

    Note: "volume" here is exchange (trading) volume, not on-chain settled
    volume (the original Willy Woo NVT definition) — a deliberate proxy so
    the 90-day moving average is available from day one, without waiting
    ~90 days of accumulated collection for a true on-chain-volume source.
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": NVT_MA_WINDOW_DAYS, "interval": "daily"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        market_caps = [point[1] for point in data["market_caps"]]
        volumes = [point[1] for point in data["total_volumes"]]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        raise CryptoDataError(f"CoinGecko NVT ratio request failed for {coin_id}: {exc}") from exc

    daily_nvt = [cap / vol for cap, vol in zip(market_caps, volumes)]
    # The most recent point is "today" (still-forming candle) — the average
    # of the previous 90 closed days is the reference moving average.
    nvt_today = daily_nvt[-1]
    nvt_ma90 = sum(daily_nvt[:-1]) / len(daily_nvt[:-1])
    return nvt_today / nvt_ma90


def resolve_coin_id(symbol: str) -> dict | None:
    """Resolves a free-text ticker (e.g. "ETH", "BTC") to a CoinGecko coin id.

    GET /search?query=X returns a `coins` list, each with
    `symbol`/`id`/`name`/`market_cap_rank`. Several unrelated coins can
    share the same symbol, so this only accepts an *exact* (case-insensitive)
    symbol match — never fuzzy. Among exact matches, the lowest
    `market_cap_rank` wins (the canonical coin for well-known tickers).
    Returns `None` if no exact match exists — not an error.
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/search", params={"query": symbol}, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        coins = response.json().get("coins", [])
    except (requests.RequestException, ValueError) as exc:
        raise CryptoDataError(f"CoinGecko coin search failed for '{symbol}': {exc}") from exc

    exact_matches = [c for c in coins if c.get("symbol", "").lower() == symbol.lower()]
    if not exact_matches:
        return None

    best = min(exact_matches, key=lambda c: c.get("market_cap_rank") or float("inf"))
    return {"coin_id": best["id"], "name": best["name"]}


def fetch_market_chart(coin_id: str, days: int = PRICE_HISTORY_DAYS) -> list[dict]:
    """Daily close price series for `coin_id`, oldest first.

    GET /coins/{id}/market_chart?days=365&interval=daily returns `prices`,
    a list of `[epoch_ms, price]` pairs, one per day. The last point also
    serves as "current price" — one HTTP call covers both a quote and price
    history backfill.
    """
    try:
        response = requests.get(
            f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": days, "interval": "daily"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        prices = response.json().get("prices", [])
    except (requests.RequestException, ValueError) as exc:
        raise CryptoDataError(f"CoinGecko market chart request failed for {coin_id}: {exc}") from exc

    # A day can appear twice near the boundary (today's still-forming
    # candle) — keep the last point seen per date, then sort chronologically.
    by_date: dict = {}
    for epoch_ms, price in prices:
        price_date = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).date()
        by_date[price_date] = price

    return [{"price_date": d, "price": p} for d, p in sorted(by_date.items())]
