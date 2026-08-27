from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

API_KEY_HEADER = {"X-API-Key": "test-key"}


def _override_get_db(db_session):
    def _get_db():
        yield db_session

    return _get_db


def test_missing_api_key_returns_401(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/macro-series/cdi")
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_wrong_api_key_returns_401(db_session, monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    from app.config import get_settings

    get_settings.cache_clear()
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/macro-series/cdi", headers={"X-API-Key": "wrong"})
    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert response.status_code == 401


def test_unknown_series_returns_404(db_session, monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    from app.config import get_settings

    get_settings.cache_clear()
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)
    response = client.get("/v1/macro-series/selic", headers=API_KEY_HEADER)
    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert response.status_code == 404


def test_success_returns_series_data(db_session, monkeypatch):
    monkeypatch.setenv("API_KEYS", "test-key")
    from app.config import get_settings

    get_settings.cache_clear()
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    client = TestClient(app)

    points = [{"reference_month": date(2026, 1, 1), "value_pct": 0.9}]
    with patch("app.services.macro_series_service.fetch_monthly_series", return_value=points):
        response = client.get("/v1/macro-series/cdi", headers=API_KEY_HEADER)

    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["series_code"] == "cdi"
    assert body["cached"] is False
    assert body["data"] == [{"reference_month": "2026-01-01", "value_pct": 0.9}]


def test_healthz_has_no_auth():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
