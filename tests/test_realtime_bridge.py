import asyncio

import pytest

from src.voice import realtime_bridge
import base64
import json


class _DummyWebSocket:
    def __init__(self):
        self.sent = []
        self._incoming = []

    async def send(self, payload: str):
        self.sent.append(payload)

    def queue_incoming(self, payload: str):
        self._incoming.append(payload)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._incoming:
            raise StopAsyncIteration
        return self._incoming.pop(0)

    async def close(self):
        return None


def _close_task(coro):
    # Prevent "coroutine was never awaited" warnings in tests where we manually drive loops.
    try:
        coro.close()
    except Exception:
        pass
    return None


@pytest.mark.asyncio
async def test_realtime_bridge_start_does_not_crash(monkeypatch):
    ws = _DummyWebSocket()

    async def _fake_connect(*args, **kwargs):
        return ws

    bridge = realtime_bridge.get_realtime_bridge()
    bridge._sessions.clear()

    monkeypatch.setattr(realtime_bridge.websockets, "connect", _fake_connect)
    monkeypatch.setattr(realtime_bridge.asyncio, "create_task", _close_task)
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_API_URL", "wss://example.com")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview")

    await bridge.start(call_sid="CA123", actor=realtime_bridge.Actor(kind="external"))

    assert "CA123" in bridge._sessions
    assert ws.sent  # session.update should have been sent


@pytest.mark.asyncio
async def test_realtime_bridge_forwards_audio_to_twilio_sender(monkeypatch):
    ws = _DummyWebSocket()
    # base64 for 6 zero bytes (3 samples of PCM16@24k) -> 1 sample at 8k after downsample
    ws.queue_incoming(json.dumps({"type": "response.audio.delta", "delta": base64.b64encode(b"\x00" * 6).decode("utf-8")}))

    async def _fake_connect(*args, **kwargs):
        return ws

    bridge = realtime_bridge.get_realtime_bridge()
    bridge._sessions.clear()

    monkeypatch.setattr(realtime_bridge.websockets, "connect", _fake_connect)
    monkeypatch.setattr(realtime_bridge.asyncio, "create_task", _close_task)
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_API_URL", "wss://example.com")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview")

    sent = {"count": 0}

    async def _sender(_pcm16_8k: bytes):
        sent["count"] += 1

    await bridge.start(call_sid="CA456", actor=realtime_bridge.Actor(kind="external"), twilio_audio_sender=_sender)

    # run listener once (it will consume queued message and exit)
    await bridge._listen("CA456")

    assert sent["count"] == 1


@pytest.mark.asyncio
async def test_realtime_bridge_low_risk_tool_executes_and_submits_output(monkeypatch):
    ws = _DummyWebSocket()
    ws.queue_incoming(
        json.dumps(
            {
                "type": "conversation.item.requires_action",
                "item": {
                    "id": "item_1",
                    "required_action": {
                        "type": "submit_tool_outputs",
                        "submit_tool_outputs": {
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "name": "web_research",
                                    "parameters": {"url": "https://example.com"},
                                }
                            ]
                        },
                    },
                },
            }
        )
    )

    async def _fake_connect(*args, **kwargs):
        return ws

    bridge = realtime_bridge.get_realtime_bridge()
    bridge._sessions.clear()

    monkeypatch.setattr(realtime_bridge.websockets, "connect", _fake_connect)
    monkeypatch.setattr(realtime_bridge.asyncio, "create_task", _close_task)
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_API_URL", "wss://example.com")
    monkeypatch.setattr(realtime_bridge.settings, "OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview")

    async def _fake_web_research(**kwargs):
        return {"success": True, "text": "ok"}

    monkeypatch.setitem(realtime_bridge.TOOL_HANDLERS, "web_research", _fake_web_research)

    await bridge.start(call_sid="CA789", actor=realtime_bridge.Actor(kind="external"))
    await bridge._listen("CA789")

    # Find submit_tool_outputs message
    submit_msgs = [json.loads(m) for m in ws.sent if '"conversation.item.required_action.submit_tool_outputs"' in m]
    assert submit_msgs
    tool_outputs = submit_msgs[-1]["tool_outputs"]
    assert tool_outputs[0]["tool_call_id"] == "call_1"
    assert json.loads(tool_outputs[0]["output"])["success"] is True

