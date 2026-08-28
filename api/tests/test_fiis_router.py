from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_db
from app.main import app

API_KEY_HEADER = {"X-API-Key": "test-key"}
CNPJ = "00332266000131"


def _override_get_db(db_session):
    def _get_db():
        yield db_session

    return _get_db


def _client_with_auth(db_session, monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    get_settings.cache_clear()
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_monthly_indicators_requires_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get(f"/v1/fiis/{CNPJ}/monthly-indicators")
    _teardown()

    assert response.status_code == 401


def test_monthly_indicators_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    indicators = {
        "reference_date": date(2026, 2, 1),
        "patrimonio_liquido": 258340696.87,
        "valor_patrimonial_cota": 92.26,
        "numero_cotistas": 3578,
        "dividend_yield_mes": 0.004338,
        "rentabilidade_efetiva_mes": 0.004874,
    }
    with patch(
        "app.services.fii_service.fetch_monthly_indicators", return_value=indicators
    ):
        response = client.get(f"/v1/fiis/{CNPJ}/monthly-indicators", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["cnpj"] == CNPJ


def test_monthly_indicators_returns_404_for_unknown_fund(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.fii_service.fetch_monthly_indicators", return_value=None):
        response = client.get(f"/v1/fiis/{CNPJ}/monthly-indicators", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_properties_returns_200_with_possibly_empty_data(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.fii_service.fetch_property_data", return_value=[]):
        response = client.get(f"/v1/fiis/{CNPJ}/properties", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["data"] == []
