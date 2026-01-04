# OAuth Token Storage (Serverless-Safe Pattern)

This repo is deployed on **Vercel**, which runs the backend as **serverless functions**.

Serverless implications:
- You **cannot** rely on local files for persistence.
- The filesystem is effectively **read-only** for our use case.
- Each invocation may run on a different instance.

Therefore OAuth tokens must be stored in a **shared external system**.

---

## Pattern used in this repo

### Storage: Postgres table (`oauth_tokens`)

We store token JSON blobs in a single table keyed by `provider`.

Providers used:
- `gmail`
- `google_calendar`
- (optionally future) `outlook`, etc.

The table is defined in `src/database/models.py` as `OAuthToken`.

---

## Why we do this

### Avoids read-only filesystem errors on Vercel

Any code that tries to write token files (e.g. `secrets/gmail_token.json`) may crash with:

- `[Errno 30] Read-only file system: 'secrets'`

### Avoids “token disappears” between requests

Even if a file write “worked” on one instance, it would not persist reliably across invocations.

---

## Implementation notes

### Auto-create table on token save

In serverless, app init paths may be skipped on cold starts. To make OAuth robust, token save code ensures the `oauth_tokens` table exists right before it writes.

### No file fallback in serverless

In production/serverless, if DB save fails we error out (and show a clear error on the frontend) rather than attempting a doomed file write.

### Scope validation

Tokens are loaded from DB without forcing an expected scope list. We validate required scopes via:
- `creds.has_scopes([...])`

This supports Google’s incremental scope behavior.

---

## Reusing this pattern in other projects

You can reuse the exact approach with minimal changes:

- Add `oauth_tokens` table
- Store token JSON per provider
- Load token JSON into `Credentials.from_authorized_user_info(token_json)` (no strict scope list)
- Validate required scopes with `has_scopes`

If you want stricter access control per feature:
- Use separate OAuth clients for Gmail vs Calendar
- Store separate tokens per client/provider


