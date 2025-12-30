import pytest

from src.security.policy import tool_risk, Risk


@pytest.mark.parametrize(
    "tool, expected_risk",
    [
        ("make_call", Risk.HIGH),
        ("send_sms", Risk.HIGH),
        ("send_email", Risk.HIGH),
        ("calendar_create_event", Risk.HIGH),
        ("calendar_update_event", Risk.HIGH),
        ("calendar_cancel_event", Risk.HIGH),
        ("web_research", Risk.LOW),
        ("read_email", Risk.LOW),
        ("list_emails", Risk.LOW),
        ("calendar_list_upcoming", Risk.LOW),
    ],
)
def test_tool_risk_classification(tool, expected_risk):
    risk, _ = tool_risk(tool)
    assert risk == expected_risk


def test_unknown_tool_defaults_high():
    risk, reasons = tool_risk("unknown_tool")
    assert risk == Risk.HIGH
    assert reasons

