import sys
import types

import pytest
from fastapi.testclient import TestClient

# Provide a lightweight stub for optional calendar dependency used during app import
if "ics" not in sys.modules:
    sys.modules["ics"] = types.SimpleNamespace(Calendar=object)

from src.main import app


client = TestClient(app)


def test_tts_returns_audio_bytes(monkeypatch):
    class _FakeResp:
        content = b"abc"

    class _FakeSpeech:
        def create(self, **kwargs):
            return _FakeResp()

    class _FakeAudio:
        speech = _FakeSpeech()

    class _FakeClient:
        audio = _FakeAudio()

    monkeypatch.setattr("src.api.routes.audio.create_openai_client", lambda *a, **k: _FakeClient())

    resp = client.post("/api/audio/tts", json={"text": "hi", "voice": "alloy", "model": "tts-1", "format": "mp3"})
    assert resp.status_code == 200
    assert resp.content == b"abc"


def test_stt_returns_text(monkeypatch):
    class _FakeTranscriptionResp:
        text = "hello"

    class _FakeTranscriptions:
        def create(self, **kwargs):
            return _FakeTranscriptionResp()

    class _FakeAudio:
        transcriptions = _FakeTranscriptions()

    class _FakeClient:
        audio = _FakeAudio()

    monkeypatch.setattr("src.api.routes.audio.create_openai_client", lambda *a, **k: _FakeClient())

    resp = client.post("/api/audio/stt", files={"file": ("test.wav", b"RIFF....", "audio/wav")})
    assert resp.status_code == 200
    assert resp.json()["text"] == "hello"


