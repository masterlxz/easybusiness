"""Known ETH health-indicator catalog.

Deliberately locked to the 4 codes already validated in production by the
Anchor project (see project/CONTEXT.md) — no threshold/classification here
(GREEN/NEUTRAL/RED is application-level domain logic in Anchor, not part of
the data the Finance API serves; consumers apply their own thresholds to the
raw value). Each entry's `fetch` returns a bare float; the service layer
wraps it into the `{"raw_value": ...}` shape `single_row_cache` expects.
"""
from dataclasses import dataclass
from typing import Callable

from app.sources import cripto_coingecko, cripto_defillama, cripto_ultrasound

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
}


def get_indicator_info(indicator_code: str) -> CryptoIndicatorInfo | None:
    return CRYPTO_INDICATOR_CATALOG.get(indicator_code)
