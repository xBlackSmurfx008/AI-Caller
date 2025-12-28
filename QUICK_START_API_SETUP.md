# Quick Start: API Setup

## 🚀 Fast Setup (5 minutes)

### 1. Get Your API Keys

**OpenAI:**
- Visit: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key (starts with `sk-`)

**Twilio:**
- Visit: https://console.twilio.com/
- Copy Account SID (starts with `AC`)
- Show and copy Auth Token
- Note your Phone Number from Phone Numbers section

### 2. Create .env File

Create a `.env` file in the project root with:

```bash
# Required - OpenAI
OPENAI_API_KEY=sk-your-key-here

# Required - Twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token-here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=http://localhost:8000

# Required - Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_caller
REDIS_URL=redis://localhost:6379/0

# Required - Security (generate random strings)
SECRET_KEY=change-me-generate-random-string
JWT_SECRET_KEY=change-me-generate-random-string
```

### 3. Test Your Setup

```bash
# Activate virtual environment (if using one)
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Run the test script
python scripts/setup_apis.py
```

### 4. Expected Output

```
🚀 AI Caller - API Setup & Test Script
============================================================

🔍 Testing OpenAI API...
  → Testing model list access...
  → Testing API completion...
  ✅ OpenAI API connection successful!
     - Available models: 50+
     - Test response: API test successful

🔍 Testing Twilio API...
  → Testing account access...
  → Fetching phone numbers...
  ✅ Twilio API connection successful!
     - Account Name: Your Account Name
     - Account Status: active
     - Phone Numbers Found: 1

============================================================
📊 Test Summary
============================================================
OpenAI API:  ✅ PASS
Twilio API:  ✅ PASS

🎉 All API tests passed! You're ready to use AI Caller.
```

## ❌ Troubleshooting Quick Fixes

**"OpenAI API key not configured"**
→ Check `.env` file exists and `OPENAI_API_KEY` is set correctly

**"Twilio 401 Unauthorized"**
→ Verify Account SID and Auth Token are correct (no extra spaces)

**"Module not found"**
→ Run: `pip install -r requirements.txt`

**"Python not found"**
→ Activate virtual environment: `source venv/bin/activate`

## 📚 Full Documentation

See [API_SETUP_GUIDE.md](./API_SETUP_GUIDE.md) for detailed instructions.

