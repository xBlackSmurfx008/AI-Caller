# Error Code Reference

**Last Updated**: 2025-01-29  
**Version**: 1.0

Complete reference guide for all error codes, error types, and error handling patterns used in the AI Voice Assistant.

---

## Table of Contents

1. [OpenAI API Errors](#openai-api-errors)
2. [Twilio API Errors](#twilio-api-errors)
3. [Application Errors](#application-errors)
4. [HTTP Status Codes](#http-status-codes)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Troubleshooting](#troubleshooting)

---

## OpenAI API Errors

### Error Types

| Error Type | HTTP Status | Description | Retry? |
|------------|-------------|-------------|--------|
| `RateLimitError` | 429 | Rate limit exceeded | Yes (with backoff) |
| `APIConnectionError` | N/A | Network/connection issue | Yes (with backoff) |
| `APITimeoutError` | N/A | Request timeout | Yes (with backoff) |
| `APIError` (4xx) | 400-499 | Client error | No (except 429) |
| `APIError` (5xx) | 500-599 | Server error | Yes (with backoff) |
| `InvalidRequestError` | 400 | Invalid request parameters | No |

### Common OpenAI Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `invalid_api_key` | Invalid API key | Check `OPENAI_API_KEY` environment variable |
| `rate_limit_exceeded` | Too many requests | Wait and retry with exponential backoff |
| `invalid_request_error` | Invalid request parameters | Check request format and parameters |
| `server_error` | OpenAI server error | Retry with exponential backoff |
| `model_not_found` | Model not available | Check `OPENAI_MODEL` configuration |

### Error Handling

**Location**: `src/utils/openai_client.py`

```python
from openai import RateLimitError, APIConnectionError, APITimeoutError, APIError

# Retry decorator with exponential backoff
@retry_openai_call(max_retries=3)
def call_openai():
    # OpenAI API call
    pass
```

**Retry Strategy**:
- Exponential backoff: 1s, 2s, 4s, 8s...
- Maximum delay: 60 seconds
- Random jitter to prevent thundering herd
- Respects `retry-after` header for rate limits

---

## Twilio API Errors

### Error Code Ranges

| Code Range | Category | Description |
|------------|----------|-------------|
| 20000-20003 | Request Errors | Invalid request parameters |
| 20400-20499 | HTTP Errors | HTTP-related errors |
| 21200-21299 | Phone Number Errors | Invalid phone numbers |
| 21600-21699 | Call Errors | Call-related errors |
| 30000-39999 | Server Errors | Twilio server errors |

### Common Twilio Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `20000` | Invalid URL | Check webhook URL format |
| `20001` | Invalid HTTP method | Use POST for webhooks |
| `20002` | Invalid parameter | Check parameter names and values |
| `20003` | Missing required parameter | Include all required parameters |
| `20404` | Resource not found | Check resource ID exists |
| `20429` | Too many requests | Rate limit exceeded, retry with backoff |
| `21211` | Invalid 'To' phone number | Use E.164 format (+1234567890) |
| `21216` | Invalid 'To' phone number format | Check phone number format |
| `21608` | Invalid 'From' phone number | Use verified Twilio number |
| `21614` | Unsubscribed recipient | Recipient opted out of SMS |
| `30001` | Queue overflow | Too many requests, retry later |
| `30002` | Account suspended | Check Twilio account status |
| `30003` | Unauthorized | Check credentials (Account SID, Auth Token) |

### Error Handling

**Location**: `src/telephony/twilio_client.py`

```python
from twilio.base.exceptions import TwilioException, TwilioRestException

try:
    call = client.calls.create(...)
except TwilioRestException as e:
    # Handle API errors (includes error codes)
    logger.error("twilio_error", code=e.code, message=e.msg)
except TwilioException as e:
    # Handle other Twilio errors
    logger.error("twilio_error", error=str(e))
```

---

## Application Errors

### Task Errors

**Location**: `src/utils/errors.py`

| Error Type | Description | HTTP Status |
|------------|-------------|-------------|
| `TaskError` | General task error | 400 |
| `TaskNotFoundError` | Task not found | 404 |
| `TaskExecutionError` | Task execution failed | 500 |
| `TaskValidationError` | Task validation failed | 400 |

### Database Errors

| Error Type | Description | HTTP Status |
|------------|-------------|-------------|
| `DatabaseError` | Database operation failed | 500 |
| `IntegrityError` | Database constraint violation | 400 |
| `NotFoundError` | Resource not found | 404 |

### Validation Errors

| Error Type | Description | HTTP Status |
|------------|-------------|-------------|
| `ValidationError` | Input validation failed | 400 |
| `MissingFieldError` | Required field missing | 400 |
| `InvalidFormatError` | Invalid data format | 400 |

---

## HTTP Status Codes

### Success Codes

| Code | Description | Usage |
|------|-------------|-------|
| `200` | OK | Successful GET, PUT, PATCH |
| `201` | Created | Successful POST (resource created) |
| `204` | No Content | Successful DELETE |

### Client Error Codes

| Code | Description | Usage |
|------|-------------|-------|
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Authorization failed |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource conflict (e.g., duplicate) |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Description | Usage |
|------|-------------|-------|
| `500` | Internal Server Error | Unexpected server error |
| `502` | Bad Gateway | Upstream service error |
| `503` | Service Unavailable | Service temporarily unavailable |
| `504` | Gateway Timeout | Upstream service timeout |

---

## Error Handling Patterns

### Structured Error Responses

All API errors return consistent format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field": "additional error details"
    }
  }
}
```

### Error Logging

**Location**: `src/utils/logging.py`

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Structured logging
logger.error("error_name", 
    error_code="CODE",
    error_message="Message",
    context={"additional": "context"}
)
```

### User-Friendly Error Messages

**Location**: `src/utils/openai_client.py` → `get_openai_error_message()`

Converts technical errors to user-friendly messages:

```python
def get_openai_error_message(error: Exception) -> str:
    """Convert OpenAI errors to user-friendly messages."""
    if isinstance(error, RateLimitError):
        return "Rate limit exceeded. Please try again in a moment."
    # ... more conversions
```

---

## Troubleshooting

### Common Issues

#### Issue: OpenAI Rate Limit Errors

**Symptoms**: Frequent 429 errors from OpenAI API

**Solutions**:
1. Check API usage in OpenAI dashboard
2. Implement exponential backoff (already implemented)
3. Reduce request frequency
4. Upgrade OpenAI plan if needed

#### Issue: Twilio Webhook Validation Fails

**Symptoms**: Webhook requests rejected with 403

**Solutions**:
1. Verify webhook signature validation is enabled
2. Check `TWILIO_AUTH_TOKEN` is correct
3. Ensure webhook URL is HTTPS (not HTTP)
4. Check RequestValidator implementation

#### Issue: Invalid Phone Number Format

**Symptoms**: Twilio error 21211 or 21216

**Solutions**:
1. Use E.164 format: `+1234567890`
2. Include country code
3. Remove spaces, dashes, parentheses
4. Verify number is valid in Twilio

#### Issue: Database Connection Errors

**Symptoms**: 500 errors, database connection failures

**Solutions**:
1. Check database is running
2. Verify connection string in `.env`
3. Check database permissions
4. Review connection pool settings

---

## Error Code Reference by Component

### Agent System (`src/agent/`)

- `openai_api_error`: OpenAI API call failed
- `tool_execution_error`: Tool execution failed
- `invalid_tool_schema`: Tool schema validation failed

### Telephony (`src/telephony/`)

- `twilio_api_error`: Twilio API call failed
- `webhook_validation_failed`: Webhook signature invalid
- `audio_format_error`: Audio format conversion failed

### API Routes (`src/api/routes/`)

- `task_not_found`: Task ID not found
- `task_validation_error`: Task validation failed
- `confirmation_required`: High-risk action requires confirmation

### Memory System (`src/memory/`)

- `memory_retrieval_error`: Failed to retrieve memory
- `interaction_store_error`: Failed to store interaction
- `summary_generation_error`: Failed to generate summary

---

## Best Practices

1. **Always use structured error responses** - Consistent format across all endpoints
2. **Log errors with context** - Include request ID, user ID, etc.
3. **Provide user-friendly messages** - Don't expose technical details to users
4. **Implement retry logic** - For transient errors (network, rate limits)
5. **Handle errors gracefully** - Don't crash, return appropriate HTTP status
6. **Monitor error rates** - Set up alerts for high error rates

---

## Related Documentation

- [OpenAI Voice Documentation](OPENAI_VOICE_DOCUMENTATION.md) - OpenAI-specific error handling
- [Twilio Documentation](TWILIO_DOCUMENTATION.md) - Twilio-specific error handling
- [Agent Planning Framework](agent.md) - Section 8: Error Handling & Edge Cases
- [Security Policy](SECURITY_POLICY.md) - Security-related errors

---

**Last Updated**: 2025-01-29  
**Maintained By**: Development Team

