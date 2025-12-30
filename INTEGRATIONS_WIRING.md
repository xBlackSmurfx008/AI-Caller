# Integration Wiring and Connection Status

## Overview
This document describes how all integrations are wired together and how to verify their connections.

## Integration Architecture

### Core Integrations
1. **Database** (PostgreSQL/SQLite) - Core data storage
2. **OpenAI** - AI/LLM services
3. **Twilio** - Voice calls, SMS/MMS/WhatsApp
4. **Google Calendar** - Calendar events (OAuth required)
5. **SMTP** - Email sending

### Service Layer
Services are organized in a dependency hierarchy:

```
Database
  ├── MemoryService (OpenAI + Database)
  ├── OrchestratorService (OpenAI + Database)
  └── MessagingService (Twilio + MemoryService)
        └── VoiceAssistant (OpenAI + OrchestratorService)
              └── RealtimeCallBridge (VoiceAssistant)
```

## Integration Manager

### Location
- `src/integrations/manager.py` - Main integration manager
- `src/integrations/connections.py` - Connection verification
- `src/integrations/retry.py` - Retry utilities

### Initialization
The integration manager is automatically initialized in:
- `src/main.py` (main FastAPI app)
- `api/index.py` (Vercel serverless)

### Features
1. **Centralized Initialization** - All integrations verified at startup
2. **Connection Verification** - Each integration tested with retry logic
3. **Status Tracking** - Real-time status for monitoring
4. **Health Checks** - API endpoints for status monitoring
5. **Graceful Degradation** - App continues even if optional integrations fail

## Service Registry

### Location
- `src/services/registry.py` - Service instance management

### Purpose
Ensures services are properly initialized in dependency order and shared as singletons.

### Services Registered
1. **TwilioService** - No dependencies
2. **MemoryService** - Depends on OpenAI, Database
3. **OrchestratorService** - Depends on OpenAI, Database
4. **MessagingService** - Depends on TwilioService, MemoryService
5. **VoiceAssistant** - Depends on OpenAI, OrchestratorService
6. **RealtimeCallBridge** - Depends on VoiceAssistant

## Integration Dependencies

### Twilio Integration
- **Used by**: `TwilioService`, `MessagingService`, `tools.py`
- **Configuration**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- **Webhooks**: `/webhooks/twilio/voice`, `/webhooks/twilio/inbound-message`
- **Status**: Verified at startup, connection tested

### OpenAI Integration
- **Used by**: `VoiceAssistant`, `MemoryService`, `OrchestratorService`
- **Configuration**: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_REALTIME_API_URL`
- **Status**: Client initialized at startup

### Database Integration
- **Used by**: All services that store data
- **Configuration**: `DATABASE_URL` (optional, falls back to SQLite)
- **Status**: Connection tested with retry logic

### Google Calendar Integration
- **Used by**: `tools.py`, `scheduler.py`, `calendar.py` routes
- **Configuration**: `GOOGLE_OAUTH_CLIENT_SECRETS_FILE` or `GOOGLE_OAUTH_CLIENT_SECRETS_JSON`
- **Status**: OAuth token checked (requires user authentication)
- **Note**: Optional integration, app works without it

### SMTP Integration
- **Used by**: `tools.py` (send_email function)
- **Configuration**: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`
- **Status**: Configuration verified (no actual connection test)
- **Note**: Optional integration, app works without it

## Connection Verification

### Health Check Endpoints

#### Basic Health
```
GET /api/health
```
Returns basic service status.

#### Integration Health
```
GET /api/health/integrations
```
Returns detailed status for all integrations.

#### Connection Health
```
GET /api/health/connections
```
Returns detailed connection status including:
- Integration status
- Service connection status
- Dependency verification

#### Connection Summary
```
GET /api/health/connections/summary
```
Returns summary of all connections.

### Verification Flow

1. **Startup**:
   - Integration manager initializes all integrations
   - Service registry initializes all services
   - Connections verified

2. **Runtime**:
   - Services use registered integrations
   - Health endpoints provide real-time status
   - Errors logged and tracked

3. **Monitoring**:
   - Use `/api/health/connections` for detailed status
   - Use `/api/health/integrations` for integration status
   - Check logs for connection errors

## Service Wiring

### TwilioService
```python
from src.telephony.twilio_client import TwilioService
service = TwilioService()  # Uses settings.TWILIO_*
```

### MessagingService
```python
from src.messaging.messaging_service import MessagingService
service = MessagingService()  # Uses TwilioService + MemoryService
```

### MemoryService
```python
from src.memory.memory_service import MemoryService
service = MemoryService()  # Uses OpenAI + Database
```

### VoiceAssistant
```python
from src.agent.assistant import VoiceAssistant
service = VoiceAssistant()  # Uses OpenAI + OrchestratorService
```

### OrchestratorService
```python
from src.orchestrator.orchestrator_service import OrchestratorService
service = OrchestratorService()  # Uses OpenAI + Database
```

## Integration Status Values

- `not_initialized` - Integration not yet checked
- `initializing` - Currently being verified
- `connected` - Successfully connected and verified
- `disconnected` - Configuration present but not authenticated (e.g., Google Calendar OAuth)
- `not_configured` - Required configuration missing
- `error` - Connection failed after retries

## Troubleshooting

### Integration Not Connecting

1. **Check Configuration**:
   - Verify environment variables are set
   - Check `.env` file or environment

2. **Check Logs**:
   - Look for integration initialization errors
   - Check connection retry attempts

3. **Verify Health Endpoints**:
   - Call `/api/health/integrations` to see status
   - Call `/api/health/connections` for detailed info

4. **Test Individual Integration**:
   - Call `/api/health/integrations/{name}` for specific status

### Service Not Working

1. **Check Dependencies**:
   - Verify required integrations are connected
   - Check `/api/health/connections` for dependency status

2. **Check Service Initialization**:
   - Verify service registry initialized
   - Check service-specific logs

3. **Verify Integration Access**:
   - Ensure service can access required integrations
   - Check for permission/authentication issues

## Next Steps

1. **Monitor Integration Health**: Use health endpoints regularly
2. **Configure Missing Services**: Set environment variables for `not_configured` services
3. **Complete OAuth**: For Google Calendar, complete OAuth flow via `/api/calendar/oauth/start`
4. **Test Connections**: Use health endpoints to verify all connections

## Files Modified

- `src/integrations/manager.py` - Integration manager (existing)
- `src/integrations/connections.py` - Connection verification (new)
- `src/services/registry.py` - Service registry (new)
- `src/main.py` - Service registry initialization (updated)
- `api/index.py` - Service registry initialization (updated)
- `src/api/routes/health.py` - Connection health endpoints (updated)

