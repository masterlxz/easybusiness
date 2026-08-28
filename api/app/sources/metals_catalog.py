"""Known precious metals catalog.

Unlike the other sources, metals have no dedicated HTTP client — they're
just Yahoo Finance quotes for a fixed set of COMEX/NYMEX futures symbols,
with no `.SA` suffix (see app/sources/acoes_yahoo.py, called directly with
`suffix=""` by app/services/metal_service.py). ISO 4217 precious-metal
codes (XAU/XAG/XPT/XPD), same convention as anchor/data-collector/sources/metais_yahoo.py.
Price/quantity stays in troy ounces — the real unit of the futures
contract, no conversion applied here.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MetalInfo:
    code: str
    yahoo_symbol: str
    name: str


METALS_CATALOG: dict[str, MetalInfo] = {
    "xau": MetalInfo("xau", "GC=F", "Gold"),
    "xag": MetalInfo("xag", "SI=F", "Silver"),
    "xpt": MetalInfo("xpt", "PL=F", "Platinum"),
    "xpd": MetalInfo("xpd", "PA=F", "Palladium"),
}


def get_metal_info(metal_code: str) -> MetalInfo | None:
    return METALS_CATALOG.get(metal_code)
