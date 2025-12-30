# Responses & Tools (Function Calling) — How We Use It

Last verified: 2025-12-28

## Canonical docs
- Responses guide: `https://platform.openai.com/docs/guides/responses`
- Tools / function calling: `https://platform.openai.com/docs/guides/function-calling`
- API reference: `https://platform.openai.com/docs/api-reference`

## What we do in this repo today
We currently implement a **plan → confirm → execute** workflow using OpenAI **function calling** (via the Python SDK).

Key files:
- Planner: `src/agent/assistant.py` (`plan_task()`)
- Tool implementations: `src/agent/tools.py`
- Policy & confirmation: `src/security/policy.py`
- Task API: `src/api/routes/tasks.py`

## Why plan → confirm → execute
Because the assistant can contact real people (calls/SMS/email) and change your calendar, we enforce:
- **High-risk tools** (call/SMS/email/calendar): never execute without explicit approval
- **Low-risk tools** (web research): can execute immediately

Policy classification:
- `src/security/policy.py` → `tool_risk()` and `decide_confirmation()`

## How to add a new tool safely
1. Add implementation in `src/agent/tools.py` and return a structured JSON result.\n
2. Add a schema entry to `TOOLS` (name + JSON schema).\n
3. Add the handler to `TOOL_HANDLERS`.\n
4. Update policy:\n
   - If it has side effects, add it to the **high-risk** set in `src/security/policy.py`.\n
5. Add UI support if confirmation is required:\n
   - `frontend/src/App.tsx` shows “awaiting_confirmation” tasks with Approve/Reject.

## Guardrails we currently enforce
- Twilio signature validation for webhooks: `src/api/webhooks/twilio_webhook.py`
- Host allowlist for research: `src/tools/web_research.py`
- Godfather allowlist stored in gitignored `secrets/godfather.json`: `src/security/godfather_store.py`


