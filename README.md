# AI Voice Assistant

Voice-oriented assistant that plans tool calls and executes them across calls,
SMS, email, calendar, and web research. Built with OpenAI and Twilio. The
voice-to-voice loop (Twilio Media Streams + OpenAI Realtime) is planned but not
yet implemented.

## What it does now
- Plans tasks with OpenAI tool-calling and a confirmation policy layer
- Telephony & messaging: make calls and send SMS via Twilio; voice/status webhooks exposed
- Email: send via Gmail/Outlook/SMTP; read/list Gmail or Outlook when connected
- Calendar: create/list Google Calendar events (optional OAuth)
- Web research: allowlisted URL fetch for summarization (read-only)
- Context: contact memory, preference resolution, and orchestrator suggestions when data exists
- Cost/budget: per-task estimation, runtime tracking, and event logging
- Persistence: tasks/results stored via SQLAlchemy (SQLite fallback)
- Voice-to-voice bridge is not implemented (see `VoiceAssistant.handle_voice_conversation`)

## Architecture
- `src/agent/assistant.py` — plans tasks and executes tools with OpenAI
- `src/agent/tools.py` — Twilio calls/SMS, email send/read/list, calendar, web research
- `src/api/routes/tasks.py` — task lifecycle with confirmation and cost tracking
- `src/api/webhooks/twilio_webhook.py` — Twilio voice/status webhooks
- `src/telephony/` — Twilio service wrapper
- `src/memory/`, `src/orchestrator/` — contact memory and suggestions
- `src/cost/` — estimating, tracking, and logging provider costs
- `src/security/policy.py` — confirmation policy (Godfather token aware)
- `frontend/` — React UI for submitting tasks and monitoring status

## Quickstart
1. Backend
   - `cd "/Users/mr.008/Desktop/Projects/AI Caller"`
   - `python -m venv venv && source venv/bin/activate`
   - `pip install -r requirements.txt`
   - Copy `env.example` to `.env` and set: `OPENAI_API_KEY`, `OPENAI_MODEL`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `TWILIO_WEBHOOK_URL`, and `GODFATHER_API_TOKEN`
   - Start API: `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
   - Database falls back to SQLite when `DATABASE_URL` is empty
2. Frontend (optional)
   - `cd frontend && npm install`
   - `npm run dev` (Vite default: http://localhost:5173)
3. Health check: `GET http://localhost:8000/api/health`

## Configuration highlights
- Core: `APP_HOST`, `APP_PORT`, `FRONTEND_URL`, `GODFATHER_API_TOKEN`
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`; realtime vars exist but voice loop is not wired (`OPENAI_REALTIME_API_URL`, `OPENAI_REALTIME_MODEL`, `OPENAI_REALTIME_VOICE`)
- Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `TWILIO_WEBHOOK_URL`, plus media streams flags (`TWILIO_MEDIA_STREAMS_ENABLED`, `TWILIO_MEDIA_STREAMS_WS_BASE_URL`)
- Database: `DATABASE_URL` (Neon/Postgres supported; SQLite fallback)
- Email: Gmail/Outlook OAuth (`GMAIL_*`, `OUTLOOK_*`) or SMTP fallback (`SMTP_*`)
- Calendar: Google OAuth (`GOOGLE_OAUTH_*`) and `GOOGLE_CALENDAR_ID`
- Identity: `GODFATHER_PHONE_NUMBERS`, `GODFATHER_EMAIL` for policy context

## API quickstart
- Create a task:
```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -H "X-Godfather-Token: $GODFATHER_API_TOKEN" \
  -d '{"task": "Call +1234567890 and ask for the agenda", "actor_phone": "+15551234567"}'
```
- If the policy requires confirmation, approve with:
```bash
curl -X POST http://localhost:8000/api/tasks/{task_id}/confirm \
  -H "Content-Type: application/json" \
  -H "X-Godfather-Token: $GODFATHER_API_TOKEN" \
  -d '{"approve": true}'
```
- List tasks: `GET /api/tasks` (auth header required when token is set)
- Swagger UI: `GET /docs`

## Telephony
- Voice webhook: `POST {TWILIO_WEBHOOK_URL}/webhooks/twilio/voice`
- Status webhook: `POST {TWILIO_WEBHOOK_URL}/webhooks/twilio/status`
- Media Streams: set `TWILIO_MEDIA_STREAMS_ENABLED=true` and `TWILIO_MEDIA_STREAMS_WS_BASE_URL` when wiring realtime voice (not implemented yet)

## Documentation
See `DOCUMENTATION_OVERVIEW.md` for the curated map of guides and historical reviews.

## Deployment
- Docker: `Dockerfile` and `docker-compose.yml`
- Vercel: `vercel.json` and `api/index.py`

## License

MIT
