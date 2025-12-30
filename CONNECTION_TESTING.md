# Connection Testing Guide

This document outlines how to test all connections before deploying to Neon/Vercel.

## Pre-Deployment Testing Checklist

### 1. Database Connection (Local)

Test database connection locally first:

```bash
# Set DATABASE_URL in .env or export
export DATABASE_URL="postgresql://user:password@host.neon.tech:5432/dbname?sslmode=require"

# Or use SQLite for local testing (default if DATABASE_URL not set)
# No setup needed - will create ai_caller.db automatically

# Test database initialization
python -c "from src.database.database import init_db; init_db(); print('Database initialized')"
```

### 2. API Endpoints Testing

Test all API endpoints locally:

```bash
# Start the server
uvicorn src.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/
curl http://localhost:8000/api/tasks/
curl http://localhost:8000/api/calendar/status
curl http://localhost:8000/api/settings/godfather
```

### 3. Database Persistence Test

Verify tasks are being stored in database:

```bash
# Create a task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"task": "Test task", "context": {}}'

# List tasks (should show the created task)
curl http://localhost:8000/api/tasks/

# Get specific task (use task_id from previous response)
curl http://localhost:8000/api/tasks/{task_id}
```

### 4. Frontend Connection Test

Test frontend can connect to API:

```bash
# In frontend directory
cd frontend
npm run dev

# Open browser to http://localhost:5173
# Check browser console for API connection errors
# Test creating a task from the UI
```

### 5. Environment Variables Check

Verify all required environment variables are set:

```python
# Run this script to check
python -c "
from src.utils.config import get_settings
settings = get_settings()
required = ['OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
missing = [k for k in required if not getattr(settings, k, None)]
if missing:
    print(f'Missing: {missing}')
else:
    print('All required variables present')
"
```

### 6. Vercel Function Test (Local)

Test the Vercel entry point locally:

```bash
# Install vercel CLI
npm i -g vercel

# Test locally
vercel dev
```

## Post-Deployment Testing

After deploying to Vercel:

### 1. Health Check

```bash
curl https://your-domain.vercel.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "AI Voice Assistant",
  "settings_loaded": true
}
```

### 2. API Endpoints

```bash
# Root
curl https://your-domain.vercel.app/

# Tasks
curl https://your-domain.vercel.app/api/tasks/

# Calendar
curl https://your-domain.vercel.app/api/calendar/status

# Settings
curl https://your-domain.vercel.app/api/settings/godfather
```

### 3. Database Connection

Create a task and verify it persists:

```bash
# Create task
curl -X POST https://your-domain.vercel.app/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"task": "Test deployment task"}'

# Verify it's stored (should return the task)
curl https://your-domain.vercel.app/api/tasks/
```

### 4. Frontend

1. Visit `https://your-domain.vercel.app`
2. Check browser console for errors
3. Test creating a task
4. Verify tasks persist after page refresh

### 5. Twilio Webhook (if configured)

Test Twilio webhook endpoint:

```bash
# This should return TwiML
curl -X POST https://your-domain.vercel.app/webhooks/twilio/voice \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=test&From=+1234567890&To=+0987654321"
```

## Common Issues and Solutions

### Database Connection Fails

**Issue**: `psycopg2.OperationalError` or connection timeout

**Solutions**:
- Verify `DATABASE_URL` format is correct
- Ensure `?sslmode=require` is at the end
- Check Neon dashboard for connection limits
- Verify IP allowlist in Neon (if enabled)

### Tasks Not Persisting

**Issue**: Tasks disappear after server restart

**Solutions**:
- Verify `DATABASE_URL` is set in Vercel environment variables
- Check database logs in Neon dashboard
- Verify tables exist: `SELECT * FROM tasks LIMIT 1;`

### API Routes Return 404

**Issue**: Routes not found in Vercel

**Solutions**:
- Verify `vercel.json` routing configuration
- Check that all routers are included in `api/index.py`
- Review Vercel function logs

### Frontend Can't Connect to API

**Issue**: CORS errors or connection refused

**Solutions**:
- Verify `CORS_ORIGINS` includes your Vercel domain
- Check `VITE_API_URL` is set correctly
- Verify frontend is using relative URLs in production

### Import Errors in Vercel

**Issue**: Module not found errors

**Solutions**:
- Verify all dependencies in `api/requirements.txt`
- Check that `src/` directory structure is correct
- Review Vercel build logs for missing modules

## Testing Script

Create a test script `test_connections.py`:

```python
"""Test all connections"""
import os
import sys
import requests

def test_database():
    """Test database connection"""
    try:
        from src.database.database import get_db, init_db
        init_db()
        db = next(get_db())
        # Try a simple query
        db.execute("SELECT 1")
        print("✓ Database connection: OK")
        return True
    except Exception as e:
        print(f"✗ Database connection: FAILED - {e}")
        return False

def test_api(base_url="http://localhost:8000"):
    """Test API endpoints"""
    endpoints = [
        "/health",
        "/",
        "/api/tasks/",
        "/api/calendar/status",
        "/api/settings/godfather",
    ]
    
    all_ok = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code < 500:
                print(f"✓ {endpoint}: OK ({response.status_code})")
            else:
                print(f"✗ {endpoint}: ERROR ({response.status_code})")
                all_ok = False
        except Exception as e:
            print(f"✗ {endpoint}: FAILED - {e}")
            all_ok = False
    
    return all_ok

def test_env_vars():
    """Test required environment variables"""
    from src.utils.config import get_settings
    settings = get_settings()
    
    required = ['OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN']
    missing = [k for k in required if not getattr(settings, k, None)]
    
    if missing:
        print(f"✗ Missing environment variables: {missing}")
        return False
    else:
        print("✓ Environment variables: OK")
        return True

if __name__ == "__main__":
    print("Testing connections...\n")
    
    env_ok = test_env_vars()
    db_ok = test_database()
    api_ok = test_api()
    
    print("\n" + "="*50)
    if all([env_ok, db_ok, api_ok]):
        print("✓ All connections successful!")
        sys.exit(0)
    else:
        print("✗ Some connections failed")
        sys.exit(1)
```

Run with:
```bash
python test_connections.py
```

