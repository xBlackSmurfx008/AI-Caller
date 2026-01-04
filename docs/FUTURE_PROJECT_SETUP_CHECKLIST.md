# Future Project Setup Checklist (Vercel + Postgres + Google OAuth)

This is a reusable checklist for spinning up a new project with the same architecture patterns as **AI Caller**:

- Frontend: Vercel (React/Vite)
- Backend: Vercel (FastAPI serverless)
- DB: Postgres (Supabase/Neon/etc.)
- OAuth: Google (Gmail + Calendar)

---

## 1) Vercel project layout expectations

This repo uses:

- `frontend/` for the Vite/React app
- `api/index.py` for the Vercel serverless entrypoint (FastAPI)
- `vercel.json` for routing + cron config

Make sure your new repo follows the same structure or update build settings accordingly.

---

## 2) Required environment variables (backend)

Set these in **Vercel Project → Settings → Environment Variables** (Production + Preview as needed):

### Core
- `APP_ENV=production`
- `OPENAI_API_KEY=...`
- `TWILIO_ACCOUNT_SID=AC...`
- `TWILIO_AUTH_TOKEN=...`
- `TWILIO_PHONE_NUMBER=+1...`
- `DATABASE_URL=postgresql://...`
- `GODFATHER_API_TOKEN=...` (if using the “godfather token” auth gate)

### Google OAuth (client secrets)
Provide either:
- `GMAIL_OAUTH_CLIENT_SECRETS_JSON` (recommended on Vercel)
- `GOOGLE_OAUTH_CLIENT_SECRETS_JSON`

Notes:
- The JSON must be the OAuth client secrets JSON from Google Cloud Console.
- Do not commit secrets files to git.

### Optional hardening
- `DB_FORCE_IPV4=1` (helps on serverless if IPv6 DNS breaks connections)
- `DISABLE_BACKGROUND_TASKS=1` (serverless safety)

---

## 3) Required environment variables (frontend)

Set in Vercel for the frontend build:

- `VITE_API_BASE_URL=https://<YOUR_DOMAIN>` (or leave empty if `axios` uses relative `/api`)
- `VITE_GODFATHER_TOKEN=...` (if the frontend stores/uses it)
- `VITE_SUPABASE_URL=...` + `VITE_SUPABASE_ANON_KEY=...` (if using Supabase auth)

---

## 4) Database migration / schema

Minimum requirements:
- DB must be reachable from Vercel
- Tables are created on startup or via migrations

For OAuth persistence in serverless:
- Ensure the `oauth_tokens` table exists (or auto-create it on token save as done in this repo).

---

## 5) Google Cloud Console OAuth config

Go to Google Cloud Console:
- APIs & Services → Credentials → OAuth 2.0 Client IDs

### Authorized JavaScript origins
- `https://<YOUR_DOMAIN>`

### Authorized redirect URIs
- `https://<YOUR_DOMAIN>/api/gmail/oauth/callback`
- `https://<YOUR_DOMAIN>/api/calendar/oauth/callback`

### Scopes strategy (important)
If you run **both** Gmail and Calendar:
- Request a **union** scope set for all Google OAuth flows, OR
- Use separate OAuth clients (one per integration)

Union scopes is simpler and avoids “Scope has changed …” issues.

---

## 6) Common gotchas

### Vercel filesystem
- Treat it as **read-only**
- Do **not** write token files in `secrets/` on Vercel
- Persist tokens in DB/KV instead

### OAuth refresh tokens
To consistently receive refresh tokens:
- Use `access_type=offline`
- Use `prompt=consent`

This repo’s OAuth flow already sets these.

---

## 7) Smoke tests (production trial readiness)

After deploy:
- `GET /api/health` → returns `healthy`
- `GET /api/health/integrations` → DB/OpenAI/Twilio show expected status
- Connect Gmail → `GET /api/gmail/status` shows `connected: true`
- Connect Calendar → `GET /api/calendar/status` shows `connected: true`


