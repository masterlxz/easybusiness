from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_db
from app.main import app

API_KEY_HEADER = {"X-API-Key": "test-key"}


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


def test_roe_requires_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/companies/4170/roe")
    _teardown()

    assert response.status_code == 401


def test_roe_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch(
        "app.services.company_service.fetch_roe",
        return_value={"reference_year": 2025, "roe": 20.0},
    ):
        response = client.get("/v1/companies/4170/roe", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["roe"] == 20.0


def test_roe_returns_404_for_unknown_company(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.company_service.fetch_roe", return_value=None):
        response = client.get("/v1/companies/999999/roe", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_payout_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch(
        "app.services.company_service.fetch_payout", return_value={"payout_avg_5y": 35.5}
    ):
        response = client.get("/v1/companies/4170/payout", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200


def test_dcf_fundamentals_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    fields = {
        "reference_year": 2025, "ebit": 50.0, "tax_rate": 25.0,
        "depreciation_amortization": 3.0, "capex": 4.0, "nwc_change": 1.0,
        "total_debt": 40.0, "cash": 25.0, "revenue": 100.0, "inventory": 8.0,
    }
    with patch("app.services.company_service.fetch_dcf_fundamentals", return_value=fields):
        response = client.get("/v1/companies/4170/dcf-fundamentals", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["ebit"] == 50.0
