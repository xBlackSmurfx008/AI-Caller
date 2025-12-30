# Codebase Cleanup Summary

Last updated: 2025-12-28  
For a current doc map, see `DOCUMENTATION_OVERVIEW.md`.

## Current footprint
- Core: `src/agent` (planning + tools), `src/api` (tasks + Twilio webhooks), `src/telephony`, `src/email`, `src/calendar`, `src/memory`, `src/orchestrator`, `src/cost`, `src/security`, `src/utils`, `src/tools/web_research`, `src/main.py`
- Persistence: SQLAlchemy with SQLite fallback; contact memory, cost logging, and preference resolution enabled
- Frontend: minimal React app in `frontend/` for task submission and status
- Docs: `README.md`, `DOCUMENTATION_OVERVIEW.md`, `RUNBOOK.md`, `env.example`, plus targeted guides (OpenAI voice, Twilio, security, error codes). Legacy review/audit files were removed to reduce noise (available via git history if needed).

## Removed/archived from pre-rebuild
- Legacy knowledge base, QA, escalation, template, and complex route stacks
- Heavy middleware (auth/metrics/RBAC/security headers) replaced with lightweight policy checks
- Old setup scripts, migrations, and unused configurations
- Historical audit/review documents were removed to reduce noise; retrieve via git history if needed.

## Next steps
- Wire OpenAI Realtime voice loop to Twilio Media Streams
- Extend persistence as needed (contacts, transcripts, richer task history)
- Add visuals/FAQ and a realtime tool-calling example (see `DOCUMENTATION_STATUS.md`)

