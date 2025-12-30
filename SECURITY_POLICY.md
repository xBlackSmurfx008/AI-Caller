# Security Policy Documentation

**Last Updated**: 2025-01-29  
**Version**: 1.0

---

## Overview

The AI Voice Assistant implements a comprehensive security policy system that ensures high-risk actions (calls, SMS, emails, calendar modifications) require explicit confirmation before execution. This document explains the security architecture, policy rules, and implementation details.

---

## Architecture

### Plan → Confirm → Execute Workflow

The system uses a three-phase workflow to prevent unauthorized actions:

1. **Plan Phase**: AI analyzes the request and generates tool calls (no side effects)
2. **Confirm Phase**: Policy engine evaluates risk and determines if confirmation is required
3. **Execute Phase**: Tools execute only after confirmation (or for low-risk tools)

**Location**: `src/api/routes/tasks.py` → `create_task()` endpoint

### Security Policy Engine

**Location**: `src/security/policy.py`

The policy engine consists of:
- **Risk Classification**: Classifies tools as HIGH or LOW risk
- **Actor Identification**: Identifies who initiated the action (Godfather vs external)
- **Confirmation Decision**: Determines if confirmation is required

---

## Risk Classification

### HIGH-Risk Tools

These tools **always require confirmation** before execution:

| Tool Name | Description | Risk Reason |
|-----------|-------------|-------------|
| `make_call` | Initiates an outbound phone call | Contacts real people |
| `send_sms` | Sends a text message | Contacts real people |
| `send_email` | Sends an email | Contacts real people |
| `calendar_create_event` | Creates a calendar event | Modifies user's calendar |
| `calendar_update_event` | Updates a calendar event | Modifies user's calendar |
| `calendar_cancel_event` | Cancels a calendar event | Modifies user's calendar |

**Implementation**: `tool_risk()` function in `src/security/policy.py`

### LOW-Risk Tools

These tools can **auto-execute without confirmation**:

| Tool Name | Description | Risk Reason |
|-----------|-------------|-------------|
| `web_research` | Performs web research | Read-only operation |

**Note**: Unknown tools default to HIGH-risk until reviewed.

---

## Actor Identification

### Godfather Identity

The "Godfather" is the authorized user who owns the assistant. Godfather identity is verified through:

1. **Phone Number Allowlist**: E.164 formatted phone numbers
2. **Email Allowlist**: Email addresses

**Storage**: 
- `secrets/godfather.json` (gitignored, local storage)
- Environment variables: `GODFATHER_PHONE_NUMBERS`, `GODFATHER_EMAIL`

**Verification Function**: `is_godfather(actor)` in `src/security/policy.py`

### External Callers

Any caller who is not verified as Godfather is considered "external". External callers:
- Can never auto-execute HIGH-risk tools
- Always require confirmation for HIGH-risk actions
- Can execute LOW-risk tools (e.g., web research)

---

## Confirmation Decision Logic

### Policy Rules

The `decide_confirmation()` function implements these rules:

1. **LOW-risk tools**: No confirmation required (auto-execute)
2. **HIGH-risk tools + Godfather**: Confirmation required
3. **HIGH-risk tools + External**: Confirmation required + additional reason

**Implementation**:

```python
def decide_confirmation(actor: Actor, planned_calls: List[PlannedToolCall]) -> PolicyDecision:
    """
    Rules:
    - Any HIGH-risk tool => confirmation required.
    - External callers can never auto-execute HIGH-risk tools.
    """
    # Check risk level of all planned tools
    # Return PolicyDecision with requires_confirmation flag
```

### Policy Decision Structure

```python
@dataclass(frozen=True)
class PolicyDecision:
    requires_confirmation: bool  # True if confirmation needed
    risk: Risk                   # HIGH or LOW
    reasons: List[str]           # Human-readable reasons
```

---

## Implementation Details

### Task Creation Flow

1. **User submits task** → `POST /api/tasks/`
2. **Plan phase** → `assistant.plan_task()` generates tool calls
3. **Policy check** → `decide_confirmation(actor, planned_calls)`
4. **Response**:
   - If confirmation required: Task status = `awaiting_confirmation`
   - If auto-execute: Task status = `processing` (executes immediately)

### Confirmation Flow

1. **Frontend displays** → Approve/Reject buttons for `awaiting_confirmation` tasks
2. **User confirms** → `POST /api/tasks/{task_id}/confirm` with `approve: true/false`
3. **If approved** → `execute_planned_tools()` runs
4. **If rejected** → Task status = `rejected`, no execution

**Frontend**: `frontend/src/pages/Tasks.tsx` shows confirmation UI

---

## Security Considerations

### Phone Number Validation

- **Format**: E.164 format required (`+1234567890`)
- **Validation**: Regex pattern `^\+[1-9]\d{1,14}$`
- **Normalization**: `normalize_e164()` function strips whitespace

### Email Validation

- **Case-insensitive**: Email comparison is case-insensitive
- **Exact match**: Must match stored Godfather email exactly

### Webhook Security

Twilio webhooks require signature validation:

**Location**: `src/api/webhooks/twilio_webhook.py`

```python
from twilio.request_validator import RequestValidator

validator = RequestValidator(auth_token)
is_valid = validator.validate(url, params, signature)
```

---

## Configuration

### Environment Variables

```env
# Godfather identity (optional, can also use secrets/godfather.json)
GODFATHER_PHONE_NUMBERS=+1234567890,+0987654321
GODFATHER_EMAIL=user@example.com
```

### Godfather Store

**Location**: `src/security/godfather_store.py`

Stores Godfather identity in `secrets/godfather.json`:

```json
{
  "phone_numbers_csv": "+1234567890,+0987654321",
  "email": "user@example.com"
}
```

**Note**: This file is gitignored for security.

---

## Adding New Tools

When adding a new tool, you must classify its risk:

1. **Add tool handler** in `src/agent/tools.py`
2. **Add tool schema** to `TOOLS` array
3. **Classify risk** in `tool_risk()` function:
   ```python
   def tool_risk(tool_name: str) -> Tuple[Risk, List[str]]:
       high = {
           "your_new_tool": "reason why it's high-risk"
       }
       if tool_name in high:
           return Risk.HIGH, [high[tool_name]]
       # Or return Risk.LOW for low-risk tools
   ```

---

## Examples

### Example 1: Godfather Submits High-Risk Task

```python
# User: "Call John at +1234567890"
actor = Actor(kind="godfather", phone_number="+1234567890")
planned_calls = [PlannedToolCall(name="make_call", arguments={...})]

decision = decide_confirmation(actor, planned_calls)
# Result: requires_confirmation=True, risk=HIGH
# Task status: awaiting_confirmation
```

### Example 2: External Caller Submits High-Risk Task

```python
# External caller: "Call John at +1234567890"
actor = Actor(kind="external", phone_number="+9999999999")
planned_calls = [PlannedToolCall(name="make_call", arguments={...})]

decision = decide_confirmation(actor, planned_calls)
# Result: requires_confirmation=True, risk=HIGH
# Reasons: ["initiates an outbound call", "initiator is not Godfather"]
# Task status: awaiting_confirmation
```

### Example 3: Low-Risk Tool (Auto-Execute)

```python
# User: "Research the weather in San Francisco"
actor = Actor(kind="godfather", phone_number="+1234567890")
planned_calls = [PlannedToolCall(name="web_research", arguments={...})]

decision = decide_confirmation(actor, planned_calls)
# Result: requires_confirmation=False, risk=LOW
# Task status: processing (executes immediately)
```

---

## Troubleshooting

### Issue: Confirmation Not Required for High-Risk Tools

**Check**:
1. Is `tool_risk()` correctly classifying the tool?
2. Is `decide_confirmation()` being called?
3. Check task status in database/logs

### Issue: External Callers Can Execute High-Risk Tools

**Check**:
1. Is `is_godfather()` correctly identifying external callers?
2. Is confirmation UI showing in frontend?
3. Check policy decision in logs

### Issue: Godfather Not Recognized

**Check**:
1. Is phone number in E.164 format?
2. Is email exactly matching (case-insensitive)?
3. Check `secrets/godfather.json` or environment variables
4. Verify `is_godfather()` function logic

---

## Best Practices

1. **Always classify new tools** in `tool_risk()` function
2. **Default to HIGH-risk** for unknown tools (security-first)
3. **Test confirmation flow** for all high-risk tools
4. **Log policy decisions** for debugging and auditing
5. **Keep Godfather identity secure** (gitignored, encrypted if possible)

---

## Related Documentation

- [Agent Planning Framework](agent.md) - Section 4.5: Plan → Confirm → Execute Workflow
- [Agent Planning Framework](agent.md) - Section 4.6: Godfather Identity System
- [Agent Planning Framework](agent.md) - Section 7: Security & Privacy
- [OpenAI Agent Capabilities](OPENAI_AGENT_CAPABILITIES.md) - Tool execution flow

---

**Last Updated**: 2025-01-29  
**Maintained By**: Development Team

