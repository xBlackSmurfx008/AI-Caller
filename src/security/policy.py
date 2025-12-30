"""Security & confirmation policy for the Godfather assistant."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.utils.config import get_settings
from src.security.godfather_store import load_identity


class Risk(str, Enum):
    LOW = "low"
    HIGH = "high"


@dataclass(frozen=True)
class Actor:
    """Who initiated the action."""

    # "godfather" or "external"
    kind: str
    phone_number: Optional[str] = None
    email: Optional[str] = None


@dataclass(frozen=True)
class PlannedToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass(frozen=True)
class PolicyDecision:
    requires_confirmation: bool
    risk: Risk
    reasons: List[str]


_E164_RE = re.compile(r"^\+[1-9]\d{1,14}$")


def normalize_e164(phone: str) -> str:
    phone = (phone or "").strip()
    return phone


def parse_phone_allowlist(csv_numbers: str) -> List[str]:
    raw = (csv_numbers or "").strip()
    if not raw:
        return []
    numbers = [normalize_e164(x) for x in raw.split(",")]
    return [n for n in numbers if n and _E164_RE.match(n)]


def is_godfather(actor: Actor) -> bool:
    settings = get_settings()
    stored = load_identity()
    allowlist = set(parse_phone_allowlist(stored.phone_numbers_csv)) | set(parse_phone_allowlist(settings.GODFATHER_PHONE_NUMBERS))
    if actor.phone_number and normalize_e164(actor.phone_number) in allowlist:
        return True
    stored_email = (stored.email or "").strip()
    env_email = (settings.GODFATHER_EMAIL or "").strip()
    if actor.email and stored_email and actor.email.lower() == stored_email.lower():
        return True
    if actor.email and env_email and actor.email.lower() == env_email.lower():
        return True
    return False


def tool_risk(tool_name: str) -> Tuple[Risk, List[str]]:
    """
    Classify tool calls.
    High-risk: contacting people or modifying calendar.
    Low-risk: research/summarization.
    """
    high = {
        "make_call": "initiates an outbound call",
        "send_sms": "sends an SMS",
        "send_email": "sends an email",
        "calendar_create_event": "creates a calendar event",
        "calendar_update_event": "updates a calendar event",
        "calendar_cancel_event": "cancels a calendar event",
    }
    low = {
        "web_research": "performs web research (read-only)",
        "read_email": "reads email content (read-only)",
        "list_emails": "lists/searches email (read-only)",
        "calendar_list_upcoming": "lists calendar events (read-only)",
    }
    if tool_name in high:
        return Risk.HIGH, [high[tool_name]]
    if tool_name in low:
        return Risk.LOW, [low[tool_name]]
    # Unknown tools default to high until reviewed
    return Risk.HIGH, ["unknown tool (default-high)"]


def decide_confirmation(actor: Actor, planned_calls: List[PlannedToolCall]) -> PolicyDecision:
    """
    Rules:
    - If AUTO_EXECUTE_HIGH_RISK is True, skip all confirmations (execute immediately).
    - Otherwise: Any HIGH-risk tool => confirmation required.
    - External callers can never auto-execute HIGH-risk tools (unless auto-execute is on).
    """
    settings = get_settings()
    reasons: List[str] = []
    worst = Risk.LOW
    for c in planned_calls:
        r, rs = tool_risk(c.name)
        reasons.extend(rs)
        if r == Risk.HIGH:
            worst = Risk.HIGH

    if worst == Risk.LOW:
        return PolicyDecision(requires_confirmation=False, risk=worst, reasons=reasons)

    # Auto-execute mode: skip confirmation for all actions
    if settings.AUTO_EXECUTE_HIGH_RISK:
        return PolicyDecision(requires_confirmation=False, risk=Risk.HIGH, reasons=reasons + ["auto-execute enabled"])

    # high-risk with confirmation required
    if is_godfather(actor):
        return PolicyDecision(requires_confirmation=True, risk=Risk.HIGH, reasons=reasons)
    return PolicyDecision(requires_confirmation=True, risk=Risk.HIGH, reasons=reasons + ["initiator is not Godfather"])


