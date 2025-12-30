import sys
import types

import pytest
from fastapi.testclient import TestClient

# Provide a lightweight stub for optional calendar dependency used during app import
if "ics" not in sys.modules:
    sys.modules["ics"] = types.SimpleNamespace(Calendar=object)

from src.main import app
from src.api.webhooks import twilio_webhook


client = TestClient(app)


def test_voice_webhook_returns_501_when_token_missing(monkeypatch):
    monkeypatch.setattr(twilio_webhook.settings, "TWILIO_AUTH_TOKEN", "")

    response = client.post("/webhooks/twilio/voice", data={})

    assert response.status_code == 501
    assert "TWILIO_AUTH_TOKEN" in response.text


def test_voice_webhook_returns_403_on_invalid_signature(monkeypatch):
    monkeypatch.setattr(twilio_webhook.settings, "TWILIO_AUTH_TOKEN", "dummy-token")

    response = client.post("/webhooks/twilio/voice", data={})

    # Voice webhooks return TwiML even on invalid signature so Twilio can play the error message.
    assert response.status_code == 200


def test_voice_webhook_succeeds_when_planning_and_no_tools(monkeypatch):
    # Bypass signature validation
    monkeypatch.setattr(twilio_webhook, "_validate_twilio_request", lambda request, form: (True, "ok"))
    monkeypatch.setattr(twilio_webhook.settings, "TWILIO_AUTH_TOKEN", "ignored-for-test")

    called = {"executed": False}

    async def _fake_execute_planned_tools(_planned):
        called["executed"] = True
        return []

    monkeypatch.setattr(twilio_webhook.assistant, "plan_task", lambda task, context=None: {
        "response": "done",
        "planned_tool_calls": [],
    })
    monkeypatch.setattr(twilio_webhook.assistant, "execute_planned_tools", _fake_execute_planned_tools)

    response = client.post(
        "/webhooks/twilio/voice",
        data={
            "SpeechResult": "hello",
            "From": "+15551234567",
            "To": "+15550000000",
        },
    )

    assert response.status_code == 200
    assert "done" in response.text
    # No tools, so executed should remain False
    assert called["executed"] is False

