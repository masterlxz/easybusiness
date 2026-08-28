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


def test_eth_indicator_requires_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/crypto/eth-indicators/tvl-trend")
    _teardown()

    assert response.status_code == 401


def test_eth_indicator_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.sources.cripto_defillama.fetch_tvl_trend_mom", return_value=12.5):
        response = client.get("/v1/crypto/eth-indicators/tvl-trend", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["raw_value"] == 12.5


def test_eth_indicator_returns_404_for_unknown_code(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    response = client.get("/v1/crypto/eth-indicators/unknown-code", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_fear_greed_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    reading = {"value": 42, "classification": "Fear", "reading_date": date(2026, 1, 1)}
    with patch("app.services.crypto_service.fetch_fear_greed", return_value=reading):
        response = client.get("/v1/crypto/fear-greed", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["value"] == 42


def test_quote_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch(
        "app.services.crypto_service.resolve_coin_id",
        return_value={"coin_id": "bitcoin", "name": "Bitcoin"},
    ):
        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[{"price_date": date(2026, 1, 1), "price": 50000.0}],
        ):
            response = client.get("/v1/crypto/BTC/quote", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert response.json()["symbol"] == "BTC"
    assert response.json()["price"] == 50000.0


def test_quote_returns_404_for_unknown_symbol(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch("app.services.crypto_service.resolve_coin_id", return_value=None):
        response = client.get("/v1/crypto/NOTACOIN123/quote", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 404


def test_price_history_returns_200(db_session, monkeypatch):
    client = _client_with_auth(db_session, monkeypatch)
    with patch(
        "app.services.crypto_service.resolve_coin_id",
        return_value={"coin_id": "bitcoin", "name": "Bitcoin"},
    ):
        with patch(
            "app.services.crypto_service.fetch_market_chart",
            return_value=[{"price_date": date(2026, 1, 1), "price": 50000.0}],
        ):
            response = client.get("/v1/crypto/BTC/price-history", headers=API_KEY_HEADER)
    _teardown()

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
