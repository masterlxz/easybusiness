from unittest.mock import patch

import pytest
import requests

from app.sources.acoes_bolsai import BolsaiError, fetch_fii_summary, fetch_fundamentals


def _fake_response(status_code, payload=None):
    class FakeResponse:
        def __init__(self):
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

        def json(self):
            return payload

    return FakeResponse()


def test_fetch_fundamentals_parses_payload():
    payload = {
        "ticker": "PETR4",
        "lpa": 2.5,
        "vpa": 15.0,
        "roe": 20.0,
        "shares_outstanding": 1_000_000.0,
        "cvm_code": 9512,
    }
    with patch(
        "app.sources.acoes_bolsai.requests.get", return_value=_fake_response(200, payload)
    ):
        result = fetch_fundamentals("PETR4", api_key="fake-key")

    assert result == {
        "lpa": 2.5,
        "vpa": 15.0,
        "roe": 20.0,
        "shares_outstanding": 1_000_000.0,
        "cvm_code": "9512",
    }


def test_fetch_fundamentals_returns_none_on_404():
    with patch(
        "app.sources.acoes_bolsai.requests.get", return_value=_fake_response(404)
    ):
        assert fetch_fundamentals("UNKNOWN1", api_key="fake-key") is None


def test_fetch_fundamentals_raises_without_api_key():
    with pytest.raises(BolsaiError):
        fetch_fundamentals("PETR4", api_key="")


def test_fetch_fundamentals_wraps_network_error():
    with patch(
        "app.sources.acoes_bolsai.requests.get", side_effect=requests.ConnectionError("boom")
    ):
        with pytest.raises(BolsaiError):
            fetch_fundamentals("PETR4", api_key="fake-key")


def test_fetch_fii_summary_parses_payload():
    payload = {
        "ticker": "HGLG11",
        "name": "CSHG LOGISTICA FUNDO DE INVESTIMENTO IMOBILIARIO",
        "administrator_cnpj": "27.809.513/0001-30",
    }
    with patch(
        "app.sources.acoes_bolsai.requests.get", return_value=_fake_response(200, payload)
    ):
        result = fetch_fii_summary("HGLG11", api_key="fake-key")

    assert result == payload


def test_fetch_fii_summary_returns_none_on_404():
    with patch("app.sources.acoes_bolsai.requests.get", return_value=_fake_response(404)):
        assert fetch_fii_summary("NOTAFII1", api_key="fake-key") is None


def test_fetch_fii_summary_raises_without_api_key():
    with pytest.raises(BolsaiError):
        fetch_fii_summary("HGLG11", api_key="")
