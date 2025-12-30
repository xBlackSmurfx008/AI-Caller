import types

import pytest

from src.agent.assistant import VoiceAssistant
from src.utils.errors import OpenAIError


class _FakeToolCall:
    def __init__(self, name: str, arguments: str):
        self.function = types.SimpleNamespace(name=name, arguments=arguments)


class _FakeMessage:
    def __init__(self, content: str, tool_calls):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message):
        self.message = message


class _FakeResponse:
    def __init__(self, message):
        self.choices = [_FakeChoice(message)]
        self.usage = None
        self.model = "test-model"
        self.id = "resp_test"


def test_plan_task_rejects_invalid_tool_arguments_json(monkeypatch):
    assistant = VoiceAssistant()

    fake_msg = _FakeMessage(
        content="doing it",
        tool_calls=[_FakeToolCall("send_sms", "{not json}")],
    )
    fake_resp = _FakeResponse(fake_msg)

    monkeypatch.setattr(
        assistant.client.chat.completions,
        "create",
        lambda **kwargs: fake_resp,
    )

    with pytest.raises(OpenAIError) as exc:
        assistant.plan_task("text bob")

    assert "invalid json arguments" in str(exc.value).lower()


def test_plan_task_accepts_valid_tool_arguments_json(monkeypatch):
    assistant = VoiceAssistant()

    fake_msg = _FakeMessage(
        content="ok",
        tool_calls=[_FakeToolCall("send_sms", '{"to_number":"+15551234567","message":"hi"}')],
    )
    fake_resp = _FakeResponse(fake_msg)

    monkeypatch.setattr(
        assistant.client.chat.completions,
        "create",
        lambda **kwargs: fake_resp,
    )

    plan = assistant.plan_task("text bob")
    assert plan["success"] is True
    assert plan["planned_tool_calls"][0]["name"] == "send_sms"

