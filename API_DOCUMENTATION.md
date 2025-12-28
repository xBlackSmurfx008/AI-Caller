# API Documentation

Complete API reference for the AI Caller system.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/login
Login and get access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /auth/forgot-password
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### POST /auth/reset-password
Reset password with token.

**Request:**
```json
{
  "token": "reset-token",
  "new_password": "newpassword"
}
```

### Configuration

#### POST /config/test-connection
Test API credentials without saving.

**Request:**
```json
{
  "openai_api_key": "sk-...",
  "twilio_account_sid": "AC...",
  "twilio_auth_token": "...",
  "twilio_phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "openai": {
    "connected": true,
    "error": null
  },
  "twilio": {
    "connected": true,
    "error": null
  },
  "success": true
}
```

#### GET /config/business
List business configurations.

#### POST /config/business
Create business configuration.

#### GET /config/business/{id}
Get business configuration.

#### PUT /config/business/{id}
Update business configuration.

#### DELETE /config/business/{id}
Delete business configuration.

#### GET /config/business/{id}/usage
Check if business config is in use.

### Setup

#### POST /setup/complete
Complete setup wizard.

**Request:**
```json
{
  "business_config": {
    "name": "Business Name",
    "type": "customer_support",
    "config_data": {}
  },
  "agents": [],
  "knowledge_base": [],
  "api_config": {}
}
```

### Calls

#### GET /calls
List calls with filtering and pagination.

**Query Parameters:**
- `status`: Filter by status
- `direction`: Filter by direction
- `business_id`: Filter by business
- `from_date`: Start date (ISO format)
- `to_date`: End date (ISO format)
- `page`: Page number
- `limit`: Items per page

#### GET /calls/{call_id}
Get call details.

#### POST /calls/initiate
Initiate outbound call.

#### POST /calls/{call_id}/escalate
Escalate call to human agent.

#### POST /calls/{call_id}/end
End a call.

#### GET /calls/{call_id}/notes
List call notes.

#### POST /calls/{call_id}/notes
Add note to call.

**Request:**
```json
{
  "note": "Note text",
  "category": "Follow-up",
  "tags": ["important"]
}
```

#### PUT /calls/{call_id}/notes/{note_id}
Update call note.

#### DELETE /calls/{call_id}/notes/{note_id}
Delete call note.

### Agents

#### GET /agents
List agents.

#### POST /agents
Create agent.

#### GET /agents/{id}
Get agent.

#### PUT /agents/{id}
Update agent.

#### DELETE /agents/{id}
Delete agent.

#### GET /agents/{id}/usage
Check agent usage before deletion.

**Response:**
```json
{
  "agent_id": "uuid",
  "is_in_use": false,
  "active_escalations": 0,
  "active_calls": 0,
  "total_escalations": 0,
  "total_calls": 0
}
```

### Notifications

#### GET /notifications
List notifications.

**Query Parameters:**
- `unread_only`: Filter unread only
- `type`: Filter by type

#### GET /notifications/unread-count
Get unread notification count.

#### PATCH /notifications/{id}/read
Mark notification as read.

#### PATCH /notifications/read-all
Mark all notifications as read.

#### DELETE /notifications/{id}
Delete notification.

### Analytics

#### GET /analytics/dashboard
Get dashboard overview.

#### GET /analytics/call-volume
Get call volume statistics.

#### GET /analytics/qa-stats
Get QA statistics.

#### GET /analytics/export
Export analytics data (CSV/PDF).

## WebSocket Events

Connect to: `ws://localhost:8000/ws/calls?token=<jwt-token>`

### Events Emitted

- `call.started`: New call started
- `call.updated`: Call updated
- `call.ended`: Call ended
- `interaction.added`: New interaction added
- `qa.score.updated`: QA score updated
- `sentiment.changed`: Sentiment changed
- `escalation.triggered`: Call escalated
- `escalation.completed`: Escalation completed
- `notification.created`: New notification created

### Subscribe to Events

```javascript
socket.emit('subscribe', { type: 'all_calls' });
socket.emit('subscribe', { type: 'call', call_id: 'call-id' });
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

Common status codes:
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

