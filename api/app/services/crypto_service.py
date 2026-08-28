"""Cache-through orchestration for crypto data (ETH health indicators,
global Fear & Greed, and generic coin quote/price history).

Three shapes:

- "single row per indicator code" (eth-indicators): overwritten on refresh,
  via the shared `single_row_cache` — same as `crypto_fear_greed` (a
  singleton, PK fixed at 1 — there's only ever one global reading) and
  `crypto_quotes`.
- "symbol -> CoinGecko coin id" resolution (`crypto_coin_resolution`): also
  a single-row cache, but with its own TTL (`resolution_ttl_seconds`,
  independent from whatever resource is being fetched) since a symbol's
  coin id essentially never changes — quote/price-history both resolve
  through this before doing anything else.
- "append-only list per symbol" (price history): historical, immutable once
  recorded — the shared `append_only_list_cache`.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.crypto import (
    CryptoCoinResolution,
    CryptoFearGreed,
    CryptoIndicator,
    CryptoPriceHistory,
    CryptoQuote,
)
from app.services.append_only_list_cache import get_or_refresh_list
from app.services.single_row_cache import get_or_refresh_single_row
from app.sources.cripto_coingecko import fetch_market_chart, resolve_coin_id
from app.sources.cripto_feargreed import fetch_latest as fetch_fear_greed
from app.sources.crypto_common import CryptoDataError
from app.sources.crypto_indicator_catalog import get_indicator_info

COINGECKO_SOURCE = "coingecko"
FEAR_GREED_SOURCE = "alternative.me"
FEAR_GREED_SINGLETON_ID = 1


class UnknownIndicatorError(ValueError):
    """Raised when `indicator_code` isn't in the known indicator catalog."""


class CoinNotFoundError(ValueError):
    """Raised when a symbol can't be resolved to a CoinGecko coin and no
    cache exists — a legitimate absence of data, not a source failure."""


def get_or_refresh_eth_indicator(db: Session, indicator_code: str, ttl_seconds: int) -> dict:
    indicator_info = get_indicator_info(indicator_code)
    if indicator_info is None:
        raise UnknownIndicatorError(indicator_code)

    def _fetch(_code):
        return {"raw_value": indicator_info.fetch()}

    row, cached, stale = get_or_refresh_single_row(
        db, CryptoIndicator, CryptoIndicator.indicator_code, indicator_code, ttl_seconds,
        _fetch, indicator_info.source, CryptoDataError,
    )
    return {
        "indicator_code": indicator_code,
        "source": row.source,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "raw_value": row.raw_value,
    }


def get_or_refresh_fear_greed(db: Session, ttl_seconds: int) -> dict:
    def _fetch(_id):
        return fetch_fear_greed()

    row, cached, stale = get_or_refresh_single_row(
        db, CryptoFearGreed, CryptoFearGreed.id, FEAR_GREED_SINGLETON_ID, ttl_seconds,
        _fetch, FEAR_GREED_SOURCE, CryptoDataError,
    )
    return {
        "source": row.source,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "value": row.value,
        "classification": row.classification,
        "reading_date": row.reading_date,
    }


def _resolve_symbol(db: Session, symbol: str, ttl_seconds: int) -> CryptoCoinResolution:
    symbol_upper = symbol.upper()

    def _fetch(_symbol):
        return resolve_coin_id(symbol_upper)

    row, _cached, _stale = get_or_refresh_single_row(
        db, CryptoCoinResolution, CryptoCoinResolution.symbol, symbol_upper, ttl_seconds,
        _fetch, COINGECKO_SOURCE, CryptoDataError, CoinNotFoundError,
    )
    return row


def get_or_refresh_quote(
    db: Session, symbol: str, resolution_ttl_seconds: int, ttl_seconds: int
) -> dict:
    symbol_upper = symbol.upper()
    resolution = _resolve_symbol(db, symbol_upper, resolution_ttl_seconds)

    def _fetch(_symbol):
        points = fetch_market_chart(resolution.coin_id)
        if not points:
            raise CryptoDataError(f"CoinGecko returned no price history for '{symbol_upper}'")
        latest = points[-1]
        return {"coin_id": resolution.coin_id, "name": resolution.name, "price": latest["price"]}

    row, cached, stale = get_or_refresh_single_row(
        db, CryptoQuote, CryptoQuote.symbol, symbol_upper, ttl_seconds, _fetch,
        COINGECKO_SOURCE, CryptoDataError,
    )
    return {
        "symbol": symbol_upper,
        "coin_id": row.coin_id,
        "name": row.name,
        "source": row.source,
        "cached": cached,
        "stale": stale,
        "fetched_at": row.fetched_at,
        "price": row.price,
    }


def get_or_refresh_price_history(
    db: Session, symbol: str, resolution_ttl_seconds: int, ttl_seconds: int
) -> dict:
    symbol_upper = symbol.upper()
    resolution = _resolve_symbol(db, symbol_upper, resolution_ttl_seconds)

    rows, cached, stale = get_or_refresh_list(
        db,
        CryptoPriceHistory,
        CryptoPriceHistory.symbol,
        symbol_upper,
        CryptoPriceHistory.price_date,
        ttl_seconds,
        lambda _symbol: fetch_market_chart(resolution.coin_id),
        lambda symbol, item, now: {
            "symbol": symbol,
            "price_date": item["price_date"],
            "price": item["price"],
            "source": COINGECKO_SOURCE,
            "fetched_at": now,
        },
        COINGECKO_SOURCE,
        CryptoDataError,
    )
    return {
        "symbol": symbol_upper,
        "coin_id": resolution.coin_id,
        "source": COINGECKO_SOURCE,
        "cached": cached,
        "stale": stale,
        "fetched_at": max((r.fetched_at for r in rows), default=None),
        "data": rows,
    }
