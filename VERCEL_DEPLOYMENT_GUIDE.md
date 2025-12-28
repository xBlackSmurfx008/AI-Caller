# Vercel Deployment Guide for AI Caller

This guide will help you deploy your FastAPI backend to Vercel for webhook support.

## Prerequisites

- **GitHub Account** - Repository must be on GitHub for Vercel integration
- **Vercel Account** - Free tier available at https://vercel.com
- **Python 3.11+** - Vercel supports Python 3.11

## Architecture Overview

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│   GitHub Repo   │────────▶│    Vercel    │────────▶│   Twilio    │
│  (Source Code)  │  Deploy │  (Hosting)   │  Webhook│  (Calls)    │
└─────────────────┘         └──────────────┘         └─────────────┘
                                      │
                                      │
                              ┌───────▼────────┐
                              │  Live URL      │
                              │  *.vercel.app  │
                              └────────────────┘
```

**How it works:**
1. Code is pushed to GitHub
2. Vercel automatically builds and deploys from GitHub
3. Vercel provides a public URL for webhooks
4. Twilio sends webhook requests to Vercel URL

## Step 1: Prepare Your Repository

### 1.1 Verify Files Are Created

Ensure these files exist in your repository:
- ✅ `vercel.json` - Vercel configuration
- ✅ `api/index.py` - Vercel serverless function entry point
- ✅ `requirements.txt` - Python dependencies

### 1.2 Commit and Push to GitHub

```bash
git add vercel.json api/index.py
git commit -m "Add Vercel deployment configuration"
git push origin main
```

## Step 2: Link Repository to Vercel

### Option A: Via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit https://vercel.com
   - Sign in with GitHub (recommended for seamless integration)

2. **Import Project**
   - Click **"Add New..."** → **"Project"**
   - Select your GitHub repository (`AI Caller`)
   - Click **"Import"**

3. **Configure Project Settings**
   - **Framework Preset:** Other (or Python)
   - **Root Directory:** `./` (root of repository)
   - **Build Command:** Leave empty (Vercel auto-detects Python)
   - **Output Directory:** Leave empty
   - **Install Command:** `pip install -r requirements.txt`

4. **Initial Deploy**
   - Click **"Deploy"** (we'll add environment variables after first deploy)
   - Wait for build to complete (2-5 minutes)

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI (optional)
npm i -g vercel

# Or use npx (no installation)
npx vercel login

# Link project
npx vercel link

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No (create new)
# - Project name? ai-caller
# - Directory? ./
```

## Step 3: Get Production URL

After first deployment, Vercel will provide a URL:
- Format: `https://[project-name].vercel.app`
- **Save this URL** - you'll need it for `TWILIO_WEBHOOK_URL`

Example: `https://ai-caller.vercel.app`

## Step 4: Configure Environment Variables

### 4.1 Access Environment Variables Settings

1. Go to your Vercel project dashboard
2. Click **Settings** → **Environment Variables**

### 4.2 Add Required Variables

Add each variable for **Production**, **Preview**, and **Development** environments:

#### Core Application Variables

```
APP_NAME=AI Caller
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=[generate-secure-random-key]
```

#### Database Variables

```
DATABASE_URL=[your-database-connection-string]
REDIS_URL=[your-redis-connection-string]
```

**Note:** For production, use a managed database service (Supabase, Railway, etc.)

#### OpenAI Variables

```
OPENAI_API_KEY=[your-openai-api-key]
OPENAI_MODEL=gpt-4o-realtime-preview
OPENAI_REALTIME_API_URL=wss://api.openai.com/v1/realtime
```

#### Twilio Variables

```
TWILIO_ACCOUNT_SID=[your-twilio-account-sid]
TWILIO_AUTH_TOKEN=[your-twilio-auth-token]
TWILIO_PHONE_NUMBER=[your-twilio-phone-number]
TWILIO_WEBHOOK_URL=https://[your-project].vercel.app
```

**Important:** 
- `TWILIO_WEBHOOK_URL` must be your actual Vercel URL
- Update this after first deployment

#### Security Variables

```
JWT_SECRET_KEY=[generate-secure-random-key]
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

#### Optional Variables

```
CORS_ORIGINS=["*"]
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 4.3 Generate Secure Keys

Generate secure random strings for secrets:

```bash
# Generate SECRET_KEY
openssl rand -base64 32

# Generate JWT_SECRET_KEY
openssl rand -base64 32
```

### 4.4 Set Environment Scope

For each variable, select which environments it applies to:
- ✅ **Production** - Live production URL
- ✅ **Preview** - Preview deployments (pull requests)
- ✅ **Development** - Local development (if using Vercel CLI)

### 4.5 Update TWILIO_WEBHOOK_URL After First Deploy

1. After first deployment, note your Vercel URL
2. Go to **Settings** → **Environment Variables**
3. Update `TWILIO_WEBHOOK_URL` to your actual Vercel URL
4. Redeploy (or wait for next push to trigger auto-deploy)

## Step 5: Deploy to Production

### 5.1 Automatic Deployment (Recommended)

Once linked to GitHub, Vercel automatically deploys on:
- Push to `main` branch → Production deployment
- Push to other branches → Preview deployment
- Pull requests → Preview deployment

**No manual action needed** - just push to GitHub:

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

### 5.2 Manual Deployment

**Via Dashboard:**
- Go to **Deployments** tab
- Click **"Redeploy"** on latest deployment

**Via CLI:**
```bash
vercel --prod
```

### 5.3 Monitor Build Process

1. Go to **Deployments** tab in Vercel dashboard
2. Click on the latest deployment
3. Watch **Build Logs** for errors
4. Build typically takes 2-5 minutes

## Step 6: Configure Twilio Webhooks

### 6.1 Get Your Vercel URL

After deployment, your webhook URLs will be:
- **Voice Webhook:** `https://[your-project].vercel.app/webhooks/twilio/voice`
- **Status Callback:** `https://[your-project].vercel.app/webhooks/twilio/status`

### 6.2 Configure in Twilio Console

1. **Go to Twilio Console**
   - Visit https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
   - Click on your phone number: `+19472432891`

2. **Set Voice Webhook**
   - Scroll to **"Voice & Fax"** section
   - Set **Voice & Fax webhook URL** to:
     ```
     https://[your-project].vercel.app/webhooks/twilio/voice
     ```
   - Set **HTTP Method** to: `POST`

3. **Set Status Callback**
   - Scroll to **"Status Callback"** section
   - Set **Status Callback URL** to:
     ```
     https://[your-project].vercel.app/webhooks/twilio/status
     ```
   - Set **HTTP Method** to: `POST`

4. **Save Configuration**
   - Click **"Save"** at the bottom

### 6.3 Test Webhooks

You can also use the automated script:

```bash
# Update .env with your Vercel URL first
TWILIO_WEBHOOK_URL=https://[your-project].vercel.app

# Run the configuration script
python scripts/configure_twilio_webhooks.py
```

## Step 7: Post-Deployment Verification

### 7.1 Check Build Success

1. **Build Logs**
   - Go to Vercel Dashboard → **Deployments**
   - Click latest deployment
   - Verify **Build Logs** show "Build Completed"

2. **Common Build Issues:**
   - ❌ "Module not found" → Check `requirements.txt` dependencies
   - ❌ "Environment variable not found" → Verify all env vars are set
   - ❌ "Import error" → Check Python path in `api/index.py`

### 7.2 Test Production URL

1. **Visit Your Live URL**
   - Open `https://[your-project].vercel.app`
   - Should see API root response

2. **Test API Endpoints**
   - Health check: `https://[your-project].vercel.app/health`
   - API docs: `https://[your-project].vercel.app/docs`
   - Webhook test: `https://[your-project].vercel.app/webhooks/twilio/status`

### 7.3 Test Webhooks

1. **Make a Test Call**
   - Call your Twilio number: `+19472432891`
   - Check Vercel function logs for webhook requests
   - Verify call is processed correctly

2. **Check Vercel Logs**
   - Go to Vercel Dashboard → **Functions** tab
   - View real-time logs for webhook requests
   - Check for any errors

### 7.4 Verify Environment Variables

1. Go to Vercel → **Settings** → **Environment Variables**
2. Verify all required variables are set:
   - ✅ `TWILIO_ACCOUNT_SID`
   - ✅ `TWILIO_AUTH_TOKEN`
   - ✅ `TWILIO_PHONE_NUMBER`
   - ✅ `TWILIO_WEBHOOK_URL` (should be your Vercel URL)
   - ✅ `OPENAI_API_KEY`
   - ✅ `OPENAI_MODEL`
   - ✅ `DATABASE_URL`
   - ✅ `SECRET_KEY`
   - ✅ `JWT_SECRET_KEY`

## Troubleshooting

### Build Fails

**Error: "Module not found"**
- **Solution:** Verify all dependencies in `requirements.txt` are correct
- **Solution:** Check Python version (should be 3.11)
- **Solution:** Review build logs for specific missing module

**Error: "Import error"**
- **Solution:** Verify `api/index.py` has correct import path
- **Solution:** Check that `sys.path` is set correctly in `api/index.py`
- **Solution:** Ensure project structure matches expected layout

**Error: "Environment variable not found"**
- **Solution:** Verify all env vars are set in Vercel dashboard
- **Solution:** Check variable names match exactly (case-sensitive)
- **Solution:** Ensure variables are set for correct environment (Production/Preview)

### Runtime Errors

**Error: "Webhook not receiving requests"**
- **Solution:** Verify webhook URL in Twilio Console matches Vercel URL
- **Solution:** Check Vercel function logs for incoming requests
- **Solution:** Test webhook URL directly in browser (should return 405 Method Not Allowed for GET)

**Error: "Database connection failed"**
- **Solution:** Verify `DATABASE_URL` is correct
- **Solution:** Check database allows connections from Vercel IPs
- **Solution:** Use connection pooling for better performance

**Error: "Function timeout"**
- **Solution:** Vercel has a 10-second timeout for free tier
- **Solution:** Optimize webhook handler to respond quickly
- **Solution:** Consider upgrading to Pro tier for longer timeouts

### Webhook Issues

**Error: "405 Method Not Allowed"**
- **Solution:** Verify Twilio is sending POST requests
- **Solution:** Check route configuration in `vercel.json`

**Error: "Webhook validation failed"**
- **Solution:** Implement Twilio request validation (optional but recommended)
- **Solution:** Check webhook signature in request headers

## Key Concepts & Best Practices

### Vercel Serverless Functions

**How it works:**
- Vercel converts your FastAPI app into serverless functions
- Each request triggers a new function instance
- Functions have a 10-second timeout (free tier)

**Best Practices:**
- ✅ Keep webhook handlers fast (< 5 seconds)
- ✅ Use async/await for I/O operations
- ✅ Initialize database connections efficiently
- ✅ Use connection pooling for databases

### Environment Variable Management

**Local Development:**
- Use `.env` file (git-ignored)
- Contains local configuration

**Production (Vercel):**
- Set in Vercel Dashboard → Settings → Environment Variables
- Contains production configuration
- `TWILIO_WEBHOOK_URL` = `https://[project].vercel.app`

**Best Practices:**
- ✅ Never commit `.env` to Git
- ✅ Use same secrets for local and production (where applicable)
- ✅ Set variables for all environments (Production, Preview, Development)
- ✅ Update `TWILIO_WEBHOOK_URL` after first deployment

### Deployment Workflow

**Recommended Flow:**

1. **Develop Locally**
   - Test with local server
   - Verify webhooks work with ngrok

2. **Push to GitHub**
   - Commit and push changes
   - Vercel automatically detects changes

3. **Vercel Auto-Deploys**
   - Builds application
   - Uses production environment variables
   - Deploys to production URL

4. **Update Webhooks**
   - Update Twilio webhook URLs to Vercel URL
   - Test with actual calls

### Security Considerations

1. **Never Commit Secrets**
   - `.env` is git-ignored
   - Use Vercel environment variables for production

2. **Webhook Security**
   - Implement Twilio request validation (optional)
   - Use HTTPS (Vercel provides automatically)
   - Monitor webhook logs for suspicious activity

3. **Database Security**
   - Use connection strings with strong passwords
   - Enable SSL/TLS for database connections
   - Restrict database access to Vercel IPs if possible

4. **API Keys**
   - Rotate API keys periodically
   - Use different keys for development and production
   - Monitor API usage for anomalies

## Summary Checklist

### Vercel Setup
- [ ] Created `vercel.json` configuration
- [ ] Created `api/index.py` entry point
- [ ] Linked GitHub repository to Vercel
- [ ] Completed first deployment
- [ ] Noted production URL

### Environment Variables
- [ ] Added `TWILIO_ACCOUNT_SID`
- [ ] Added `TWILIO_AUTH_TOKEN`
- [ ] Added `TWILIO_PHONE_NUMBER`
- [ ] Added `TWILIO_WEBHOOK_URL` (Vercel URL)
- [ ] Added `OPENAI_API_KEY`
- [ ] Added `OPENAI_MODEL`
- [ ] Added `DATABASE_URL`
- [ ] Added `SECRET_KEY`
- [ ] Added `JWT_SECRET_KEY`
- [ ] Set variables for Production, Preview, Development

### Deployment
- [ ] Pushed code to GitHub
- [ ] Verified build succeeds in Vercel
- [ ] Tested production URL
- [ ] Verified API endpoints work

### Webhook Configuration
- [ ] Updated `TWILIO_WEBHOOK_URL` to Vercel URL
- [ ] Configured webhooks in Twilio Console
- [ ] Tested webhook with actual call
- [ ] Verified webhook logs in Vercel

### Post-Deployment
- [ ] Checked build logs for errors
- [ ] Tested key functionality
- [ ] Verified webhook receives requests
- [ ] Confirmed environment variables are set

---

## Quick Reference: Webhook URLs

**After Vercel Deployment:**

- **Voice Webhook:**
  ```
  https://[your-project].vercel.app/webhooks/twilio/voice
  ```

- **Status Callback:**
  ```
  https://[your-project].vercel.app/webhooks/twilio/status
  ```

**Replace:**
- `[your-project]` → Your Vercel project name (e.g., `ai-caller`)

---

**Last Updated:** Based on FastAPI + Vercel deployment configuration
**Framework:** FastAPI + Python 3.11 + Vercel Serverless Functions

