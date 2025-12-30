### Runbook (Local + Production)

### Local dev
- **Backend**:
  - `cd "/Users/mr.008/Desktop/Projects/AI Caller"`
  - `source venv/bin/activate`
  - `pip install -r requirements.txt`
  - Copy `env.example` → `.env` (Cursor global ignore may block dotfiles in this sandbox; on your machine, create `.env` normally)
  - `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
- **Frontend**:
  - `cd frontend`
  - `npm install`
  - `npm run dev`

### Health
- `GET /api/health`

### Auth (Godfather-only)
- Set `GODFATHER_API_TOKEN`.
- Send requests with either:
  - `X-Godfather-Token: <token>` or
  - `Authorization: Bearer <token>`
- Exempt:
  - `/api/health*`
  - `/api/*/oauth/*` (OAuth)
  - `/webhooks/twilio/*` (Twilio)

### Twilio setup
- **Account SID must start with `AC...`** (not `SK...`).
- Configure your Twilio phone number webhooks:
  - Voice webhook: `POST {TWILIO_WEBHOOK_URL}/webhooks/twilio/voice`
  - Status webhook: `POST {TWILIO_WEBHOOK_URL}/webhooks/twilio/status`
- For voice-to-voice:
  - Host a public WebSocket server
  - Set `TWILIO_MEDIA_STREAMS_ENABLED=true`
  - Set `TWILIO_MEDIA_STREAMS_WS_BASE_URL=wss://<public-host>`

### Database (Neon)
- Set `DATABASE_URL` to your Neon connection string.
- If Postgres driver isn’t available, app falls back to SQLite for local dev.

### Migrations (Alembic)
- Install: `pip install alembic`
- Create schema:
  - `alembic upgrade head`

### Google Calendar
- Optional. Install deps:
  - `pip install google-api-python-client google-auth google-auth-oauthlib`
- Set OAuth client secrets via env.
- Connect via `GET /api/calendar/oauth/start`.


