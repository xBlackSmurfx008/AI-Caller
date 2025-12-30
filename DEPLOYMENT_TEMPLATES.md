## Deployment Templates — Vercel (Frontend + FastAPI) and Neon Postgres

Use these templates to document and repeat deployments. Copy, fill in brackets, and commit alongside your project.

---

### 1) Vercel Project Summary
- **Project name**: [my-project]
- **Framework**: Vite/React frontend + FastAPI backend (Python)
- **Monorepo layout**: frontend/ and api/index.py
- **Vercel config**: `vercel.json` with Python function and static build
- **Primary domains**: [prod-domain], [preview-domain]

---

### 2) Environment Variables (Vercel)
| Name | Example | Required | Notes |
| --- | --- | --- | --- |
| APP_ENV | production | yes | Must be `production` in prod |
| SECRET_KEY | (generate) | yes | Strong random value |
| OPENAI_API_KEY | sk-... | yes | Needed for assistant |
| DATABASE_URL | postgresql://...neon.tech/neondb?sslmode=require | yes | Neon connection string |
| TWILIO_ACCOUNT_SID | ACxxxxx | optional | If telephony is used |
| TWILIO_AUTH_TOKEN | xxxxx | optional | If telephony is used |
| TWILIO_PHONE_NUMBER | +1555... | optional | If telephony is used |
| TWILIO_WEBHOOK_URL | https://[domain] | optional | Public base for Twilio callbacks |
| CORS_ORIGINS | https://[domain] | optional | Defaults to `*` |
| VITE_API_URL | https://[domain] | optional | Frontend base API URL |
| GOOGLE_OAUTH_CLIENT_SECRETS_JSON | {...} | optional | For Google Calendar |
| GMAIL_OAUTH_CLIENT_SECRETS_JSON | {...} | optional | For Gmail |
| OUTLOOK_OAUTH_CLIENT_SECRETS_JSON | {...} | optional | For Outlook |

---

### Credential Placeholders (fill these before deploy)
- **Neon Postgres**  
  - `DATABASE_URL`: `postgresql://<USER>:<PASSWORD>@<HOST>/<DB>?sslmode=require`  
    - Example: `postgresql://neondb_owner:<PASSWORD>@ep-xxxxx-pooler.neon.tech/neondb?sslmode=require`
- **OpenAI**  
  - `OPENAI_API_KEY`: `sk-...`
- **Twilio** (if used)  
  - `TWILIO_ACCOUNT_SID`: `AC...`  
  - `TWILIO_AUTH_TOKEN`: `<token>`  
  - `TWILIO_PHONE_NUMBER`: `+1555...`  
  - `TWILIO_WEBHOOK_URL`: `https://<your-domain>`
- **Google / Gmail** (if used)  
  - `GOOGLE_OAUTH_CLIENT_SECRETS_JSON`: JSON string  
  - `GMAIL_OAUTH_CLIENT_SECRETS_JSON`: JSON string
- **Outlook** (if used)  
  - `OUTLOOK_OAUTH_CLIENT_SECRETS_JSON`: JSON string

---

### 3) Build Commands (Vercel)
- Frontend: `npm install && npm run vercel-build` (from `frontend/`)
- Backend (Python): install from `api/requirements.txt`

---

### 4) Routing Template (vercel.json)
```json
{
  "version": 2,
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" },
    { "src": "frontend/package.json", "use": "@vercel/static-build", "config": { "distDir": "dist" } }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/webhooks/(.*)", "dest": "api/index.py" },
    { "src": "/docs", "dest": "api/index.py" },
    { "src": "/redoc", "dest": "api/index.py" },
    { "src": "/health", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "api/index.py" }
  ],
  "env": { "PYTHON_VERSION": "3.11" }
}
```
Notes:
- FastAPI serves `/api/*`; static SPA is mounted in `api/index.py`.
- Trailing slashes: use `/api/tasks/` etc.

---

### 5) Neon Postgres Template
- **Project**: [neon-project-name]
- **Branch**: main
- **Database**: [neondb]
- **Connection string**: `postgresql://neondb_owner:[password]@[host]/neondb?sslmode=require`
- **Pooler**: enabled (recommended for serverless)
- **Role**: neondb_owner (create a least-privilege role later)
- **SSL**: `sslmode=require`
- **Migrations**: `DATABASE_URL=... alembic upgrade head`

---

### 6) Local Validation Checklist
- [ ] `npm run build` (frontend) succeeds
- [ ] `pip install -r api/requirements.txt` succeeds
- [ ] `alembic upgrade head` against Neon succeeds
- [ ] `/health` returns healthy locally (`uvicorn src.main:app`)
- [ ] `/api/tasks/` returns 200 (even if empty list)

---

### 7) Production Smoke Checklist (Vercel)
- [ ] `/health` returns healthy on prod domain
- [ ] `/api/tasks/` returns 200 (empty list ok)
- [ ] SPA loads without 404 and renders navigation
- [ ] Critical env vars set in Vercel (see table)
- [ ] Twilio webhooks (if used) point to `https://[domain]/webhooks/twilio/...`

---

### 8) Troubleshooting Snippets
- **Static 404s**: ensure `vercel.json` routes catch-all to `api/index.py` and FastAPI mounts `frontend/dist`.
- **DB fallback**: In prod, enforce `DATABASE_URL`; do not fallback to SQLite.
- **Trailing slash 404**: use `/api/.../` (FastAPI’s default redirect may be stripped by proxies).


