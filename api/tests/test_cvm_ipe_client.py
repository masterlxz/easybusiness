from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
import requests

from app.sources.cvm_ipe import CvmIpeError, fetch_dividend_notices
from tests.cvm_fixtures import IPE_FIELDS, build_zip, ipe_row

CURRENT_YEAR = datetime.now(timezone.utc).year


def _fake_response(content: bytes):
    class FakeResponse:
        def __init__(self, content: bytes):
            self._content = content

        def raise_for_status(self):
            pass

        @property
        def content(self):
            return self._content

    return FakeResponse(content)


def _ipe_zip(year: int, rows: list[dict]) -> bytes:
    filename = f"ipe_cia_aberta_{year}.csv"
    return build_zip({filename: rows}, {filename: IPE_FIELDS})


def test_fetch_dividend_notices_filters_category_and_cvm_code():
    rows = [
        ipe_row(cvm_code="001023", categoria="Relatório Proventos", protocolo="111"),
        ipe_row(cvm_code="001023", categoria="Fato Relevante", protocolo="222"),
        ipe_row(cvm_code="099999", categoria="Relatório Proventos", protocolo="333"),
    ]
    current_zip = _ipe_zip(CURRENT_YEAR, rows)
    prior_zip = _ipe_zip(CURRENT_YEAR - 1, [])

    def fake_get(url, **kwargs):
        return _fake_response(current_zip if str(CURRENT_YEAR) in url else prior_zip)

    with patch("app.sources.cvm_ipe.requests.get", side_effect=fake_get):
        result = fetch_dividend_notices(1023)

    assert result == [
        {
            "protocolo_entrega": "111",
            "data_entrega": date(2026, 2, 11),
            "link_download": "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo=1477025",
        }
    ]


def test_fetch_dividend_notices_merges_current_and_previous_year():
    current_rows = [ipe_row(cvm_code="001023", data_entrega="2026-02-11", protocolo="222")]
    prior_rows = [ipe_row(cvm_code="001023", data_entrega="2025-12-20", protocolo="111")]

    def fake_get(url, **kwargs):
        if str(CURRENT_YEAR) in url and str(CURRENT_YEAR - 1) not in url:
            return _fake_response(_ipe_zip(CURRENT_YEAR, current_rows))
        return _fake_response(_ipe_zip(CURRENT_YEAR - 1, prior_rows))

    with patch("app.sources.cvm_ipe.requests.get", side_effect=fake_get):
        result = fetch_dividend_notices(1023)

    assert [n["protocolo_entrega"] for n in result] == ["111", "222"]


def test_fetch_dividend_notices_tolerates_one_missing_year():
    current_rows = [ipe_row(cvm_code="001023", protocolo="111")]

    def fake_get(url, **kwargs):
        if str(CURRENT_YEAR) in url and str(CURRENT_YEAR - 1) not in url:
            return _fake_response(_ipe_zip(CURRENT_YEAR, current_rows))
        raise requests.ConnectionError("boom")

    with patch("app.sources.cvm_ipe.requests.get", side_effect=fake_get):
        result = fetch_dividend_notices(1023)

    assert [n["protocolo_entrega"] for n in result] == ["111"]


def test_fetch_dividend_notices_raises_when_both_years_fail():
    with patch(
        "app.sources.cvm_ipe.requests.get", side_effect=requests.ConnectionError("boom")
    ):
        with pytest.raises(CvmIpeError):
            fetch_dividend_notices(1023)


def test_fetch_dividend_notices_returns_empty_for_company_with_no_filings():
    with patch(
        "app.sources.cvm_ipe.requests.get",
        return_value=_fake_response(_ipe_zip(CURRENT_YEAR, [])),
    ):
        assert fetch_dividend_notices(1023) == []


def test_fetch_dividend_notices_falls_back_to_link_when_protocolo_blank():
    # Confirmed live against the real CVM file: "Relatório Proventos" rows
    # always have a blank Protocolo_Entrega — the link is the real identity.
    row = ipe_row(cvm_code="001023", protocolo="", link="https://cvm.example/doc?numSequencia=999")
    with patch(
        "app.sources.cvm_ipe.requests.get",
        return_value=_fake_response(_ipe_zip(CURRENT_YEAR, [row])),
    ):
        result = fetch_dividend_notices(1023)

    assert result[0]["protocolo_entrega"] == "https://cvm.example/doc?numSequencia=999"
