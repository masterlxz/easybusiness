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


def test_fundamentals_requires_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/us-stocks/AAPL/fundamentals")
    _teardown()

    assert response.status_code == 401


def test_fundamentals_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    fundamentals = {"lpa": 5.0, "vpa": 10.0, "roe": 20.0, "shares_outstanding": 100.0}
    with patch("app.services.us_stock_service.resolve_cik", return_value=320193):
        with patch(
            "app.services.us_stock_service.fetch_fundamentals", return_value=fundamentals
        ):
            response = client.get("/v1/us-stocks/AAPL/fundamentals", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["lpa"] == 5.0


def test_fundamentals_returns_404_for_unknown_ticker(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.us_stock_service.resolve_cik", return_value=None):
        response = client.get("/v1/us-stocks/NOTATICKER/fundamentals", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_dcf_fundamentals_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    fields = {
        "reference_year": 2025, "ebit": 500.0, "tax_rate": 25.0,
        "depreciation_amortization": 20.0, "capex": 30.0, "nwc_change": 5.0,
        "total_debt": 150.0, "cash": 80.0, "revenue": 900.0, "inventory": 40.0,
    }
    with patch("app.services.us_stock_service.resolve_cik", return_value=320193):
        with patch(
            "app.services.us_stock_service.fetch_dcf_fundamentals", return_value=fields
        ):
            response = client.get("/v1/us-stocks/AAPL/dcf-fundamentals", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["ebit"] == 500.0


def test_payout_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.us_stock_service.resolve_cik", return_value=320193):
        with patch(
            "app.services.us_stock_service.fetch_payout",
            return_value={"payout_avg_5y": 20.0},
        ):
            response = client.get("/v1/us-stocks/AAPL/payout", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["payout_avg_5y"] == 20.0
