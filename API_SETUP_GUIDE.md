# API Setup Guide for Twilio and OpenAI

This guide will help you set up and test your Twilio and OpenAI API credentials for full functional testing.

## Prerequisites

1. **OpenAI Account**: Sign up at https://platform.openai.com/
2. **Twilio Account**: Sign up at https://www.twilio.com/try-twilio
3. **Python 3.11+** installed
4. **Dependencies installed**: `pip install -r requirements.txt`

## Step 1: Get Your API Credentials

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Give it a name (e.g., "AI Caller Development")
4. Copy the key immediately (it starts with `sk-`)
5. ⚠️ **Important**: You won't be able to see it again, so save it securely

### Twilio Credentials

1. Go to https://console.twilio.com/
2. Your **Account SID** is visible on the dashboard (starts with `AC`)
3. Click "Show" next to Auth Token to reveal your **Auth Token**
4. Go to Phone Numbers → Manage → Active numbers
5. Note your **Phone Number** (format: +1234567890)
6. If you don't have a number, purchase one:
   - Go to Phone Numbers → Buy a number
   - Select your country and requirements
   - Complete the purchase

## Step 2: Create Environment File

1. Create a `.env` file in the project root:

```bash
cp .env.example .env  # If .env.example exists
# OR create .env manually
```

2. Add your credentials to `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_REALTIME_API_URL=wss://api.openai.com/v1/realtime

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-actual-twilio-auth-token-here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:8000

# Database (required)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_caller

# Redis (required)
REDIS_URL=redis://localhost:6379/0

# Security (generate random strings)
SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-random-jwt-secret-key-here
```

## Step 3: Test Your API Connections

### Option 1: Using the Setup Script (Recommended)

Run the automated test script:

```bash
# Make script executable (Unix/Mac)
chmod +x scripts/setup_apis.py

# Run the script
python scripts/setup_apis.py
```

The script will:
- ✅ Test OpenAI API connection
- ✅ Test Twilio API connection
- ✅ Verify your phone number
- ✅ Provide helpful error messages if something fails

### Option 2: Using the API Endpoint

If the backend is running, you can test via the API:

```bash
# Start the backend
uvicorn src.main:app --reload

# In another terminal, test the connection
curl -X POST http://localhost:8000/api/v1/config/test-connection \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "openai_api_key": "sk-your-key",
    "twilio_account_sid": "ACxxxxx",
    "twilio_auth_token": "your-token",
    "twilio_phone_number": "+1234567890"
  }'
```

### Option 3: Manual Python Test

Create a quick test script:

```python
from openai import OpenAI
from twilio.rest import Client as TwilioClient

# Test OpenAI
openai_client = OpenAI(api_key="sk-your-key")
models = openai_client.models.list()
print(f"OpenAI: ✅ Connected ({len(list(models))} models available)")

# Test Twilio
twilio_client = TwilioClient("ACxxxxx", "your-token")
account = twilio_client.api.accounts("ACxxxxx").fetch()
print(f"Twilio: ✅ Connected (Account: {account.friendly_name})")
```

## Step 4: Verify Webhook Configuration (For Production)

For local testing, you'll need to expose your local server to the internet:

### Using ngrok (Recommended for Testing)

1. Install ngrok: https://ngrok.com/download
2. Start your backend server:
   ```bash
   uvicorn src.main:app --reload
   ```
3. In another terminal, expose port 8000:
   ```bash
   ngrok http 8000
   ```
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. Update your `.env`:
   ```bash
   TWILIO_WEBHOOK_URL=https://abc123.ngrok.io
   ```
6. Configure Twilio webhook:
   - Go to Twilio Console → Phone Numbers → Your Number
   - Set Voice & Fax webhook URL to: `https://abc123.ngrok.io/webhooks/twilio/voice`
   - Set Status Callback URL to: `https://abc123.ngrok.io/webhooks/twilio/status`

## Step 5: Test a Real Call (Optional)

Once everything is configured, you can test making a call:

```bash
# Using the API
curl -X POST http://localhost:8000/api/v1/calls/initiate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "to_number": "+1234567890",
    "business_config_id": "your-config-id"
  }'
```

## Troubleshooting

### OpenAI API Issues

**Error: "Invalid API key"**
- Verify your API key starts with `sk-`
- Check that you copied the entire key
- Ensure there are no extra spaces in your `.env` file
- Verify your OpenAI account has credits/billing set up

**Error: "Rate limit exceeded"**
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Check your usage at https://platform.openai.com/usage

**Error: "Model not found"**
- Verify `OPENAI_MODEL` is set to a valid model (e.g., `gpt-4o`, `gpt-4o-mini`)
- Check model availability at https://platform.openai.com/docs/models

### Twilio API Issues

**Error: "401 Unauthorized"**
- Verify your Account SID and Auth Token are correct
- Check for typos in your `.env` file
- Ensure you're using the correct credentials from the Twilio Console

**Error: "Phone number not found"**
- Verify your phone number format: `+1234567890` (with country code)
- Check that the number is active in your Twilio account
- Go to Phone Numbers → Manage → Active numbers to verify

**Error: "Webhook URL not accessible"**
- For local testing, use ngrok or similar tunneling service
- Ensure your backend server is running
- Verify the webhook URL is accessible from the internet
- Check firewall settings

### General Issues

**Error: "Module not found"**
- Install dependencies: `pip install -r requirements.txt`
- Activate your virtual environment

**Error: "Database connection failed"**
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` is correct
- Check database exists: `createdb ai_caller`

**Error: "Redis connection failed"**
- Ensure Redis is running: `redis-server`
- Verify `REDIS_URL` is correct
- Test connection: `redis-cli ping` (should return `PONG`)

## Next Steps

Once your APIs are configured and tested:

1. ✅ Run database migrations: `alembic upgrade head`
2. ✅ Start the backend: `uvicorn src.main:app --reload`
3. ✅ Start the frontend: `cd frontend && npm run dev`
4. ✅ Access the setup wizard at http://localhost:3000
5. ✅ Complete the business configuration
6. ✅ Test making a call!

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use different API keys** for development and production
3. **Rotate API keys** regularly
4. **Use environment variables** in production (not `.env` files)
5. **Restrict API key permissions** when possible
6. **Monitor API usage** to detect unauthorized access

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Twilio Voice API Documentation](https://www.twilio.com/docs/voice)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Project README](./README.md)
- [Environment Variables Reference](./ENVIRONMENT_VARIABLES.md)

## Support

If you encounter issues not covered in this guide:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review error logs in the console
3. Verify all environment variables are set correctly
4. Test each API individually using the manual test methods

