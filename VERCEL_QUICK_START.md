# Vercel Deployment Quick Start

## 🚀 Fast Setup (5 minutes)

### Step 1: Push to GitHub

```bash
git add vercel.json api/index.py VERCEL_DEPLOYMENT_GUIDE.md
git commit -m "Add Vercel deployment configuration"
git push origin main
```

### Step 2: Deploy to Vercel

**Option A: Via Dashboard (Recommended)**
1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Click "Deploy" (we'll add env vars after)

**Option B: Via CLI**
```bash
./scripts/setup_vercel.sh
```

### Step 3: Set Environment Variables

After first deployment, go to Vercel Dashboard → Settings → Environment Variables

**Required Variables:**
```bash
TWILIO_ACCOUNT_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
TWILIO_WEBHOOK_URL=https://[your-project].vercel.app  # Update after deployment
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-realtime-preview
DATABASE_URL=[your-database-url]
SECRET_KEY=[generate-with: openssl rand -base64 32]
JWT_SECRET_KEY=[generate-with: openssl rand -base64 32]
```

### Step 4: Update Webhook URL

1. After deployment, copy your Vercel URL (e.g., `https://ai-caller.vercel.app`)
2. Update `TWILIO_WEBHOOK_URL` in Vercel environment variables
3. Redeploy or wait for auto-deploy

### Step 5: Configure Twilio Webhooks

**Automated:**
```bash
# Update .env with Vercel URL
TWILIO_WEBHOOK_URL=https://[your-project].vercel.app

# Run configuration script
python scripts/configure_twilio_webhooks.py
```

**Manual:**
1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on `+19472432891`
3. Set Voice webhook: `https://[your-project].vercel.app/webhooks/twilio/voice`
4. Set Status callback: `https://[your-project].vercel.app/webhooks/twilio/status`
5. Save

### Step 6: Test

1. Call your Twilio number: `+19472432891`
2. Check Vercel function logs
3. Verify webhook is received

## 📋 Checklist

- [ ] Code pushed to GitHub
- [ ] Vercel project created
- [ ] First deployment successful
- [ ] Environment variables set
- [ ] TWILIO_WEBHOOK_URL updated to Vercel URL
- [ ] Twilio webhooks configured
- [ ] Test call successful

## 🔗 Your Webhook URLs

After deployment, your webhooks will be at:

- **Voice:** `https://[your-project].vercel.app/webhooks/twilio/voice`
- **Status:** `https://[your-project].vercel.app/webhooks/twilio/status`

## 📚 Full Documentation

See `VERCEL_DEPLOYMENT_GUIDE.md` for complete instructions.

