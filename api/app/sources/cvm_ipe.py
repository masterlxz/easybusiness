"""CVM open data client (IPE — Informações Periódicas e Eventuais).

Mirrors `app/sources/cvm_dfp.py`'s zip-download/parse pattern (same host,
same `;`-delimited/`latin1` shape), for a different CVM dataset:
GET https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip

Unlike DFP (one immutable zip per *fiscal* year, cached to disk forever by
`cvm_dfp.py`), IPE's zip is named by *publication* year and keeps gaining
rows all year as companies file new documents — never cached to disk here;
`app.services.append_only_list_cache`'s TTL (one layer up) is what keeps
this from re-downloading on every request.

Schema confirmed live against the real 2026 file (13MB, 33k rows): columns
`CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;
Especie;Assunto;Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;
Link_Download`. The category **"Relatório Proventos"** (481 of 33k rows in
2026) is a standardized CVM form — confirmed by downloading and reading one
real document (Banco do Brasil, `Codigo_CVM=1023`) — with Valor Bruto
(R$/unidade), Data Pagamento, "Último dia de negociação com Direitos" (data
ex/com) and ISIN per share class, unlike the generic "Fato Relevante"/
"Comunicado ao Mercado" categories (free-text `Assunto`, majority not about
dividends at all despite some mentioning the word). Filtering on `Categoria`
alone is precise enough — no keyword heuristic needed.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone

import requests

CVM_ZIP_URL_TEMPLATE = (
    "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip"
)
REQUEST_TIMEOUT_SECONDS = 60

CATEGORIA_RELATORIO_PROVENTOS = "Relatório Proventos"


class CvmIpeError(RuntimeError):
    """Raised when a CVM IPE zip download or parse fails."""


def _download_zip_bytes(year: int) -> bytes:
    try:
        response = requests.get(
            CVM_ZIP_URL_TEMPLATE.format(year=year), timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise CvmIpeError(f"CVM IPE zip download failed for {year}: {exc}") from exc
    return response.content


def _rows_from_zip(content: bytes, cvm_code: int) -> list[dict]:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            filename = zf.namelist()[0]
            with zf.open(filename) as raw:
                text = io.TextIOWrapper(raw, encoding="latin1")
                reader = csv.DictReader(text, delimiter=";")
                return [
                    row
                    for row in reader
                    if row["Categoria"] == CATEGORIA_RELATORIO_PROVENTOS
                    and int(row["Codigo_CVM"]) == cvm_code
                ]
    except (zipfile.BadZipFile, KeyError, ValueError, IndexError) as exc:
        raise CvmIpeError(f"CVM IPE zip parsing failed: {exc}") from exc


def fetch_dividend_notices(cvm_code: int) -> list[dict]:
    """"Relatório Proventos" filings for `cvm_code`, current + previous
    publication year (a document filed in early January can still belong to
    the previous year's zip, or vice-versa right at the boundary). Returns
    `[{"protocolo_entrega": str, "data_entrega": date, "link_download": str}, ...]`,
    oldest first. Never raises for "company has no dividend notices this
    year" — only for a real fetch/parse failure (and only if *both* years
    fail, since the previous year alone is often enough).
    """
    current_year = datetime.now(timezone.utc).year
    rows: list[dict] = []
    errors: list[CvmIpeError] = []

    for year in (current_year, current_year - 1):
        try:
            content = _download_zip_bytes(year)
        except CvmIpeError as exc:
            errors.append(exc)
            continue
        rows.extend(_rows_from_zip(content, cvm_code))

    if not rows and errors:
        raise errors[0]

    notices = [
        {
            # `Protocolo_Entrega` is blank for every "Relatório Proventos" row
            # — confirmed live against the real CVM file, not assumed from
            # the column name (other categories do have it filled in).
            # `Link_Download` always carries its own `numSequencia`, unique
            # per filing (confirmed across a company's several filings), so
            # it's the fallback identity — and the primary one in practice
            # for this category, not an edge case.
            "protocolo_entrega": row["Protocolo_Entrega"] or row["Link_Download"],
            "data_entrega": datetime.strptime(row["Data_Entrega"], "%Y-%m-%d").date(),
            "link_download": row["Link_Download"],
        }
        for row in rows
    ]
    notices.sort(key=lambda n: n["data_entrega"])
    return notices
