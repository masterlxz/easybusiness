"""Known macro series catalog.

Deliberately small (Fase 1.4 do project/PHASE.md): only CDI and IPCA, the two
series already validated in production by the Anchor project (see
project/CONTEXT.md). Do not add speculative codes (e.g. Selic, exchange
rate) without confirming them against the real API first — see
project/GUIDELINES.md, "Confiabilidade antes de cobertura".
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MacroSeriesInfo:
    slug: str
    bcb_code: int
    display_name: str


MACRO_SERIES_CATALOG: dict[str, MacroSeriesInfo] = {
    "cdi": MacroSeriesInfo("cdi", 4391, "CDI (accumulated monthly)"),
    "ipca": MacroSeriesInfo("ipca", 433, "IPCA (monthly change)"),
}


def get_series_info(series_code: str) -> MacroSeriesInfo | None:
    return MACRO_SERIES_CATALOG.get(series_code)
