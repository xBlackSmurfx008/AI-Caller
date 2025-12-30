import types

import pytest

from src.agent.assistant import VoiceAssistant


def test_plan_task_parses_responses_output(monkeypatch):
    assistant = VoiceAssistant()

    # Force responses path
    monkeypatch.setattr("src.agent.assistant.settings.OPENAI_USE_RESPONSES", True)

    fake_output = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "ok"}],
        },
        {
            "type": "function_call",
            "name": "send_sms",
            "arguments": '{"to_number":"+15551234567","message":"hi"}',
            "id": "call_1",
        },
    ]

    fake_resp = {"output": fake_output}

    class _FakeResponses:
        def create(self, **kwargs):
            return fake_resp

    assistant.client.responses = _FakeResponses()

    plan = assistant.plan_task("text bob", context={})
    assert plan["response"] == "ok"
    assert plan["planned_tool_calls"][0]["name"] == "send_sms"
    assert plan["planned_tool_calls"][0]["arguments"]["to_number"] == "+15551234567"

