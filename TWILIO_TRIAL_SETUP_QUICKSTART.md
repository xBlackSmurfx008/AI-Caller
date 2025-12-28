# Twilio Trial Number Setup - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Prerequisites
- Twilio account (sign up at https://www.twilio.com/try-twilio)
- Trial phone number (get one free at https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
- Python environment with dependencies installed

### Step 1: Configure Environment Variables

Create or update your `.env` file:

```bash
# Twilio Credentials (get from https://console.twilio.com/)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Webhook URL (for local testing, use ngrok - see Step 2)
TWILIO_WEBHOOK_URL=https://your-ngrok-url.ngrok.io
```

### Step 2: Get Public URL (Local Testing Only)

**Option A: ngrok (Recommended)**
```bash
# Install: https://ngrok.com/download
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok.io)
```

**Option B: localtunnel**
```bash
npm install -g localtunnel
lt --port 8000
# Copy the URL provided
```

Update `.env` with the URL:
```bash
TWILIO_WEBHOOK_URL=https://abc123.ngrok.io
```

### Step 3: Run Comprehensive Setup

```bash
source venv/bin/activate
python scripts/setup_twilio_trial.py
```

This script will:
- ✅ Validate your Twilio credentials
- ✅ Verify your phone number exists and has voice capability
- ✅ Configure all webhooks automatically
- ✅ Validate webhook endpoints
- ✅ Show complete configuration summary

### Step 4: Start Your Server

```bash
source venv/bin/activate
uvicorn src.main:app --reload
```

Keep ngrok/localtunnel running in a separate terminal.

### Step 5: Test Your Setup

1. **Verify your phone number is verified** (Trial accounts can only call verified numbers):
   - Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
   - Add your phone number if not already verified

2. **Call your Twilio number** from your verified phone

3. **Check server logs** for:
   - `twilio_voice_webhook` - Call received
   - `media_stream_connected` - Media stream established
   - `bridge_started` - OpenAI bridge connected

## ✅ Verification Checklist

- [ ] Twilio credentials are set in `.env`
- [ ] Phone number is configured in `.env`
- [ ] Webhook URL is set and publicly accessible
- [ ] Setup script ran successfully
- [ ] Server is running
- [ ] ngrok/localtunnel is running (for local testing)
- [ ] Phone number is verified in Twilio Console
- [ ] Can call the number and hear the AI agent

## 🔧 Common Issues

### "No phone numbers found"
- Get a free trial number: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
- Click "Buy a number" and select one (FREE for trial)

### "Webhook not accessible"
- Make sure ngrok/localtunnel is running
- Verify `TWILIO_WEBHOOK_URL` in `.env` matches the ngrok URL
- Test the URL in a browser

### "403 Forbidden" when configuring
- API Keys have limited permissions
- Configure webhooks manually in Twilio Console (script will show instructions)

### "Can only call verified numbers" (Trial Account)
- Add your phone number: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- Verify it via SMS or call

## 📚 Additional Resources

- Full documentation: [TWILIO_WEBHOOK_SETUP.md](./TWILIO_WEBHOOK_SETUP.md)
- Twilio Console: https://console.twilio.com/
- Twilio Trial Guide: https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account

## 🎯 Next Steps

Once setup is complete:
1. Test inbound calls (call your Twilio number)
2. Test outbound calls (use the API)
3. Monitor call logs in Twilio Console
4. Check server logs for webhook activity
5. Upgrade to paid account when ready for production

