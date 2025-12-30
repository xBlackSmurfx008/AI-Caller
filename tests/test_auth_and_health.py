from fastapi.testclient import TestClient

from src.main import app
from src.utils.config import get_settings


def _configure_auth(monkeypatch, *, api_token: str | None, enforce_in_tests: bool = True) -> None:
    if enforce_in_tests:
        monkeypatch.setenv("GODFATHER_API_TOKEN_ENFORCE_IN_TESTS", "1")
    else:
        monkeypatch.delenv("GODFATHER_API_TOKEN_ENFORCE_IN_TESTS", raising=False)

    if api_token is None:
        monkeypatch.delenv("GODFATHER_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("GODFATHER_API_TOKEN", api_token)

    # Refresh cached settings (middleware reads settings at request time)
    get_settings.cache_clear()


def test_health_is_public(monkeypatch):
    _configure_auth(monkeypatch, api_token="secret")
    client = TestClient(app)

    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_api_requires_token_when_configured(monkeypatch):
    _configure_auth(monkeypatch, api_token="secret")
    client = TestClient(app)

    r = client.post("/api/tasks", json={"task": "say hello"})
    assert r.status_code == 401

    r2 = client.post(
        "/api/tasks",
        headers={"X-Godfather-Token": "secret"},
        json={"task": "say hello"},
    )
    # May fail downstream if OpenAI not fully configured; but auth should pass.
    assert r2.status_code != 401


def test_api_is_public_when_token_not_set(monkeypatch):
    _configure_auth(monkeypatch, api_token=None, enforce_in_tests=True)
    client = TestClient(app)

    r = client.post("/api/tasks", json={"task": "say hello"})
    assert r.status_code != 401


def test_twilio_webhook_is_exempt_from_api_auth(monkeypatch):
    _configure_auth(monkeypatch, api_token="secret")
    client = TestClient(app)

    # No auth header on purpose; should not 401.
    # Signature validation will fail in this synthetic request; webhook returns TwiML error.
    r = client.post("/webhooks/twilio/voice", data={"CallSid": "CA123", "From": "+15550001111"})
    assert r.status_code == 200
    assert "application/xml" in r.headers.get("content-type", "")


