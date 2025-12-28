# Twilio Webhook Configuration Guide

## Quick Setup

### Option 1: Comprehensive Trial Setup (Recommended for First-Time Setup)

For complete Twilio trial number setup, use the comprehensive setup script:

```bash
source venv/bin/activate
python scripts/setup_twilio_trial.py
```

This script will:
- ✅ Validate your Twilio credentials
- ✅ Get/verify your phone number
- ✅ Configure all webhooks (voice, status)
- ✅ Validate webhook endpoints
- ✅ Verify complete configuration
- ✅ Provide detailed setup summary

### Option 2: Quick Webhook Configuration Only

If you just need to update webhooks:

```bash
source venv/bin/activate
python scripts/configure_twilio_webhooks.py
```

### Option 2: Manual Configuration

1. **Get a public URL for local development:**
   
   For local testing, you need to expose your local server. Use one of these:

   **Using ngrok (Recommended):**
   ```bash
   # Install ngrok: https://ngrok.com/download
   ngrok http 8000
   # Copy the https URL (e.g., https://abc123.ngrok.io)
   ```

   **Using localtunnel:**
   ```bash
   npm install -g localtunnel
   lt --port 8000
   # Copy the URL provided
   ```

2. **Update .env file:**
   ```bash
   TWILIO_WEBHOOK_URL=https://your-ngrok-url.ngrok.io
   # OR for production:
   TWILIO_WEBHOOK_URL=https://your-domain.com
   ```

3. **Configure in Twilio Console:**
   - Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
   - Click on your phone number: `+19472432891`
   - Scroll to "Voice & Fax" section
   - Set **Voice & Fax webhook URL** to:
     ```
     https://your-url/webhooks/twilio/voice
     ```
   - Set **HTTP Method** to: `POST`
   - Scroll to "Status Callback" section
   - Set **Status Callback URL** to:
     ```
     https://your-url/webhooks/twilio/status
     ```
   - Set **HTTP Method** to: `POST`
   - Click **Save**

## Webhook Endpoints

Your application provides these webhook endpoints:

- **Voice Webhook**: `/webhooks/twilio/voice`
  - Handles incoming calls
  - Returns TwiML instructions
  - URL: `{TWILIO_WEBHOOK_URL}/webhooks/twilio/voice`

- **Status Callback**: `/webhooks/twilio/status`
  - Receives call status updates
  - Updates call status in database
  - URL: `{TWILIO_WEBHOOK_URL}/webhooks/twilio/status`

## Complete Setup Process for Testing

### Step 1: Get Your Twilio Trial Number

If you don't have a phone number yet:

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click "Buy a number"
3. Select a number (FREE for trial accounts)
4. Complete the purchase

### Step 2: Configure Your Environment

1. **Set up your .env file with Twilio credentials:**
   ```bash
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+1234567890
   ```

2. **For local testing, get a public URL:**
   
   **Using ngrok (Recommended):**
   ```bash
   # Install ngrok: https://ngrok.com/download
   ngrok http 8000
   # Copy the https URL (e.g., https://abc123.ngrok.io)
   ```
   
   **Using localtunnel:**
   ```bash
   npm install -g localtunnel
   lt --port 8000
   # Copy the URL provided
   ```

3. **Add webhook URL to .env:**
   ```bash
   TWILIO_WEBHOOK_URL=https://your-ngrok-url.ngrok.io
   ```

### Step 3: Run Comprehensive Setup

Run the comprehensive setup script to configure everything:

```bash
source venv/bin/activate
python scripts/setup_twilio_trial.py
```

This will:
- ✅ Validate your credentials
- ✅ Verify your phone number
- ✅ Configure all webhooks
- ✅ Validate endpoints
- ✅ Show complete configuration summary

### Step 4: Start Your Server

```bash
source venv/bin/activate
uvicorn src.main:app --reload
```

### Step 5: Test Your Setup

1. **Verify webhook endpoints are accessible:**
   - Open: `https://your-ngrok-url.ngrok.io/webhooks/twilio/voice`
   - Should return TwiML or 405 Method Not Allowed (both are OK)

2. **Test by calling your number:**
   - Call your Twilio number from a verified phone number
   - (Trial accounts can only call verified numbers)
   - Check server logs for webhook activity
   - The call should connect and you should hear the AI agent

3. **Verify in Twilio Console:**
   - Go to: https://console.twilio.com/us1/monitor/logs/calls
   - You should see call logs with webhook requests
   - Check that webhooks are returning 200 status codes

## Production Setup

For production, use your actual domain:

```bash
TWILIO_WEBHOOK_URL=https://api.yourdomain.com
```

Then configure webhooks using the script or manually in Twilio Console.

## Troubleshooting

### Webhook Not Receiving Calls

1. **Verify the URL is publicly accessible:**
   - Test in browser: `https://your-url/webhooks/twilio/voice`
   - Should return TwiML or 405 (both are OK)

2. **Check that your server is running:**
   ```bash
   # Verify server is running on port 8000
   curl http://localhost:8000/health
   ```

3. **Verify webhook URL in Twilio Console:**
   - Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
   - Click on your phone number
   - Verify Voice URL matches: `{TWILIO_WEBHOOK_URL}/webhooks/twilio/voice`
   - Verify Status Callback matches: `{TWILIO_WEBHOOK_URL}/webhooks/twilio/status`

4. **Check server logs for incoming webhook requests:**
   - Look for log entries with "twilio_voice_webhook" or "twilio_status_callback"
   - Check for any error messages

### 403 Forbidden When Configuring

- Standard API Keys may not have permission to update webhooks
- **Solution:** Configure manually in Twilio Console (see Step 3 in Complete Setup)

### Webhook Timeout

- Ensure your server responds within 15 seconds
- Check server logs for errors
- Verify database connection is working
- Check that OpenAI API is accessible

### Trial Account Limitations

- **Can only call verified numbers:** Add verified numbers at https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- **Limited credits:** Check your balance at https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- **Some features restricted:** Upgrade to paid account for full features

### Media Stream Not Connecting

- Verify WebSocket endpoint is accessible: `wss://your-url/webhooks/twilio/media/{call_sid}`
- Check that `TWILIO_WEBHOOK_URL` uses `https://` (not `http://`) for WebSocket connections
- Verify OpenAI API key is set correctly
- Check server logs for "media_stream_connected" messages

