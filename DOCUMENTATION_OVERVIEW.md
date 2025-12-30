# Documentation Overview

Use this map to find the most relevant docs and avoid digging through older
review artifacts.

## Start here
- `README.md` — project overview, quickstart, and API basics
- `RUNBOOK.md` — fastest commands for local/prod and health checks
- `env.example` — full list of environment variables to copy into `.env`

## Current capabilities (snapshot)
- Task planner uses OpenAI tool-calling with a confirmation policy layer
- Tools: Twilio calls/SMS; email send/read/list (Gmail/Outlook/SMTP fallback)
- Calendar: create/list Google Calendar events (optional OAuth)
- Web research: allowlisted URL fetch for summarization (read-only)
- Context: contact memory, preference resolution, and orchestrator suggestions (when data exists)
- Cost/budget: per-task estimation, runtime tracking, and event logging
- Persistence: tasks and results stored via SQLAlchemy (SQLite fallback when `DATABASE_URL` is empty)
- Voice-to-voice loop with OpenAI Realtime + Twilio Media Streams is planned but not implemented yet

## Deep dives
- `OPENAI_VOICE_DOCUMENTATION.md` — voice/realtime integration plan
- `OPENAI_AGENT_CAPABILITIES.md` — agent behavior and tool usage
- `TOOLS_WIRING_DOCUMENTATION.md` & `TOOLS_SKILLS_VERIFICATION.md` — tool schemas and validation
- `TWILIO_DOCUMENTATION.md` & `TWILIO_API_CAPABILITIES.md` — telephony and SMS setup/reference
- `SECURITY_POLICY.md` — Godfather token, confirmation rules, and safety policies
- `ERROR_CODES.md` — error catalog
- `OPENAI_COMPLIANCE_REVIEW.md` — compliance guardrails

## Integrations & API references
- `docs/EMAIL_INTEGRATIONS_SETUP.md` — Gmail/Outlook/SMTP setup steps
- `docs/MESSAGING_USER_GUIDE.md` — messaging flow reference
- `docs/CONTACTS_API_DOCUMENTATION.md` & `docs/CONTACTS_QUICK_REFERENCE.md` — contacts API details
- `docs/openai/README.md` (plus `models.md`, `realtime.md`, `responses_and_tools.md`) — internal OpenAI notes

## Frontend
- `frontend/README.md` — UI development quickstart
- `frontend/CAPACITOR_CONTACTS_SETUP.md` — mobile contact sync setup

## Notes
- Legacy review/audit files were removed to reduce noise. If you need them, pull from git history.
- `REBUILD_PLAN.md` and `REBUILD_SUMMARY.md` capture the original rebuild context.

## Known follow-ups
- `DOCUMENTATION_STATUS.md` tracks remaining gaps (FAQ, visuals, realtime tool-calling guide).

