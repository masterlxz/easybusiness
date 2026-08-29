from datetime import date
from unittest.mock import patch

import pytest
import requests

from app.sources.cripto_coingecko import fetch_market_chart, fetch_nvt_ratio_vs_ma90, resolve_coin_id
from app.sources.cripto_coinmetrics import (
    fetch_active_addresses_trend_mom,
    fetch_exchange_netflow_ratio,
    fetch_mvrv_z_score,
    fetch_puell_multiple,
)
from app.sources.cripto_defillama import fetch_tvl_trend_mom
from app.sources.cripto_feargreed import fetch_latest
from app.sources.cripto_ultrasound import fetch_fees_vs_emission_ratio, fetch_net_issuance_annualized_pct
from app.sources.crypto_common import CryptoDataError


def _fake_response(payload):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    return FakeResponse()


# --- DefiLlama ---------------------------------------------------------


def test_fetch_tvl_trend_mom_computes_percent_change():
    history = [{"date": i, "tvl": 100.0} for i in range(30)] + [{"date": 30, "tvl": 110.0}]
    with patch(
        "app.sources.cripto_defillama.requests.get", return_value=_fake_response(history)
    ):
        result = fetch_tvl_trend_mom()

    assert result == pytest.approx(10.0)


def test_fetch_tvl_trend_mom_wraps_network_error():
    with patch(
        "app.sources.cripto_defillama.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(CryptoDataError):
            fetch_tvl_trend_mom()


# --- ultrasound.money ----------------------------------------------------


def test_fetch_net_issuance_annualized_pct():
    payload = _fake_response({"d30": [{"supply": 100.0}, {"supply": 101.0}]})
    with patch("app.sources.cripto_ultrasound.requests.get", return_value=payload):
        result = fetch_net_issuance_annualized_pct()

    # 1% over 30 days, annualized (x 365/30)
    assert result == pytest.approx(1.0 * (365 / 30))


def test_fetch_fees_vs_emission_ratio():
    supply_payload = _fake_response({"d30": [{"supply": 100.0}, {"supply": 101.0}]})
    burn_payload = _fake_response({"d30": {"sum": {"eth": 0.5}}})
    with patch(
        "app.sources.cripto_ultrasound.requests.get", side_effect=[supply_payload, burn_payload]
    ):
        result = fetch_fees_vs_emission_ratio()

    # net_change=1.0, burn=0.5 -> gross_issuance=1.5 -> ratio=0.5/1.5
    assert result == pytest.approx(0.5 / 1.5)


def test_ultrasound_wraps_network_error():
    with patch(
        "app.sources.cripto_ultrasound.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(CryptoDataError):
            fetch_net_issuance_annualized_pct()


# --- alternative.me --------------------------------------------------------


def test_fetch_fear_greed_latest():
    payload = _fake_response(
        {"data": [{"value": "42", "value_classification": "Fear", "timestamp": "1700000000"}]}
    )
    with patch("app.sources.cripto_feargreed.requests.get", return_value=payload):
        result = fetch_latest()

    assert result["value"] == 42
    assert result["classification"] == "Fear"
    assert isinstance(result["reading_date"], date)


def test_fear_greed_wraps_network_error():
    with patch(
        "app.sources.cripto_feargreed.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(CryptoDataError):
            fetch_latest()


# --- CoinGecko -------------------------------------------------------------


def test_fetch_nvt_ratio_vs_ma90():
    payload = _fake_response(
        {
            "market_caps": [[0, 100.0], [1, 100.0], [2, 200.0]],
            "total_volumes": [[0, 10.0], [1, 10.0], [2, 10.0]],
        }
    )
    with patch("app.sources.cripto_coingecko.requests.get", return_value=payload):
        result = fetch_nvt_ratio_vs_ma90()

    # daily_nvt = [10, 10, 20]; today=20, ma90 of [10,10] = 10 -> ratio 2.0
    assert result == pytest.approx(2.0)


def test_resolve_coin_id_picks_lowest_market_cap_rank():
    payload = _fake_response(
        {
            "coins": [
                {"symbol": "eth", "id": "ethfi-token", "name": "ETHFI", "market_cap_rank": 500},
                {"symbol": "ETH", "id": "ethereum", "name": "Ethereum", "market_cap_rank": 2},
            ]
        }
    )
    with patch("app.sources.cripto_coingecko.requests.get", return_value=payload):
        result = resolve_coin_id("eth")

    assert result == {"coin_id": "ethereum", "name": "Ethereum"}


def test_resolve_coin_id_returns_none_without_exact_match():
    payload = _fake_response({"coins": [{"symbol": "ethfi", "id": "ethfi-token", "name": "ETHFI"}]})
    with patch("app.sources.cripto_coingecko.requests.get", return_value=payload):
        assert resolve_coin_id("eth") is None


def test_fetch_market_chart_keeps_last_point_per_date():
    payload = _fake_response(
        {
            "prices": [
                [1700000000000, 10.0],
                [1700000000001, 10.5],  # same day, later point wins
                [1700086400000, 11.0],  # next day
            ]
        }
    )
    with patch("app.sources.cripto_coingecko.requests.get", return_value=payload):
        result = fetch_market_chart("ethereum")

    assert len(result) == 2
    assert result[0]["price"] == 10.5
    assert result[1]["price"] == 11.0


def test_coingecko_wraps_network_error():
    with patch(
        "app.sources.cripto_coingecko.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(CryptoDataError):
            fetch_market_chart("ethereum")


# --- CoinMetrics -------------------------------------------------------


def _coinmetrics_response(rows):
    return _fake_response({"data": rows})


def test_fetch_mvrv_z_score_computes_z_score():
    # market_caps=[100,200], CapMVRVCur=[1,2] -> realized_caps=[100,100]
    # (constant) -> stddev(market_caps)=50 -> Z = (200-100)/50 = 2.0
    rows = [
        {"time": "t0", "CapMrktCurUSD": "100.0", "CapMVRVCur": "1.0"},
        {"time": "t1", "CapMrktCurUSD": "200.0", "CapMVRVCur": "2.0"},
    ]
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        return_value=_coinmetrics_response(rows),
    ):
        result = fetch_mvrv_z_score()

    assert result == pytest.approx(2.0)


def test_fetch_puell_multiple_computes_ratio():
    rows = [{"time": f"t{i}", "IssTotUSD": "100.0"} for i in range(365)] + [
        {"time": "t365", "IssTotUSD": "200.0"}
    ]
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        return_value=_coinmetrics_response(rows),
    ):
        result = fetch_puell_multiple()

    expected_ma = (364 * 100.0 + 200.0) / 365
    assert result == pytest.approx(200.0 / expected_ma)


def test_fetch_puell_multiple_raises_with_insufficient_history():
    rows = [{"time": f"t{i}", "IssTotUSD": "100.0"} for i in range(10)]
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        return_value=_coinmetrics_response(rows),
    ):
        with pytest.raises(CryptoDataError):
            fetch_puell_multiple()


def test_fetch_active_addresses_trend_mom_computes_percent_change():
    rows = [{"time": f"t{i}", "AdrActCnt": "100.0"} for i in range(30)] + [
        {"time": "t30", "AdrActCnt": "110.0"}
    ]
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        return_value=_coinmetrics_response(rows),
    ):
        result = fetch_active_addresses_trend_mom()

    assert result == pytest.approx(10.0)


def test_fetch_exchange_netflow_ratio_computes_bounded_ratio():
    rows = [
        {"time": f"t{i}", "FlowInExUSD": "10.0", "FlowOutExUSD": "20.0"} for i in range(30)
    ]
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        return_value=_coinmetrics_response(rows),
    ):
        result = fetch_exchange_netflow_ratio()

    # inflow=300, outflow=600, total=900 -> (300-600)/900 = -1/3
    assert result == pytest.approx(-1 / 3)


def test_coinmetrics_wraps_network_error():
    with patch(
        "app.sources.cripto_coinmetrics.requests.get",
        side_effect=requests.ConnectionError("boom"),
    ):
        with pytest.raises(CryptoDataError):
            fetch_mvrv_z_score()
