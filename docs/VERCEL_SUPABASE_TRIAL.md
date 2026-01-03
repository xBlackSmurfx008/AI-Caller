## Vercel + Supabase production trial (recommended setup for this repo)

This repo can deploy to Vercel as:
- **Frontend**: static (`frontend/dist`)
- **Backend**: Python serverless function (`api/index.py`)

Because serverless does not support long-running background loops reliably, this repo also includes
`GET /api/cron/tick` and a Vercel Cron job that calls it every 10 minutes.

### 1) Create a Supabase project + database URL

- Create a Supabase project
- Copy the **connection string** and set it as:
  - `DATABASE_URL=postgresql://...`

Notes:
- Supabase typically requires SSL; the app will default to `sslmode=require` for Postgres if not provided.

### 2) Run migrations against Supabase

From your machine:

```bash
cd "/Users/mr.008/Desktop/Projects/AI Caller"
export DATABASE_URL="postgresql://..."
source venv/bin/activate
alembic upgrade head
```

### 3) Create a Vercel project from this repo

In Vercel:
- Import the repo
- Ensure **Python version 3.11** (already configured in `vercel.json`)

### 4) Set Vercel Environment Variables (Production)

Required:
- `DATABASE_URL` (Supabase Postgres)
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (e.g. `gpt-4o`)
- `TWILIO_ACCOUNT_SID` (starts with `AC`)
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `TWILIO_WEBHOOK_URL` (your Vercel deployment URL, e.g. `https://your-app.vercel.app`)

Strongly recommended:
- `APP_ENV=production`
- `GODFATHER_API_TOKEN=<strong-random-secret>` (enables auth on `/api/*`)
- `AUTO_EXECUTE_HIGH_RISK=false` (safer for a trial)
- `CORS_ORIGINS=["https://your-app.vercel.app"]` (or your custom domain)

Optional (Google Calendar):
- `GOOGLE_OAUTH_CLIENT_SECRETS_FILE=config/google_oauth_credentials.json`
- `GOOGLE_OAUTH_TOKEN_FILE=config/google_oauth_token.json`
- `GOOGLE_CALENDAR_ID=primary`

### 5) Configure Google OAuth redirect URIs

In Google Cloud Console (OAuth client):
- Add redirect URI:
  - `https://<your-vercel-domain>/api/calendar/oauth/callback`

If you use Gmail OAuth also add:
- `https://<your-vercel-domain>/api/gmail/oauth/callback`

### 6) Configure Twilio webhooks to your Vercel URL

Set your Twilio phone number webhooks to:
- Voice: `POST https://<your-vercel-domain>/webhooks/twilio/voice`
- Status: `POST https://<your-vercel-domain>/webhooks/twilio/status`

### 7) Confirm cron is running

Vercel Cron calls:
- `GET /api/cron/tick` every 10 minutes

This performs serverless-safe maintenance:
- reminder checks (best-effort)
- messaging summary processing (best-effort)
- suggestion expiration
- budget checks


