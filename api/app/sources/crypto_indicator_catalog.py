"""Known ETH health-indicator catalog.

Originally locked to the 4 codes already validated in production by the
Anchor project (see project/CONTEXT.md) — no threshold/classification here
(GREEN/NEUTRAL/RED is application-level domain logic in Anchor, not part of
the data the Finance API serves; consumers apply their own thresholds to the
raw value). Each entry's `fetch` returns a bare float; the service layer
wraps it into the `{"raw_value": ...}` shape `single_row_cache` expects.

4 more codes added once a free source was found (CoinMetrics Community API,
confirmed live) for indicators that had been manual-only in Anchor since
Sessions 5/6/21 — see `app/sources/cripto_coinmetrics.py`. A 5th
(`staking_yield` in Anchor) still has no free source and stays manual.
"""
from dataclasses import dataclass
from typing import Callable

from app.sources import cripto_coingecko, cripto_coinmetrics, cripto_defillama, cripto_ultrasound

# `fetch` closures do a module-attribute lookup at call time (`module.fn()`,
# not a bare imported name) so that tests can `patch("app.sources.<module>.fn")`
# and have it actually take effect here — importing the function object
# directly would freeze the reference at catalog-construction time, making
# it unpatchable.


@dataclass(frozen=True)
class CryptoIndicatorInfo:
    code: str
    fetch: Callable[[], float]
    source: str


CRYPTO_INDICATOR_CATALOG: dict[str, CryptoIndicatorInfo] = {
    "tvl-trend": CryptoIndicatorInfo(
        "tvl-trend", lambda: cripto_defillama.fetch_tvl_trend_mom(), "defillama"
    ),
    "net-issuance": CryptoIndicatorInfo(
        "net-issuance",
        lambda: cripto_ultrasound.fetch_net_issuance_annualized_pct(),
        "ultrasound.money",
    ),
    "fees-vs-emission": CryptoIndicatorInfo(
        "fees-vs-emission",
        lambda: cripto_ultrasound.fetch_fees_vs_emission_ratio(),
        "ultrasound.money",
    ),
    "nvt-ratio": CryptoIndicatorInfo(
        "nvt-ratio", lambda: cripto_coingecko.fetch_nvt_ratio_vs_ma90(), "coingecko"
    ),
    "mvrv-z-score": CryptoIndicatorInfo(
        "mvrv-z-score", lambda: cripto_coinmetrics.fetch_mvrv_z_score(), "coinmetrics"
    ),
    "puell-multiple": CryptoIndicatorInfo(
        "puell-multiple", lambda: cripto_coinmetrics.fetch_puell_multiple(), "coinmetrics"
    ),
    "exchange-netflow": CryptoIndicatorInfo(
        "exchange-netflow", lambda: cripto_coinmetrics.fetch_exchange_netflow_ratio(), "coinmetrics"
    ),
    "active-addresses-trend": CryptoIndicatorInfo(
        "active-addresses-trend",
        lambda: cripto_coinmetrics.fetch_active_addresses_trend_mom(),
        "coinmetrics",
    ),
}


def get_indicator_info(indicator_code: str) -> CryptoIndicatorInfo | None:
    return CRYPTO_INDICATOR_CATALOG.get(indicator_code)
