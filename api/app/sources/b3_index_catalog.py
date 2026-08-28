"""Known B3 index catalog.

Deliberately locked to the 3 indexes already validated in production by the
Anchor project — IFIX (base year 2010), SMLL/IDIV (base year 2005). Do not
add speculative codes/base years without confirming them against the real
API first — see project/GUIDELINES.md, "Confiabilidade antes de cobertura".
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class B3IndexInfo:
    slug: str
    b3_code: str
    start_year: int


B3_INDEX_CATALOG: dict[str, B3IndexInfo] = {
    "ifix": B3IndexInfo("ifix", "IFIX", 2010),
    "smll": B3IndexInfo("smll", "SMLL", 2005),
    "idiv": B3IndexInfo("idiv", "IDIV", 2005),
}


def get_index_info(index_code: str) -> B3IndexInfo | None:
    return B3_INDEX_CATALOG.get(index_code)
