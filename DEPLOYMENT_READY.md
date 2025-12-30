# Deployment Ready Checklist

## ✅ Completed Tasks

### 1. Database Connection Setup
- ✅ Added `DATABASE_URL` to `src/utils/config.py`
- ✅ Created database connection module (`src/database/database.py`)
- ✅ Created Task model (`src/database/models.py`)
- ✅ Supports both Neon PostgreSQL (production) and SQLite (local dev)

### 2. Task Persistence
- ✅ Replaced in-memory task storage with database persistence
- ✅ Updated all task routes to use database sessions
- ✅ Tasks now persist across server restarts

### 3. Vercel Configuration
- ✅ Updated `vercel.json` to include frontend build
- ✅ Configured routing for both API and frontend
- ✅ Added all API routes to `api/index.py`:
  - Tasks API (`/api/tasks`)
  - Calendar API (`/api/calendar`)
  - Settings API (`/api/settings`)
  - Twilio Webhooks (`/webhooks/twilio`)

### 4. Frontend Configuration
- ✅ Updated API base URL to work in production (uses same domain)
- ✅ Added `vercel-build` script to `package.json`

### 5. Dependencies
- ✅ Updated `api/requirements.txt` with all necessary packages:
  - `sqlalchemy` for database ORM
  - `psycopg2-binary` for PostgreSQL connection
  - All other required dependencies

### 6. Documentation
- ✅ Created `DEPLOYMENT.md` with deployment instructions
- ✅ Created `CONNECTION_TESTING.md` with testing guide

## 🔧 Required Environment Variables for Vercel

Set these in your Vercel project settings:

### Critical (Required)
```bash
DATABASE_URL=postgresql://user:password@host.neon.tech:5432/dbname?sslmode=require
OPENAI_API_KEY=your-key
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.vercel.app
SECRET_KEY=strong-random-key
```

### Important (Recommended)
```bash
GODFATHER_PHONE_NUMBERS=+1234567890
GODFATHER_EMAIL=your-email@example.com
CORS_ORIGINS=https://your-domain.vercel.app
```

### Optional
```bash
GOOGLE_OAUTH_CLIENT_SECRETS_JSON={...}
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email
SMTP_PASSWORD=app-password
```

## 📋 Pre-Deployment Steps

1. **Set up Neon Database**
   - Create Neon project
   - Copy connection string
   - Add to Vercel as `DATABASE_URL`

2. **Configure Vercel**
   - Import GitHub repository
   - Add all environment variables
   - Deploy

3. **Test Connections**
   - Run health check: `/health`
   - Test API endpoints
   - Verify database persistence
   - Test frontend

## 🚀 Deployment Commands

```bash
# Via Vercel CLI
vercel --prod

# Or push to main branch (if connected to Vercel)
git push origin main
```

## 📝 Post-Deployment Verification

1. ✅ Health endpoint responds: `GET /health`
2. ✅ API docs accessible: `GET /docs`
3. ✅ Tasks API works: `GET /api/tasks/`
4. ✅ Tasks persist in database
5. ✅ Frontend loads correctly
6. ✅ CORS configured properly

## 🔍 Testing Endpoints

After deployment, test these:

```bash
# Health
curl https://your-domain.vercel.app/health

# Tasks
curl https://your-domain.vercel.app/api/tasks/

# Create task
curl -X POST https://your-domain.vercel.app/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"task": "Test task"}'
```

## ⚠️ Notes

- Database tables are auto-created on first use
- SQLite fallback works for local development
- All routes are included in Vercel serverless function
- Frontend and API are served from same domain

## 📚 Additional Resources

- See `DEPLOYMENT.md` for detailed deployment steps
- See `CONNECTION_TESTING.md` for testing procedures

---

**Status**: ✅ Ready for deployment to Neon/Vercel

