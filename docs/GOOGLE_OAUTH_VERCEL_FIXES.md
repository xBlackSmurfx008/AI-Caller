# Google OAuth on Vercel (Gmail + Calendar) — What We Fixed & Why

This project hit several **production-only** issues when connecting Gmail/Google Calendar via OAuth on **Vercel serverless**. This doc records what happened, what changed, and how to avoid the same problems in future projects.

---

## What broke (root causes)

### 1) Vercel filesystem is read-only

Vercel serverless functions run with a **read-only** filesystem. Any attempt to write tokens to `secrets/*` (or anywhere in the repo) will fail with:

- `Authorization Failed`
- `[Errno 30] Read-only file system: 'secrets'`

**Why it matters**: OAuth token storage must be **external** (DB, KV, Secrets Manager), not a file.

---

### 2) Google can return a token with *more scopes than requested*

Google OAuth supports incremental auth / previously granted scopes. For a given OAuth client, Google may return a token response whose scope set is a **superset** of what the current flow requested.

Some libraries (notably `google-auth-oauthlib`) can treat this as a mismatch and throw:

- `Scope has changed from "..." to "... ... https://www.googleapis.com/auth/calendar"`

**Why it matters**: If your app has multiple Google integrations (Gmail + Calendar), you must handle scope superset behavior or you’ll get intermittent OAuth failures.

---

## What we changed in this repo

### A) Store OAuth tokens in the database (serverless-safe)

We added/used an `oauth_tokens` table and now save tokens for:

- `provider="gmail"`
- `provider="google_calendar"`

If DB saving fails in serverless, we now **fail loudly** (instead of falling back to file storage).

**Files**
- `src/database/models.py`: added `OAuthToken` model (table: `oauth_tokens`)
- `src/email/gmail.py`: store Gmail token in DB; no file fallback on Vercel
- `src/calendar/google_calendar.py`: store Calendar token in DB; no file fallback on Vercel

---

### B) Auto-create the `oauth_tokens` table when saving a token

Serverless cold starts can skip app initialization paths. To keep OAuth robust, token-save now ensures the table exists before insert/update.

**Files**
- `src/email/gmail.py`
- `src/calendar/google_calendar.py`

---

### C) Use a consistent union of Google scopes to avoid “Scope has changed …”

We now request the same **union scope set** for both Gmail and Calendar OAuth starts:

- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/calendar`

This prevents the library from seeing “unexpected extra scopes” in the token exchange result.

**Files**
- `src/email/gmail.py`: `REQUESTED_GOOGLE_SCOPES`, `REQUIRED_GMAIL_SCOPES`
- `src/calendar/google_calendar.py`: `REQUESTED_GOOGLE_SCOPES`, `REQUIRED_CALENDAR_SCOPES`

---

### D) Don’t strictly bind stored credentials to an expected scope list

When loading stored credentials, we stopped calling:

- `Credentials.from_authorized_user_info(token_data, scopes=[...])`

and instead load the token as-is, then verify it has the **required scopes** using:

- `creds.has_scopes([...])`

This works correctly even if the token has a superset of scopes.

---

## How to replicate this correctly in future projects

### 1) Always store OAuth tokens outside the filesystem in serverless

Use one of:
- Postgres table (recommended)
- Redis/KV
- Cloud secrets store

Do **not** use `secrets/*.json` token files in serverless.

---

### 2) Decide your scope strategy up front

If your app uses multiple Google APIs (Gmail + Calendar), choose one:

- **Union scopes** (what we did): request a consistent scope set for all Google flows
- **Separate OAuth clients per integration**: one client for Gmail, one for Calendar (avoids scope mixing, but adds setup overhead)

Union scopes is simplest for internal tools; separate clients may be preferable for principle-of-least-privilege in customer-facing SaaS.

---

### 3) Configure redirect URIs in Google Cloud Console

Add these **Authorized redirect URIs**:

- `https://<YOUR_DOMAIN>/api/gmail/oauth/callback`
- `https://<YOUR_DOMAIN>/api/calendar/oauth/callback`

If you also use a frontend OAuth landing page, ensure the backend redirects to:

- `https://<YOUR_DOMAIN>/oauth/callback?code=success&service=gmail`
- `https://<YOUR_DOMAIN>/oauth/callback?code=success&service=calendar`

---

## Troubleshooting checklist

### If you see `Read-only file system: 'secrets'`
- You are trying to write token files on Vercel.
- Fix: store tokens in DB/KV and remove file fallback in serverless.

### If you see `Scope has changed from ... to ...`
- Your requested scopes differ from what Google returns (superset behavior).
- Fix: union scopes OR separate OAuth clients.

### If “Connect Gmail” returns to app but status stays disconnected
- The callback likely failed to persist token.
- Fix: check DB connectivity + ensure `oauth_tokens` exists + check logs for DB exceptions.


