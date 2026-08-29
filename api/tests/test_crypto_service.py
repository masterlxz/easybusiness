from datetime import date
from unittest.mock import patch

import pytest

from app.services.crypto_service import (
    CoinNotFoundError,
    UnknownIndicatorError,
    get_or_refresh_eth_indicator,
    get_or_refresh_fear_greed,
    get_or_refresh_price_history,
    get_or_refresh_quote,
)
from app.sources.crypto_common import CryptoDataError

# --- eth indicators ---------------------------------------------------


def test_indicator_first_call_fetches_and_caches(db_session):
    with patch(
        "app.sources.cripto_defillama.fetch_tvl_trend_mom", return_value=12.5
    ):
        result = get_or_refresh_eth_indicator(db_session, "tvl-trend", ttl_seconds=3600)

    assert result["cached"] is False
    assert float(result["raw_value"]) == 12.5
    assert result["source"] == "defillama"


def test_indicator_second_call_within_ttl_uses_cache(db_session):
    with patch(
        "app.sources.cripto_defillama.fetch_tvl_trend_mom", return_value=12.5
    ) as mock_fetch:
        get_or_refresh_eth_indicator(db_session, "tvl-trend", ttl_seconds=3600)
        result = get_or_refresh_eth_indicator(db_session, "tvl-trend", ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


def test_indicator_unknown_code_raises(db_session):
    with pytest.raises(UnknownIndicatorError):
        get_or_refresh_eth_indicator(db_session, "unknown-code", ttl_seconds=3600)


def test_indicator_resolves_each_of_the_4_coinmetrics_codes(db_session):
    """Integration check that the 4 new catalog entries (Fase de
    automação do CoinMetrics) are wired end-to-end through
    get_or_refresh_eth_indicator, same as the original 4 codes above."""
    codes_and_patches = [
        ("mvrv-z-score", "app.sources.cripto_coinmetrics.fetch_mvrv_z_score"),
        ("puell-multiple", "app.sources.cripto_coinmetrics.fetch_puell_multiple"),
        ("exchange-netflow", "app.sources.cripto_coinmetrics.fetch_exchange_netflow_ratio"),
        (
            "active-addresses-trend",
            "app.sources.cripto_coinmetrics.fetch_active_addresses_trend_mom",
        ),
    ]
    for code, patch_target in codes_and_patches:
        with patch(patch_target, return_value=1.5):
            result = get_or_refresh_eth_indicator(db_session, code, ttl_seconds=3600)

        assert float(result["raw_value"]) == 1.5
        assert result["source"] == "coinmetrics"


def test_indicator_source_error_with_cache_serves_stale(db_session):
    with patch(
        "app.sources.cripto_defillama.fetch_tvl_trend_mom", return_value=12.5
    ):
        get_or_refresh_eth_indicator(db_session, "tvl-trend", ttl_seconds=0)
    with patch(
        "app.sources.cripto_defillama.fetch_tvl_trend_mom",
        side_effect=CryptoDataError("down"),
    ):
        result = get_or_refresh_eth_indicator(db_session, "tvl-trend", ttl_seconds=0)

    assert result["stale"] is True
    assert float(result["raw_value"]) == 12.5


# --- fear & greed (singleton) ------------------------------------------


def test_fear_greed_first_call_fetches_and_caches(db_session):
    reading = {"value": 42, "classification": "Fear", "reading_date": date(2026, 1, 1)}
    with patch(
        "app.services.crypto_service.fetch_fear_greed", return_value=reading
    ) as mock_fetch:
        result = get_or_refresh_fear_greed(db_session, ttl_seconds=3600)

    assert mock_fetch.called
    assert result["value"] == 42


def test_fear_greed_second_call_within_ttl_uses_cache(db_session):
    reading = {"value": 42, "classification": "Fear", "reading_date": date(2026, 1, 1)}
    with patch(
        "app.services.crypto_service.fetch_fear_greed", return_value=reading
    ) as mock_fetch:
        get_or_refresh_fear_greed(db_session, ttl_seconds=3600)
        result = get_or_refresh_fear_greed(db_session, ttl_seconds=3600)

    assert mock_fetch.call_count == 1
    assert result["cached"] is True


# --- quote / price-history (coin resolution) ----------------------------


def _resolution():
    return {"coin_id": "ethereum", "name": "Ethereum"}


def test_quote_resolves_symbol_then_caches(db_session):
    with patch(
        "app.services.crypto_service.resolve_coin_id", return_value=_resolution()
    ) as mock_resolve:
        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[{"price_date": date(2026, 1, 1), "price": 100.0}],
        ):
            result = get_or_refresh_quote(
                db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=300
            )

    assert mock_resolve.called
    assert result["symbol"] == "ETH"
    assert result["coin_id"] == "ethereum"
    assert float(result["price"]) == 100.0


def test_quote_reuses_cached_resolution_across_calls(db_session):
    with patch(
        "app.services.crypto_service.resolve_coin_id", return_value=_resolution()
    ) as mock_resolve:
        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[{"price_date": date(2026, 1, 1), "price": 100.0}],
        ):
            get_or_refresh_quote(db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=0)
            get_or_refresh_price_history(
                db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=0
            )

    assert mock_resolve.call_count == 1


def test_quote_unknown_symbol_without_cache_raises(db_session):
    with patch("app.services.crypto_service.resolve_coin_id", return_value=None):
        with pytest.raises(CoinNotFoundError):
            get_or_refresh_quote(
                db_session, "notacoin", resolution_ttl_seconds=3600, ttl_seconds=300
            )


def test_price_history_first_call_fetches_and_caches(db_session):
    points = [
        {"price_date": date(2026, 1, 1), "price": 100.0},
        {"price_date": date(2026, 1, 2), "price": 101.0},
    ]
    with patch("app.services.crypto_service.resolve_coin_id", return_value=_resolution()):
        with patch("app.services.crypto_service.fetch_market_chart", return_value=points):
            result = get_or_refresh_price_history(
                db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=3600
            )

    assert result["cached"] is False
    assert len(result["data"]) == 2


def test_price_history_rerun_does_not_duplicate_existing_day(db_session):
    with patch("app.services.crypto_service.resolve_coin_id", return_value=_resolution()):
        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[{"price_date": date(2026, 1, 1), "price": 100.0}],
        ):
            get_or_refresh_price_history(
                db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=0
            )

        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[
                {"price_date": date(2026, 1, 1), "price": 100.0},
                {"price_date": date(2026, 1, 2), "price": 101.0},
            ],
        ):
            result = get_or_refresh_price_history(
                db_session, "eth", resolution_ttl_seconds=3600, ttl_seconds=0
            )

    assert len(result["data"]) == 2
    assert float(result["data"][0].price) == 100.0  # unchanged, not overwritten
