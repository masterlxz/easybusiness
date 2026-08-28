from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
import requests

from app.sources.cvm_fii import (
    CvmFiiDataError,
    fetch_monthly_indicators,
    fetch_property_data,
    normalize_cnpj,
)
from tests.cvm_fixtures import FII_COMPLEMENTO_FIELDS, FII_IMOVEL_FIELDS, build_zip

YEAR = datetime.now(timezone.utc).year
CNPJ_PUNCTUATED = "00.332.266/0001-31"
CNPJ_DIGITS = "00332266000131"


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


def test_normalize_cnpj_strips_punctuation():
    assert normalize_cnpj(CNPJ_PUNCTUATED) == CNPJ_DIGITS
    assert normalize_cnpj(CNPJ_DIGITS) == CNPJ_DIGITS


def _mensal_zip():
    filename = f"inf_mensal_fii_complemento_{YEAR}.csv"
    rows = [
        {
            "CNPJ_Fundo_Classe": CNPJ_PUNCTUATED,
            "Data_Referencia": "2026-01-01",
            "Versao": "1",
            "Total_Numero_Cotistas": "3639",
            "Patrimonio_Liquido": "258202136.67",
            "Valor_Patrimonial_Cotas": "92.2101419138767",
            "Percentual_Rentabilidade_Efetiva_Mes": "0.005242",
            "Percentual_Dividend_Yield_Mes": "0.004342",
        },
        {
            "CNPJ_Fundo_Classe": CNPJ_PUNCTUATED,
            "Data_Referencia": "2026-02-01",
            "Versao": "1",
            "Total_Numero_Cotistas": "3578",
            "Patrimonio_Liquido": "258340696.87",
            "Valor_Patrimonial_Cotas": "92.2596250663804",
            "Percentual_Rentabilidade_Efetiva_Mes": "0.004874",
            "Percentual_Dividend_Yield_Mes": "0.004338",
        },
    ]
    return build_zip({filename: rows}, {filename: FII_COMPLEMENTO_FIELDS})


def test_fetch_monthly_indicators_picks_latest_reference_date(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", return_value=_fake_response(_mensal_zip())
        ):
            result = fetch_monthly_indicators(CNPJ_PUNCTUATED)

    assert result["reference_date"] == date(2026, 2, 1)
    assert result["patrimonio_liquido"] == 258340696.87
    assert result["numero_cotistas"] == 3578


def test_fetch_monthly_indicators_matches_digits_only_cnpj(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", return_value=_fake_response(_mensal_zip())
        ):
            result = fetch_monthly_indicators(CNPJ_DIGITS)

    assert result is not None


def test_fetch_monthly_indicators_unknown_fund_returns_none(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", return_value=_fake_response(_mensal_zip())
        ):
            assert fetch_monthly_indicators("99999999000199") is None


def test_fetch_monthly_indicators_wraps_network_error(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", side_effect=requests.ConnectionError("boom")
        ):
            with pytest.raises(CvmFiiDataError):
                fetch_monthly_indicators(CNPJ_PUNCTUATED)


def _trimestral_zip():
    filename = f"inf_trimestral_fii_imovel_{YEAR}.csv"
    rows = [
        {
            "CNPJ_Fundo_Classe": CNPJ_PUNCTUATED,
            "Data_Referencia": "2026-03-31",
            "Versao": "1",
            "Nome_Imovel": "Via Parque Shopping",
            "Endereco": "Av. Ayrton Senna, 3000",
            "Area": "56484.83",
            "Percentual_Vacancia": "0.103933",
            "Percentual_Inadimplencia": "0.106526",
            "Percentual_Receitas_FII": "0.97281199403743",
            "Percentual_Locado": "",
        },
        {
            "CNPJ_Fundo_Classe": CNPJ_PUNCTUATED,
            "Data_Referencia": "2026-06-30",
            "Versao": "1",
            "Nome_Imovel": "Via Parque Shopping",
            "Endereco": "Av. Ayrton Senna, 3000",
            "Area": "56484.83",
            "Percentual_Vacancia": "0.169062",
            "Percentual_Inadimplencia": "0.014417",
            "Percentual_Receitas_FII": "0.967897",
            "Percentual_Locado": "",
        },
    ]
    return build_zip({filename: rows}, {filename: FII_IMOVEL_FIELDS})


def test_fetch_property_data_picks_latest_quarter(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", return_value=_fake_response(_trimestral_zip())
        ):
            result = fetch_property_data(CNPJ_PUNCTUATED)

    assert len(result) == 1
    assert result[0]["reference_date"] == date(2026, 6, 30)
    assert result[0]["percentual_vacancia"] == 0.169062
    assert result[0]["percentual_locado"] is None


def test_fetch_property_data_empty_for_unknown_fund(tmp_path):
    with patch("app.sources.cvm_fii.CACHE_DIR", tmp_path):
        with patch(
            "app.sources.cvm_fii.requests.get", return_value=_fake_response(_trimestral_zip())
        ):
            assert fetch_property_data("99999999000199") == []
