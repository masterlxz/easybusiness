"""bolsai API client (BR stock fundamentals).

Reimplementation of anchor/data-collector/sources/acoes_bolsai.py's behavior
(see project/CONTEXT.md for the full source catalog). Endpoint and response
format confirmed at usebolsai.com/docs by the Anchor project: base URL
https://api.usebolsai.com/api/v1, auth via `X-API-Key` header (free key,
obtained via Google login on their dashboard).

GET /fundamentals/{ticker} — current snapshot with ~27 indicators; this
client keeps only lpa, vpa, roe, shares_outstanding, cvm_code.

Note (known from the Anchor project's own production use): bolsai's `roe`
mixes quarterly and TTM profit depending on the company, without indicating
which — less reliable than a value computed directly from CVM data (see
app/sources/cvm_dfp.py). Exposed here as-is anyway: this API is a data
layer, not a domain layer — it serves what the source actually returns
rather than silently correcting it. `cvm_code` is included in the response
specifically so a caller can chain into `/v1/companies/{cvm_code}/...` for
a more reliable ROE without a separate resolution step.
"""
from __future__ import annotations

import requests

BOLSAI_BASE_URL = "https://api.usebolsai.com/api/v1"
REQUEST_TIMEOUT_SECONDS = 10


class BolsaiError(RuntimeError):
    """Raised when the bolsai request or response parsing fails, or when
    no API key is configured."""


def fetch_fundamentals(ticker: str, api_key: str) -> dict | None:
    """Current LPA, VPA, ROE, share count and CVM code for `ticker`.
    Returns `None` if bolsai doesn't recognize the ticker (404) — not an
    error, a legitimate "not found".
    """
    if not api_key:
        raise BolsaiError("BOLSAI_API_KEY is not configured")

    try:
        response = requests.get(
            f"{BOLSAI_BASE_URL}/fundamentals/{ticker}",
            headers={"X-API-Key": api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return {
            "lpa": payload["lpa"],
            "vpa": payload["vpa"],
            "roe": payload["roe"],
            "shares_outstanding": payload["shares_outstanding"],
            "cvm_code": str(payload["cvm_code"]),
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise BolsaiError(f"bolsai request failed for '{ticker}': {exc}") from exc


def fetch_fii_summary(ticker: str, api_key: str) -> dict | None:
    """Fase 1.11.3 — FII summary (`GET /fiis/{ticker}`, free plan), used
    only as an auxiliary step of `app.sources.cvm_fii.resolve_cnpj`: bolsai
    doesn't return the fund's own CNPJ (only `administrator_cnpj`, whose
    administrator manages dozens of funds), so this alone can't identify
    the fund — combined with `name` (matched exactly against CVM's
    `Nome_Fundo_Classe`) it narrows the match down safely.

    Returns `{"ticker", "name", "administrator_cnpj"}`, or `None` if the
    ticker doesn't exist / isn't a FII (404) — not an error.
    """
    if not api_key:
        raise BolsaiError("BOLSAI_API_KEY is not configured")

    try:
        response = requests.get(
            f"{BOLSAI_BASE_URL}/fiis/{ticker}",
            headers={"X-API-Key": api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return {
            "ticker": payload["ticker"],
            "name": payload["name"],
            "administrator_cnpj": payload["administrator_cnpj"],
        }
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise BolsaiError(f"bolsai FII request failed for '{ticker}': {exc}") from exc
