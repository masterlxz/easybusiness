from datetime import date
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


def test_quote_requires_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/stocks/PETR4/quote")
    _teardown()

    assert response.status_code == 401


def test_quote_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    quote = {"price": 38.5, "name": "Petrobras", "exchange": "B3", "currency": "BRL"}
    with patch("app.services.stock_service.fetch_quote", return_value=quote):
        response = client.get("/v1/stocks/PETR4/quote", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["price"] == 38.5


def test_technicals_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    technicals = {"sma_50": None, "sma_100": None, "sma_200": None, "cagr_5y": None, "cagr_10y": None}
    with patch("app.services.stock_service.fetch_technicals", return_value=technicals):
        response = client.get("/v1/stocks/PETR4/technicals", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200


def test_dividends_avg_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch(
        "app.services.stock_service.fetch_dividends_avg",
        return_value={"avg_dividend_5y": 1.5},
    ):
        response = client.get("/v1/stocks/PETR4/dividends-avg", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["avg_dividend_5y"] == 1.5


def test_dividends_avg_returns_404_without_data(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.stock_service.fetch_dividends_avg", return_value=None):
        response = client.get("/v1/stocks/MGLU3/dividends-avg", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_price_history_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    points = [{"price_date": date(2026, 1, 2), "close_price": 10.0}]
    with patch("app.services.stock_service.fetch_price_history", return_value=points):
        response = client.get("/v1/stocks/PETR4/price-history", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_dividend_payments_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    payments = [
        {
            "payment_date": date(2026, 1, 2),
            "amount": 1.0,
            "price_at_payment": 20.0,
            "yield_pct": 5.0,
        }
    ]
    with patch("app.services.stock_service.fetch_dividend_payments", return_value=payments):
        response = client.get("/v1/stocks/PETR4/dividend-payments", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
