# Deployment Guide for Neon/Vercel

This guide covers deploying the AI Caller application to Vercel with Neon PostgreSQL database.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Neon Account**: Sign up at [neon.tech](https://neon.tech) for PostgreSQL database
3. **GitHub Repository**: Your code should be in a GitHub repository

## Step 1: Set Up Neon Database

1. Create a new project in Neon
2. Copy the connection string (it will look like: `postgresql://user:password@host.neon.tech:5432/dbname?sslmode=require`)
3. Note: You'll need this for environment variables

## Step 2: Configure Vercel Environment Variables

In your Vercel project settings, add the following environment variables:

### Required Variables

```bash
# Application
APP_ENV=production
SECRET_KEY=<generate-a-strong-random-key>

# OpenAI
OPENAI_API_KEY=<your-openai-api-key>

# Twilio
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_PHONE_NUMBER=<your-twilio-phone-number>
TWILIO_WEBHOOK_URL=https://your-domain.vercel.app

# Database (Neon)
DATABASE_URL=<your-neon-connection-string>

# Godfather Identity
GODFATHER_PHONE_NUMBERS=<comma-separated-phone-numbers>
GODFATHER_EMAIL=<your-email>
```

### Optional Variables

```bash
# Google Calendar OAuth (if using)
GOOGLE_OAUTH_CLIENT_SECRETS_JSON=<json-string>
GOOGLE_CALENDAR_ID=primary

# Email Configuration (if using email tool)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-email>
SMTP_PASSWORD=<app-password>
SMTP_FROM_EMAIL=<your-email>

# CORS (defaults to *)
CORS_ORIGINS=https://your-domain.vercel.app

# Frontend API URL (if different from same domain)
VITE_API_URL=https://your-domain.vercel.app
```

## Step 3: Deploy to Vercel

### Option A: Via Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: Leave as default (or set if needed)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
4. Add all environment variables from Step 2
5. Click "Deploy"

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# For production
vercel --prod
```

## Step 4: Verify Deployment

1. Check the health endpoint: `https://your-domain.vercel.app/health`
2. Check API docs: `https://your-domain.vercel.app/docs`
3. Test the frontend: `https://your-domain.vercel.app`

## Step 5: Database Migration

The database tables will be automatically created on first API request. However, for production, you may want to run migrations manually:

```python
# In a local environment with DATABASE_URL set
from src.database.database import init_db
init_db()
```

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is correctly formatted
- Ensure SSL mode is set: `?sslmode=require` at the end of connection string
- Check Neon dashboard for connection limits

### API Routes Not Working

- Verify all routers are included in `api/index.py`
- Check Vercel function logs for import errors
- Ensure all dependencies are in `api/requirements.txt`

### Frontend Not Loading

- Verify `vercel.json` routing configuration
- Check that frontend build completes successfully
- Ensure static files are being served correctly

### Environment Variables Not Loading

- Verify variables are set in Vercel dashboard
- Restart deployment after adding new variables
- Check variable names match exactly (case-sensitive)

## Testing Connections

After deployment, test these endpoints:

1. **Health Check**: `GET /health`
2. **API Root**: `GET /`
3. **Tasks API**: `GET /api/tasks/`
4. **Calendar Status**: `GET /api/calendar/status`
5. **Settings**: `GET /api/settings/godfather`

## Post-Deployment Checklist

- [ ] Database connection working
- [ ] All API endpoints responding
- [ ] Frontend loading correctly
- [ ] Environment variables configured
- [ ] Twilio webhooks configured (update webhook URL in Twilio console)
- [ ] CORS configured for your domain
- [ ] Google Calendar OAuth configured (if using)

## Notes

- The application uses SQLite as a fallback if `DATABASE_URL` is not set (for local development)
- In production, always use Neon PostgreSQL via `DATABASE_URL`
- Task storage is now persistent using the database
- All routes are included in the Vercel serverless function

