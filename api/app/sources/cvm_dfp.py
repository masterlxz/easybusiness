"""CVM open data client (DFP — Demonstrações Financeiras Padronizadas).

Reimplementation of anchor/data-collector/sources/cvm_dfp.py's behavior (see
project/CONTEXT.md for the full source catalog this project is
centralizing). Not a per-company REST API like the other sources — the CVM
publishes **one zip per fiscal year** with the financial statements of all
~870 public companies together:
GET https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip

Schema confirmed against the real files (not just against Anchor's
docstrings): several `;`-delimited CSVs, `latin1` encoding, one per
statement — `DRE_con` (income statement), `BPA_con`/`BPP_con` (balance
sheet, assets/liabilities), `DFC_MI_con` (cash flow, indirect method),
`DMPL_con` (equity changes). Each row is one account (`CD_CONTA`, a fixed
code shared across companies for ~850 of the ~870) of one company
(`CD_CVM`, comes zero-padded as a string, e.g. `"004170"` — must be cast to
`int` before comparing) for a period (`ORDEM_EXERC` = 'ÚLTIMO'/'PENÚLTIMO'
— the annual file already carries the last two fiscal years).

Not every account is as standardized as it looks: EBIT, debt, cash and the
ΔNWC pieces use the same `CD_CONTA` for ~850 of the ~870 companies — safe to
read directly. D&A and Capex don't (the code varies company to company), so
those are extracted by keyword search over the account text (`DS_CONTA`)
instead of a fixed code, returning `None` rather than risking a wrong
number when no single confident group of rows is found.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

CVM_ZIP_URL_TEMPLATE = (
    "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
)
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "cvm_dfp"
REQUEST_TIMEOUT_SECONDS = 60

LATEST = "ÚLTIMO"
PRIOR = "PENÚLTIMO"

# ESCALA_MOEDA -> multiplier to convert VL_CONTA to BRL.
_CURRENCY_SCALE = {"MIL": 1_000, "MILHAO": 1_000_000, "UNIDADE": 1}

PAYOUT_YEARS_AVERAGED = 5
# Sanity ceiling for the effective tax rate. A pretax income close to zero
# makes the ratio blow up (a real-world case computed 263% this way) — this
# is a safety net for positive-but-near-zero cases; the `pretax_income <= 0`
# guard below already covers the more common zero/negative case.
_MAX_PLAUSIBLE_TAX_RATE = 100.0
_PATRIMONIO_LIQUIDO_CONSOLIDADO_COLUMN = "Patrimônio Líquido Consolidado"
_EMPTY_COLUMN = ""


class CvmDataError(RuntimeError):
    """Raised when a CVM DFP zip download or parse fails."""


def _zip_path(year: int) -> Path:
    return CACHE_DIR / f"dfp_cia_aberta_{year}.zip"


def _download_zip(year: int) -> Path:
    path = _zip_path(year)
    if path.exists():
        return path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(
            CVM_ZIP_URL_TEMPLATE.format(year=year), timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CvmDataError(f"CVM DFP zip download failed for {year}: {exc}") from exc
    path.write_bytes(response.content)
    return path


def _resolve_zip_path() -> Path:
    """CVM names the zip after the fiscal year it covers, not the
    publication year — in mid-2026 the latest zip is `2025` (fiscal year
    ended 2025-12-31, filed in early 2026), not a `2026` zip (which won't
    exist until ~March 2027). Tries last year first, falls back to the year
    before that on a 404 (e.g. early January, before CVM publishes the
    latest zip)."""
    candidate_year = datetime.now(timezone.utc).year - 1
    try:
        return _download_zip(candidate_year)
    except CvmDataError:
        return _download_zip(candidate_year - 1)


def _resolve_recent_years(count: int) -> list[int]:
    """Last `count` fiscal years with a published CVM zip, most recent
    first."""
    zip_path = _resolve_zip_path()
    latest_year = int(zip_path.stem.rsplit("_", 1)[-1])
    return list(range(latest_year, latest_year - count, -1))


def _read_csv_from_zip(zf: zipfile.ZipFile, filename: str) -> list[dict]:
    with zf.open(filename) as raw:
        text = io.TextIOWrapper(raw, encoding="latin1")
        return list(csv.DictReader(text, delimiter=";"))


def _rows_for_company(rows: list[dict], cvm_code: int) -> list[dict]:
    return [r for r in rows if int(r["CD_CVM"]) == cvm_code]


def _latest_version_rows(rows: list[dict]) -> list[dict]:
    """A company can have more than one `VERSAO` (amended filing) for the
    same fiscal year — keeps only the most recent version's rows, or a
    retification's duplicate accounts would inflate any sum."""
    if not rows:
        return []
    max_version = max(int(row["VERSAO"]) for row in rows)
    return [row for row in rows if int(row["VERSAO"]) == max_version]


def _to_millions_brl(row: dict) -> float:
    scale = _CURRENCY_SCALE[row["ESCALA_MOEDA"]]
    return float(row["VL_CONTA"]) * scale / 1_000_000


def _find_exact(rows: list[dict], cd_conta: str, orden_exerc: str = LATEST) -> float:
    """Reads a stable-code account (EBIT, debt, cash, ...). Raises
    `LookupError` if the account doesn't exist for this company/period."""
    candidates = _latest_version_rows(
        [r for r in rows if r["CD_CONTA"] == cd_conta and r["ORDEM_EXERC"] == orden_exerc]
    )
    if not candidates:
        raise LookupError(f"account {cd_conta!r} ({orden_exerc}) not found")
    return _to_millions_brl(candidates[0])


def _find_by_keyword(
    rows: list[dict], code_prefix: str, keywords: list[str], orden_exerc: str = LATEST
) -> float | None:
    """Finds rows by code prefix + keyword in the account text (D&A, Capex
    — codes aren't standardized across companies). Discards "parent" rows
    (whose code is a prefix of another matched row's code) to avoid summing
    a subtotal together with its detail. Returns `None` if nothing matches
    — never guesses."""
    matched = _latest_version_rows(
        [
            r
            for r in rows
            if r["CD_CONTA"].startswith(code_prefix)
            and r["ORDEM_EXERC"] == orden_exerc
            and any(keyword in r["DS_CONTA"].lower() for keyword in keywords)
        ]
    )
    if not matched:
        return None

    codes = {r["CD_CONTA"] for r in matched}
    leaves = [
        r
        for r in matched
        if not any(other != r["CD_CONTA"] and other.startswith(r["CD_CONTA"] + ".") for other in codes)
    ]
    return abs(sum(_to_millions_brl(r) for r in leaves))


def _effective_tax_rate(dre_rows: list[dict]) -> float | None:
    """Effective tax rate = income tax & social contribution ÷ pretax
    income, both from the income statement (`3.08`/`3.07`). Returned as a
    percentage. `None` when pretax income is zero/negative or the ratio
    falls outside a plausible range — mathematically unstable there, not a
    real rate."""
    pretax_income = _find_exact(dre_rows, "3.07")
    tax_expense = _find_exact(dre_rows, "3.08")

    if pretax_income <= 0:
        return None

    tax_rate = -tax_expense / pretax_income * 100
    if not (0.0 <= tax_rate <= _MAX_PLAUSIBLE_TAX_RATE):
        return None
    return tax_rate


def _nwc_change(bpa_rows: list[dict], bpp_rows: list[dict]) -> float:
    """ΔNWC = (receivables + inventory − payables) this fiscal year minus
    the same calculation last year — uses only the 3 stable balance-sheet
    codes."""

    def nwc_at(orden_exerc: str) -> float:
        receivables = _find_exact(bpa_rows, "1.01.03", orden_exerc)
        inventory = _find_exact(bpa_rows, "1.01.04", orden_exerc)
        payables = _find_exact(bpp_rows, "2.01.02", orden_exerc)
        return receivables + inventory - payables

    return nwc_at(LATEST) - nwc_at(PRIOR)


def _extract_distributions(dmpl_rows: list[dict]) -> float | None:
    """Dividends + interest on equity (JCP), found by keyword in the
    "Patrimônio Líquido Consolidado" column of the equity-changes statement
    (the total — the file repeats each row once per equity component, so
    filtering by column avoids multiplying the sum). Falls back to the
    unlabeled column (`COLUNA_DF == ""`) only when the main column sums to
    exactly `0.0` (not `None` — `None` means "no rows matched", `0.0` means
    "matched but summed to zero", only the latter is suspicious)."""
    consolidado_rows = [
        r for r in dmpl_rows if r.get("COLUNA_DF") == _PATRIMONIO_LIQUIDO_CONSOLIDADO_COLUMN
    ]
    distributions = _find_by_keyword(consolidado_rows, "5.", ["dividendo", "juros sobre capital"])
    if distributions != 0.0:
        return distributions

    empty_rows = [r for r in dmpl_rows if r.get("COLUNA_DF") == _EMPTY_COLUMN]
    return _find_by_keyword(empty_rows, "5.", ["dividendo", "juros sobre capital"])


def fetch_roe(cvm_code: int) -> dict | None:
    """Net income ÷ shareholders' equity (both consolidated, most recent
    fiscal year), computed straight from CVM instead of trusting a paid
    fundamentals API's `roe` field. Returns `{"reference_year", "roe"}` (%)
    or `None` if either account can't be found for this company (e.g.
    unusual taxonomy) — never a wrong number.
    """
    zip_path = _resolve_zip_path()
    year = int(zip_path.stem.rsplit("_", 1)[-1])

    try:
        with zipfile.ZipFile(zip_path) as zf:
            dre_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_DRE_con_{year}.csv"), cvm_code
            )
            bpp_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_BPP_con_{year}.csv"), cvm_code
            )
    except (zipfile.BadZipFile, KeyError) as exc:
        raise CvmDataError(f"CVM DFP zip parse failed: {exc}") from exc

    if not dre_rows or not bpp_rows:
        return None

    net_income = _find_by_keyword(dre_rows, "3.", ["consolidado do período"])
    equity = _find_by_keyword(bpp_rows, "2.", ["patrimônio líquido consolidado"])
    if net_income is None or equity is None or equity <= 0:
        return None

    return {"reference_year": year, "roe": net_income / equity * 100}


def fetch_payout(cvm_code: int) -> dict | None:
    """Average payout ratio (sum of dividends+JCP ÷ sum of net income,
    summed year by year before dividing once at the end — not a simple
    average of yearly payouts, since one distorted year would otherwise
    pull the result with the same weight as the others) over the last
    `PAYOUT_YEARS_AVERAGED` fiscal years. Returns `{"payout_avg_5y"}` (%) or
    `None` if no year has usable data.
    """
    totals = {"net_income": 0.0, "distributions": 0.0, "years_found": 0}

    for year in _resolve_recent_years(PAYOUT_YEARS_AVERAGED):
        zip_path = _download_zip(year)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                dre_rows = _rows_for_company(
                    _read_csv_from_zip(zf, f"dfp_cia_aberta_DRE_con_{year}.csv"), cvm_code
                )
                dmpl_rows = _rows_for_company(
                    _read_csv_from_zip(zf, f"dfp_cia_aberta_DMPL_con_{year}.csv"), cvm_code
                )
        except (zipfile.BadZipFile, KeyError) as exc:
            raise CvmDataError(f"CVM DFP zip parse failed for {year}: {exc}") from exc

        if not dre_rows or not dmpl_rows:
            continue

        net_income = _find_by_keyword(dre_rows, "3.", ["consolidado do período"])
        distributions = _extract_distributions(dmpl_rows)
        if net_income is None or net_income <= 0 or distributions is None:
            continue

        totals["net_income"] += net_income
        totals["distributions"] += distributions
        totals["years_found"] += 1

    if totals["years_found"] == 0:
        return None
    return {"payout_avg_5y": totals["distributions"] / totals["net_income"] * 100}


def fetch_dcf_fundamentals(cvm_code: int) -> dict | None:
    """The 9 accounting fields the DCF/FCFF model needs (EBIT, effective
    tax rate, D&A, Capex, ΔNWC, total debt, cash, revenue, inventory) for
    the most recent fiscal year. `depreciation_amortization`/`capex`/
    `tax_rate` can be `None` individually (no confident match) without
    discarding the rest. Returns `None` if the company can't be found at
    all in the zip, or the DRE.
    """
    zip_path = _resolve_zip_path()
    year = int(zip_path.stem.rsplit("_", 1)[-1])

    try:
        with zipfile.ZipFile(zip_path) as zf:
            dre_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_DRE_con_{year}.csv"), cvm_code
            )
            bpa_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_BPA_con_{year}.csv"), cvm_code
            )
            bpp_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_BPP_con_{year}.csv"), cvm_code
            )
            dfc_rows = _rows_for_company(
                _read_csv_from_zip(zf, f"dfp_cia_aberta_DFC_MI_con_{year}.csv"), cvm_code
            )
    except (zipfile.BadZipFile, KeyError) as exc:
        raise CvmDataError(f"CVM DFP zip parse failed: {exc}") from exc

    if not dre_rows:
        return None

    try:
        return {
            "reference_year": year,
            "ebit": _find_exact(dre_rows, "3.05"),
            "tax_rate": _effective_tax_rate(dre_rows),
            "depreciation_amortization": _find_by_keyword(
                dfc_rows, "6.01.01", ["depreciaç", "amortiza", "exaust"]
            ),
            "capex": _find_by_keyword(dfc_rows, "6.02", ["imobilizado", "intangív", "intangiv"]),
            "nwc_change": _nwc_change(bpa_rows, bpp_rows),
            "total_debt": _find_exact(bpp_rows, "2.01.04") + _find_exact(bpp_rows, "2.02.01"),
            "cash": _find_exact(bpa_rows, "1.01.01") + _find_exact(bpa_rows, "1.01.02"),
            "revenue": _find_exact(dre_rows, "3.01"),
            "inventory": _find_exact(bpa_rows, "1.01.04"),
        }
    except LookupError:
        return None
