"""CVM open data client, FII (real estate fund) slice.

Reimplementation of anchor/data-collector/sources/cvm_fii.py's behavior (see
project/CONTEXT.md for the full source catalog this project is
centralizing). Same portal as `cvm_dfp.py` (`dados.cvm.gov.br`) but a
completely separate set of files, own schema (`Data_Referencia`/`Versao`
field names, not DFP's `DT_REFER`/`VERSAO`) and a different zip-naming
convention: the zip is named after the **current** year of the data
(`inf_mensal_fii_2026.zip` already holds the months of 2026 published so
far), not the closed fiscal year like DFP.

Two reports used here, schema confirmed against the real files:
- `INF_MENSAL` — net worth, share value, monthly dividend yield, number of
  shareholders (`inf_mensal_fii_complemento_{year}.csv`, keyed by
  `CNPJ_Fundo_Classe`/`Data_Referencia`).
- `INF_TRIMESTRAL` — only the `imovel` file: vacancy and default rate per
  property (`Percentual_Vacancia`/`Percentual_Inadimplencia`), plus
  address/area/% leased/% of fund revenue.

Market price and dividend payments don't come from here — CVM is the
regulator, not the exchange; those come from `acoes_yahoo.py`.

**Fase 1.11.3**: `resolve_cnpj` (ticker -> CNPJ) ported from Anchor —
combines `acoes_bolsai.fetch_fii_summary` (official fund name + the
administrator's CNPJ) with the public `geral` file of the CVM's monthly
report (which has `Nome_Fundo_Classe` but no ticker).
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from app.sources import acoes_bolsai

CVM_FII_BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC"
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "cvm_fii"
REQUEST_TIMEOUT_SECONDS = 60


class CvmFiiDataError(RuntimeError):
    """Raised when a CVM FII zip download or parse fails."""


def normalize_cnpj(cnpj: str) -> str:
    """Strips punctuation, leaving the 14 raw digits — CVM's CSVs use the
    punctuated form (`"00.332.266/0001-31"`), API callers may use either."""
    return re.sub(r"\D", "", cnpj)


def _zip_path(kind: str, year: int) -> Path:
    return CACHE_DIR / f"inf_{kind}_fii_{year}.zip"


def _download_zip(kind: str, year: int) -> Path:
    path = _zip_path(kind, year)
    if path.exists():
        return path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{CVM_FII_BASE_URL}/INF_{kind.upper()}/DADOS/inf_{kind}_fii_{year}.zip"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CvmFiiDataError(f"CVM FII zip download failed ({kind}, {year}): {exc}") from exc
    path.write_bytes(response.content)
    return path


def _resolve_zip(kind: str) -> Path:
    """Unlike DFP, the FII zip is named after the current data year, not a
    closed fiscal year — tries the current year first (already has months/
    quarters published), falls back to last year only if it doesn't exist
    yet (e.g. the first days of January, before CVM opens the new year's
    zip)."""
    current_year = datetime.now(timezone.utc).year
    try:
        return _download_zip(kind, current_year)
    except CvmFiiDataError:
        return _download_zip(kind, current_year - 1)


def _read_csv(zf: zipfile.ZipFile, filename: str) -> list[dict]:
    with zf.open(filename) as raw:
        text = io.TextIOWrapper(raw, encoding="latin1")
        return list(csv.DictReader(text, delimiter=";"))


def _rows_for_fund(rows: list[dict], cnpj_digits: str) -> list[dict]:
    return [r for r in rows if normalize_cnpj(r["CNPJ_Fundo_Classe"]) == cnpj_digits]


def _latest_version_rows(rows: list[dict]) -> list[dict]:
    """Same discipline as `cvm_dfp.py`'s equivalent — an amended filing
    (higher `Versao`) for the same `Data_Referencia` replaces the previous
    one, never sums/duplicates."""
    if not rows:
        return []
    max_version = max(int(row["Versao"]) for row in rows)
    return [row for row in rows if int(row["Versao"]) == max_version]


def _latest_reference_rows(rows: list[dict]) -> list[dict]:
    """Keeps only the rows for the most recent `Data_Referencia` (already
    filtered to that period's latest version) — used both for the monthly
    indicator (1 row per fund) and the quarterly property data (N rows per
    fund, one per property, all from the same quarter)."""
    if not rows:
        return []
    latest_date = max(row["Data_Referencia"] for row in rows)
    return _latest_version_rows([r for r in rows if r["Data_Referencia"] == latest_date])


def _parse_optional_float(value: str) -> float | None:
    return float(value) if value else None


def fetch_monthly_indicators(cnpj: str) -> dict | None:
    """Most recent monthly report available for `cnpj`. Returns
    `{"reference_date": date, "patrimonio_liquido", "valor_patrimonial_cota",
    "numero_cotistas", "dividend_yield_mes", "rentabilidade_efetiva_mes"}`,
    or `None` if the fund has no row in the current year's file.
    """
    cnpj_digits = normalize_cnpj(cnpj)
    zip_path = _resolve_zip("mensal")

    try:
        with zipfile.ZipFile(zip_path) as zf:
            filename = next(n for n in zf.namelist() if n.startswith("inf_mensal_fii_complemento_"))
            rows = _rows_for_fund(_read_csv(zf, filename), cnpj_digits)
    except (zipfile.BadZipFile, StopIteration) as exc:
        raise CvmFiiDataError(f"CVM FII zip parse failed: {exc}") from exc

    latest = _latest_reference_rows(rows)
    if not latest:
        return None

    row = latest[0]
    return {
        "reference_date": date.fromisoformat(row["Data_Referencia"]),
        "patrimonio_liquido": float(row["Patrimonio_Liquido"]),
        "valor_patrimonial_cota": float(row["Valor_Patrimonial_Cotas"]),
        "numero_cotistas": int(row["Total_Numero_Cotistas"]) if row["Total_Numero_Cotistas"] else None,
        "dividend_yield_mes": _parse_optional_float(row["Percentual_Dividend_Yield_Mes"]),
        "rentabilidade_efetiva_mes": _parse_optional_float(row["Percentual_Rentabilidade_Efetiva_Mes"]),
    }


def fetch_property_data(cnpj: str) -> list[dict]:
    """Properties from the most recent quarterly report available for
    `cnpj`, one item per property (a fund can have several). Returns
    `[{"nome_imovel", "reference_date", "endereco", "area_m2",
    "percentual_vacancia", "percentual_inadimplencia",
    "percentual_receitas_fii", "percentual_locado"}, ...]` — empty if the
    fund has no properties reported (not an error). Percentages already
    come as a fraction (0-1) from CVM.
    """
    cnpj_digits = normalize_cnpj(cnpj)
    zip_path = _resolve_zip("trimestral")

    try:
        with zipfile.ZipFile(zip_path) as zf:
            filename = next(n for n in zf.namelist() if n.startswith("inf_trimestral_fii_imovel_"))
            rows = _rows_for_fund(_read_csv(zf, filename), cnpj_digits)
    except (zipfile.BadZipFile, StopIteration) as exc:
        raise CvmFiiDataError(f"CVM FII zip parse failed: {exc}") from exc

    results = []
    for row in _latest_reference_rows(rows):
        results.append(
            {
                "nome_imovel": row["Nome_Imovel"],
                "reference_date": date.fromisoformat(row["Data_Referencia"]),
                "endereco": row["Endereco"] or None,
                "area_m2": _parse_optional_float(row["Area"]),
                "percentual_vacancia": _parse_optional_float(row["Percentual_Vacancia"]),
                "percentual_inadimplencia": _parse_optional_float(row["Percentual_Inadimplencia"]),
                "percentual_receitas_fii": _parse_optional_float(row["Percentual_Receitas_FII"]),
                "percentual_locado": _parse_optional_float(row["Percentual_Locado"]),
            }
        )
    return results


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().upper()


def resolve_cnpj(ticker: str, bolsai_api_key: str) -> dict | None:
    """Resolves the fund's (not the administrator's) CNPJ from `ticker`,
    combining bolsai (official fund name + administrator's CNPJ) with the
    CVM's public `geral` file of the monthly report (which has
    `Nome_Fundo_Classe` but no ticker).

    Match required: `CNPJ_Administrador` matching (narrows the universe — a
    common administrator manages dozens of funds, confirmed live against
    Banco Genial) **and** `Nome_Fundo_Classe` matching exactly (normalized
    only by whitespace/case, no accent stripping — confirmed the bolsai
    name matches the CVM one character-for-character for a real HGLG11).
    Zero or more than one match -> `None`, never guesses (same discipline
    as `cvm_dfp.py`'s `_find_exact`) — same behavior as the Anchor project's
    original `resolve_cnpj`.
    """
    summary = acoes_bolsai.fetch_fii_summary(ticker, bolsai_api_key)
    if summary is None:
        return None

    admin_cnpj_digits = normalize_cnpj(summary["administrator_cnpj"])
    target_name = _normalize_name(summary["name"])

    zip_path = _resolve_zip("mensal")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            filename = next(n for n in zf.namelist() if n.startswith("inf_mensal_fii_geral_"))
            rows = _read_csv(zf, filename)
    except (zipfile.BadZipFile, StopIteration) as exc:
        raise CvmFiiDataError(f"CVM FII zip parse failed: {exc}") from exc

    candidates = {
        normalize_cnpj(row["CNPJ_Fundo_Classe"])
        for row in rows
        if normalize_cnpj(row["CNPJ_Administrador"]) == admin_cnpj_digits
        and _normalize_name(row["Nome_Fundo_Classe"]) == target_name
    }

    if len(candidates) != 1:
        return None

    return {"cnpj": next(iter(candidates)), "fund_name": summary["name"]}
