# Twilio API Documentation

Comprehensive documentation for Twilio's communication APIs, including Voice API, Media Streams, TwiML, Webhooks, SMS, and Phone Number management in the AI Caller project.

## Table of Contents

1. [Overview](#overview)
2. [Voice API](#voice-api)
3. [Media Streams](#media-streams)
4. [TwiML (Twilio Markup Language)](#twiml-twilio-markup-language)
5. [Webhooks](#webhooks)
6. [SMS/Messaging API](#smsmessaging-api)
7. [Phone Number Management](#phone-number-management)
8. [Security & Authentication](#security--authentication)
9. [Configuration](#configuration)
10. [Integration Examples](#integration-examples)
11. [Best Practices](#best-practices)
12. [Error Handling](#error-handling)
13. [Resources](#resources)

---

## Overview

Twilio is a cloud communications platform that provides APIs for voice, messaging, video, and more. This project uses Twilio primarily for:

- **Voice Calls**: Making and receiving phone calls
- **Media Streams**: Real-time bidirectional audio streaming for voice-to-voice AI
- **SMS**: Sending text messages
- **Webhooks**: Receiving call events and status updates

### Key Features Used

- **Voice API**: Initiate and manage phone calls
- **Media Streams**: WebSocket-based real-time audio streaming
- **TwiML**: XML-based instructions for call handling
- **Webhooks**: HTTP callbacks for call events
- **Phone Numbers**: Search, purchase, and manage phone numbers

---

## Voice API

The Twilio Voice API enables making and receiving phone calls programmatically.

### Authentication

Twilio uses HTTP Basic Authentication with your Account SID and Auth Token:

```python
from twilio.rest import Client

client = Client(
    account_sid="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    auth_token="your_auth_token"
)
```

### Making Outbound Calls

```python
call = client.calls.create(
    to="+15551234567",
    from_="+15559876543",
    url="https://your-server.com/webhooks/twilio/voice",
    status_callback="https://your-server.com/webhooks/twilio/status",
    status_callback_event=["initiated", "ringing", "answered", "completed"],
    record=True
)
```

### Call Parameters

- **to**: Destination phone number (E.164 format)
- **from_**: Source phone number (must be a Twilio number)
- **url**: TwiML URL for call instructions
- **status_callback**: URL for status updates
- **status_callback_event**: List of events to receive callbacks for
- **record**: Whether to record the call
- **timeout**: Call timeout in seconds (default: 60)

### Call Status Values

- `queued`: Call is queued
- `ringing`: Call is ringing
- `in-progress`: Call is in progress
- `completed`: Call completed successfully
- `busy`: Destination was busy
- `failed`: Call failed
- `no-answer`: No answer
- `canceled`: Call was canceled

### Getting Call Information

```python
call = client.calls("CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx").fetch()

print(f"Status: {call.status}")
print(f"Duration: {call.duration} seconds")
print(f"From: {call.from_}")
print(f"To: {call.to}")
```

### Updating Calls

```python
# Cancel a call
call = client.calls("CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx").update(
    status="canceled"
)

# Update call URL
call = client.calls("CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx").update(
    url="https://new-url.com/twiml"
)
```

### Call Recordings

```python
# Get recording information
recording = client.recordings("RExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx").fetch()

# Download recording
recording_url = f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
```

---

## Media Streams

Media Streams enable real-time bidirectional audio streaming over WebSocket connections. This is essential for voice-to-voice AI interactions.

### Overview

Media Streams allow you to:
- Receive real-time audio from calls
- Send real-time audio to calls
- Process audio with AI services (like OpenAI Realtime API)
- Build low-latency voice applications

### Architecture

```
Twilio Call → Media Stream (WebSocket) → Your Server → OpenAI Realtime API
```

### TwiML Configuration

To enable Media Streams, use the `<Stream>` verb inside `<Connect>`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting to AI assistant...</Say>
    <Connect>
        <Stream url="wss://your-server.com/webhooks/twilio/media">
            <Parameter name="from" value="{{From}}" />
            <Parameter name="to" value="{{To}}" />
        </Stream>
    </Connect>
</Response>
```

### WebSocket Connection

Twilio connects to your WebSocket endpoint and sends JSON messages:

#### Connection URL

- **Protocol**: `wss://` (secure) or `ws://` (insecure, for testing)
- **Endpoint**: Your WebSocket endpoint (e.g., `/webhooks/twilio/media`)
- **Parameters**: Custom parameters passed via `<Parameter>` tags

#### Event Types

**1. `start` Event**
```json
{
    "event": "start",
    "start": {
        "accountSid": "AC...",
        "callSid": "CA...",
        "streamSid": "MZ...",
        "tracks": ["inbound", "outbound"],
        "customParameters": {
            "from": "+15551234567",
            "to": "+15559876543"
        }
    }
}
```

**2. `media` Event**
```json
{
    "event": "media",
    "streamSid": "MZ...",
    "media": {
        "track": "inbound",
        "chunk": "1",
        "timestamp": "1234567890",
        "payload": "base64_encoded_audio"
    }
}
```

**3. `stop` Event**
```json
{
    "event": "stop",
    "stop": {
        "accountSid": "AC...",
        "callSid": "CA...",
        "streamSid": "MZ..."
    }
}
```

### Audio Format

- **Encoding**: µ-law (G.711)
- **Sample Rate**: 8000 Hz
- **Channels**: Mono
- **Bit Depth**: 8-bit (µ-law) → 16-bit PCM after decoding

### Receiving Audio

```python
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        
        if data.get("event") == "media":
            # Decode base64 audio
            audio_b64 = data["media"]["payload"]
            ulaw_audio = base64.b64decode(audio_b64)
            
            # Convert µ-law to PCM16
            pcm16_audio = ulaw_to_pcm16(ulaw_audio)
            
            # Process audio (e.g., send to OpenAI)
            await process_audio(pcm16_audio)
```

### Sending Audio

```python
# Convert PCM16 to µ-law
ulaw_audio = pcm16_to_ulaw(pcm16_audio)
audio_b64 = base64.b64encode(ulaw_audio).decode("utf-8")

# Send media message
message = {
    "event": "media",
    "streamSid": stream_sid,
    "media": {
        "payload": audio_b64
    }
}

await websocket.send_json(message)
```

### Audio Conversion

This project includes µ-law encoding/decoding functions:

```python
# µ-law to PCM16 (8-bit → 16-bit)
def ulaw_to_pcm16(ulaw_bytes: bytes) -> bytes:
    """Convert µ-law audio to PCM16"""
    # Implementation in src/telephony/media_stream.py

# PCM16 to µ-law (16-bit → 8-bit)
def pcm16_to_ulaw(pcm16_bytes: bytes) -> bytes:
    """Convert PCM16 audio to µ-law"""
    # Implementation in src/telephony/media_stream.py
```

### Stream Lifecycle

1. **Connection**: Twilio connects to your WebSocket endpoint
2. **Start Event**: Receive `start` event with `callSid` and `streamSid`
3. **Media Events**: Receive/send `media` events continuously
4. **Stop Event**: Receive `stop` event when call ends
5. **Disconnect**: WebSocket connection closes

---

## TwiML (Twilio Markup Language)

TwiML is an XML-based language for instructing Twilio on how to handle calls.

### Basic Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <!-- TwiML verbs here -->
</Response>
```

### Common Verbs

#### `<Say>`

Speak text to the caller:

```xml
<Say voice="alice" language="en-US">
    Hello, this is a test message.
</Say>
```

**Attributes:**
- `voice`: Voice to use (`alice`, `man`, `woman`)
- `language`: Language code (`en-US`, `en-GB`, `es`, etc.)
- `loop`: Number of times to repeat (default: 1)

#### `<Gather>`

Collect user input (DTMF or speech):

```xml
<Gather 
    input="speech" 
    action="/webhooks/twilio/voice"
    method="POST"
    language="en-US"
    timeout="5"
    speechTimeout="auto">
    <Say>Please say your message.</Say>
</Gather>
```

**Attributes:**
- `input`: Input type (`dtmf`, `speech`, or both)
- `action`: URL to send results
- `method`: HTTP method (`GET` or `POST`)
- `language`: Language for speech recognition
- `timeout`: Timeout in seconds
- `speechTimeout`: Auto or manual timeout

**Result Parameters:**
- `SpeechResult`: Recognized speech text
- `Confidence`: Confidence score (0-1)

#### `<Connect>`

Connect to another call or stream:

```xml
<Connect>
    <Stream url="wss://your-server.com/media">
        <Parameter name="custom" value="data" />
    </Stream>
</Connect>
```

#### `<Dial>`

Dial another number:

```xml
<Dial timeout="30" record="true">
    <Number>+15551234567</Number>
</Dial>
```

#### `<Redirect>`

Redirect to another TwiML URL:

```xml
<Redirect method="POST">/webhooks/twilio/voice</Redirect>
```

#### `<Hangup>`

End the call:

```xml
<Hangup/>
```

### Example: Voice Assistant with Gather

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello! I'm your AI assistant. What would you like me to help you with?</Say>
    <Gather 
        input="speech"
        action="/webhooks/twilio/voice"
        method="POST"
        language="en-US"
        timeout="5">
        <Say>How can I help you?</Say>
    </Gather>
    <Redirect method="POST">/webhooks/twilio/voice</Redirect>
</Response>
```

### Example: Media Streams

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting to AI assistant...</Say>
    <Connect>
        <Stream url="wss://your-server.com/webhooks/twilio/media">
            <Parameter name="from" value="{{From}}" />
            <Parameter name="to" value="{{To}}" />
        </Stream>
    </Connect>
</Response>
```

### Generating TwiML with Python SDK

```python
from twilio.twiml.voice_response import VoiceResponse, Gather

resp = VoiceResponse()
resp.say("Hello, how can I help you?")

gather = Gather(
    input="speech",
    action="/webhooks/twilio/voice",
    method="POST"
)
gather.say("Please speak your request.")
resp.append(gather)

print(str(resp))  # Output TwiML XML
```

---

## Webhooks

Webhooks are HTTP callbacks that Twilio sends to your server for call events.

### Voice Webhook

Called when a call is initiated or needs new instructions:

**Endpoint**: `POST /webhooks/twilio/voice`

**Request Parameters:**
- `CallSid`: Unique call identifier
- `From`: Caller's phone number
- `To`: Called phone number
- `CallStatus`: Current call status
- `SpeechResult`: Speech recognition result (if using `<Gather>`)
- `Confidence`: Speech recognition confidence

**Response**: TwiML XML

### Status Callback

Called when call status changes:

**Endpoint**: `POST /webhooks/twilio/status`

**Request Parameters:**
- `CallSid`: Call identifier
- `CallStatus`: New status
- `CallDuration`: Call duration in seconds
- `RecordingUrl`: Recording URL (if recorded)

**Response**: HTTP 200 OK (Twilio doesn't process response body)

### Webhook Security

Always validate webhook signatures to ensure requests are from Twilio:

```python
from twilio.request_validator import RequestValidator

validator = RequestValidator(auth_token)
signature = request.headers.get('X-Twilio-Signature', '')
url = str(request.url)
form_data = dict(await request.form())

is_valid = validator.validate(url, form_data, signature)
```

### Webhook URL Configuration

Set webhook URLs in:
1. **Phone Number Settings**: For inbound calls
2. **Call API**: For outbound calls
3. **TwiML**: Via `<Gather>` or `<Redirect>` verbs

**Requirements:**
- Must be publicly accessible (use ngrok for local testing)
- Must use HTTPS in production
- Must respond within 10 seconds

---

## SMS/Messaging API

Twilio's Messaging API enables sending and receiving SMS messages.

### Sending SMS

```python
message = client.messages.create(
    to="+15551234567",
    from_="+15559876543",
    body="Hello, this is a test message!"
)
```

### SMS Parameters

- **to**: Destination phone number
- **from_**: Source phone number (Twilio number or alphanumeric sender ID)
- **body**: Message text (max 1600 characters)
- **status_callback**: URL for delivery status updates
- **media_url**: URL for MMS images (up to 10)

### Receiving SMS

Configure your Twilio number's SMS webhook URL:

```python
# In Twilio Console or via API
client.incoming_phone_numbers("PN...").update(
    sms_url="https://your-server.com/webhooks/twilio/sms"
)
```

**Webhook Parameters:**
- `MessageSid`: Message identifier
- `From`: Sender's phone number
- `To`: Recipient's phone number
- `Body`: Message text
- `NumMedia`: Number of media attachments

### MMS (Multimedia Messages)

```python
message = client.messages.create(
    to="+15551234567",
    from_="+15559876543",
    body="Check out this image!",
    media_url=["https://example.com/image.jpg"]
)
```

### Message Status

- `queued`: Message queued
- `sent`: Message sent
- `delivered`: Message delivered
- `undelivered`: Message failed to deliver
- `failed`: Message failed

---

## Phone Number Management

Twilio provides APIs for searching, purchasing, and managing phone numbers.

### Searching Available Numbers

```python
# Search US local numbers
available_numbers = client.available_phone_numbers("US").local.list(
    area_code="415",
    limit=20
)

for number in available_numbers:
    print(f"{number.phone_number} - {number.locality}, {number.region}")
```

### Search Parameters

- `area_code`: Area code filter
- `contains`: Number contains pattern
- `capabilities`: Required capabilities (`voice`, `SMS`, `MMS`)
- `limit`: Maximum results

### Purchasing a Number

```python
incoming_number = client.incoming_phone_numbers.create(
    phone_number="+15551234567"
)
```

### Listing Owned Numbers

```python
numbers = client.incoming_phone_numbers.list()

for number in numbers:
    print(f"{number.phone_number} - SID: {number.sid}")
```

### Updating Number Configuration

```python
client.incoming_phone_numbers("PN...").update(
    voice_url="https://your-server.com/webhooks/twilio/voice",
    voice_method="POST",
    sms_url="https://your-server.com/webhooks/twilio/sms",
    sms_method="POST"
)
```

### Releasing a Number

```python
client.incoming_phone_numbers("PN...").delete()
```

### Phone Number Capabilities

- **Voice**: Can make/receive calls
- **SMS**: Can send/receive SMS
- **MMS**: Can send/receive MMS
- **Fax**: Can send/receive fax (legacy)

---

## Security & Authentication

### API Authentication

Twilio uses HTTP Basic Authentication:

```python
from twilio.rest import Client

client = Client(
    account_sid="AC...",
    auth_token="your_auth_token"
)
```

**Best Practices:**
- Use API Keys in production (not Account SID/Auth Token)
- Store credentials in environment variables
- Never commit credentials to version control
- Rotate credentials regularly

### Webhook Signature Validation

Always validate webhook signatures:

```python
from twilio.request_validator import RequestValidator

def validate_twilio_request(request, form_data):
    validator = RequestValidator(auth_token)
    signature = request.headers.get('X-Twilio-Signature', '')
    url = str(request.url)
    
    return validator.validate(url, form_data, signature)
```

### Request Validation Process

1. Extract `X-Twilio-Signature` header
2. Get request URL
3. Get form data (sorted by key)
4. Compute HMAC-SHA1 signature
5. Compare with provided signature

### Security Best Practices

1. **Always validate webhooks**: Prevent unauthorized requests
2. **Use HTTPS**: Encrypt all webhook URLs
3. **Rate limiting**: Implement rate limiting on webhook endpoints
4. **Logging**: Log all webhook requests for audit
5. **Error handling**: Don't expose sensitive information in errors

---

## Configuration

### Environment Variables

```bash
# Required
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567

# Optional
TWILIO_WEBHOOK_URL=https://your-server.com
TWILIO_MEDIA_STREAMS_ENABLED=true
TWILIO_MEDIA_STREAMS_WS_BASE_URL=wss://your-server.com
```

### Configuration in Code

```python
from src.utils.config import get_settings

settings = get_settings()

# Access configuration
account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
phone_number = settings.TWILIO_PHONE_NUMBER
```

### Phone Number Setup

1. **Purchase a number** in Twilio Console or via API
2. **Configure webhooks**:
   - Voice URL: `https://your-server.com/webhooks/twilio/voice`
   - Status URL: `https://your-server.com/webhooks/twilio/status`
3. **Enable Media Streams** (if using):
   - Set `TWILIO_MEDIA_STREAMS_ENABLED=true`
   - Configure WebSocket endpoint

---

## Integration Examples

### Example 1: Outbound Call with Media Streams

```python
from src.telephony.twilio_client import TwilioService

twilio = TwilioService()

# Initiate call
call_info = twilio.initiate_call(
    to_number="+15551234567",
    from_number="+15559876543",
    webhook_url="https://your-server.com/webhooks/twilio/voice",
    status_callback="https://your-server.com/webhooks/twilio/status"
)

# Media stream will be established automatically
# when Twilio connects to your WebSocket endpoint
```

### Example 2: Media Stream Handler

```python
# src/telephony/media_stream.py

class MediaStreamHandler:
    async def handle_media_stream(self, websocket: WebSocket):
        await websocket.accept()
        call_sid = None
        stream_sid = None
        
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get("event") == "start":
                call_sid = data["start"]["callSid"]
                stream_sid = data["start"]["streamSid"]
                # Initialize AI bridge
                
            elif data.get("event") == "media":
                # Decode audio
                audio_b64 = data["media"]["payload"]
                ulaw_audio = base64.b64decode(audio_b64)
                pcm16_audio = ulaw_to_pcm16(ulaw_audio)
                
                # Send to OpenAI Realtime API
                await realtime_bridge.handle_twilio_audio(call_sid, pcm16_audio)
                
            elif data.get("event") == "stop":
                # Cleanup
                break
```

### Example 3: Voice Webhook with TwiML

```python
# src/api/webhooks/twilio_webhook.py

@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    data = await request.form()
    
    # Validate signature
    if not validate_twilio_request(request, dict(data)):
        return Response(
            content="<Response><Say>Authentication error</Say></Response>",
            media_type="application/xml"
        )
    
    # Check if Media Streams enabled
    if settings.TWILIO_MEDIA_STREAMS_ENABLED:
        websocket_url = "wss://your-server.com/webhooks/twilio/media"
        twiml = media_stream_handler.generate_twiml(websocket_url)
        return Response(content=twiml, media_type="application/xml")
    
    # Fallback to Gather/Say
    resp = VoiceResponse()
    resp.say("Hello! How can I help you?")
    
    gather = Gather(
        input="speech",
        action="/webhooks/twilio/voice",
        method="POST"
    )
    gather.say("Please speak your request.")
    resp.append(gather)
    
    return Response(content=str(resp), media_type="application/xml")
```

### Example 4: Sending SMS

```python
from src.agent.tools import send_sms

# Via tool
await send_sms(
    to_number="+15551234567",
    message="Hello from AI assistant!"
)

# Direct Twilio client
from twilio.rest import Client

client = Client(account_sid, auth_token)
message = client.messages.create(
    to="+15551234567",
    from_="+15559876543",
    body="Hello!"
)
```

---

## Best Practices

### Voice Calls

1. **Use Media Streams for real-time AI**: Better latency than Gather/Say
2. **Handle call failures gracefully**: Implement retry logic
3. **Monitor call quality**: Track metrics like duration, status
4. **Set appropriate timeouts**: Balance user experience and costs
5. **Record important calls**: Enable recording for compliance

### Media Streams

1. **Use secure WebSocket (WSS)**: Always use `wss://` in production
2. **Handle reconnections**: Implement reconnection logic
3. **Monitor stream health**: Track connection status
4. **Optimize audio processing**: Minimize latency in audio pipeline
5. **Handle errors gracefully**: Don't crash on audio decode errors

### Webhooks

1. **Validate all requests**: Always check signatures
2. **Respond quickly**: Keep response time under 10 seconds
3. **Handle retries**: Twilio retries failed webhooks
4. **Log everything**: Track all webhook events
5. **Use HTTPS**: Never use HTTP in production

### Phone Numbers

1. **Choose appropriate numbers**: Consider local vs. toll-free
2. **Verify capabilities**: Ensure numbers support required features
3. **Monitor costs**: Track usage and costs
4. **Release unused numbers**: Save money by releasing unused numbers
5. **Configure webhooks**: Set up webhooks for all numbers

### Error Handling

1. **Catch Twilio exceptions**: Handle `TwilioException` properly
2. **Retry transient errors**: Implement exponential backoff
3. **Log errors**: Include context in error logs
4. **User-friendly messages**: Don't expose technical errors to users
5. **Monitor error rates**: Track and alert on high error rates

---

## Error Handling

### Common Twilio Exceptions

```python
from twilio.base.exceptions import TwilioException, TwilioRestException

try:
    call = client.calls.create(...)
except TwilioRestException as e:
    # Handle API errors
    print(f"Error {e.status}: {e.msg}")
except TwilioException as e:
    # Handle other Twilio errors
    print(f"Twilio error: {e}")
```

### Complete Error Code Reference

#### Voice API Error Codes

| Code | Description | HTTP Status | Solution |
|------|-------------|-------------|----------|
| 20000 | Invalid URL | 400 | Check webhook URL format |
| 20001 | Invalid HTTP method | 400 | Use POST for webhooks |
| 20002 | Invalid parameter | 400 | Check parameter names/values |
| 20003 | Missing required parameter | 400 | Include all required parameters |
| 20404 | Resource not found | 404 | Check resource ID |
| 20429 | Too many requests | 429 | Implement rate limiting/retry |
| 21211 | Invalid 'To' phone number | 400 | Use valid E.164 format |
| 21216 | Invalid 'To' phone number format | 400 | Use E.164 format (+1234567890) |
| 21608 | Invalid 'From' phone number | 400 | Use valid Twilio number |
| 21614 | 'To' number is not a valid mobile number | 400 | Use mobile number |
| 21615 | 'From' number is not capable of voice | 400 | Number doesn't support voice |
| 21616 | 'To' number is not capable of voice | 400 | Number doesn't support voice |

#### Messaging API Error Codes

| Code | Description | HTTP Status | Solution |
|------|-------------|-------------|----------|
| 21614 | Unsubscribed recipient | 400 | Remove from database |
| 21619 | Invalid message body | 400 | Check message content |
| 21620 | Message body too long | 400 | Split into multiple messages |

#### Common Error Handling

```python
from twilio.base.exceptions import TwilioRestException

try:
    call = client.calls.create(...)
except TwilioRestException as e:
    if e.status == 429:  # Rate limit
        # Implement exponential backoff
        time.sleep(2 ** retry_count)
    elif e.status == 400:
        # Invalid request - log and return user-friendly error
        logger.error("invalid_request", error=str(e))
        return {"error": "Invalid request. Please check your input."}
    elif e.status == 404:
        # Resource not found
        return {"error": "Resource not found."}
    else:
        # Unknown error
        logger.error("twilio_error", status=e.status, error=str(e))
        return {"error": "An error occurred. Please try again."}
```

### Handling Webhook Errors

```python
@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    try:
        # Process webhook
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.error("webhook_error", error=str(e))
        # Return error TwiML
        error_twiml = "<Response><Say>I'm sorry, I'm having trouble right now.</Say></Response>"
        return Response(content=error_twiml, media_type="application/xml")
```

### Media Stream Error Handling

```python
async def handle_media_stream(websocket: WebSocket):
    try:
        while True:
            message = await websocket.receive_text()
            # Process message
    except WebSocketDisconnect:
        logger.info("websocket_disconnected")
    except Exception as e:
        logger.error("media_stream_error", error=str(e))
        # Cleanup and close
```

---

## Frequently Asked Questions (FAQ)

### Voice Calls

**Q: How do I test webhooks locally?**  
A: Use ngrok to expose your local server: `ngrok http 8000`, then update Twilio webhook URL to the ngrok URL. Alternatively, use Twilio's webhook testing tools.

**Q: What's the difference between Media Streams and Gather/Say?**  
A: Media Streams provides real-time bidirectional audio streaming (WebSocket-based), while Gather/Say is request-response based with TwiML. Media Streams is better for AI voice agents, Gather/Say is better for simple IVR systems.

**Q: How do I handle webhook signature validation?**  
A: Use `RequestValidator` from Twilio SDK with your auth token. Always validate webhook signatures in production to prevent unauthorized requests.

**Q: What's the best way to handle call failures?**  
A: Implement retry logic with exponential backoff for transient errors. Log all failures and monitor error rates. Use Twilio's status callbacks to track call status.

**Q: Can I record calls?**  
A: Yes, set `record=True` in `calls.create()` or use `<Record>` in TwiML. Recordings are stored in Twilio and accessible via API.

### SMS/Messaging

**Q: How do I handle SMS opt-outs?**  
A: Check for error code `21614` (unsubscribed recipient). Remove opted-out numbers from your database and respect opt-out requests.

**Q: What's the character limit for SMS?**  
A: Standard SMS is 160 characters. Longer messages are automatically split into multiple SMS (concatenated SMS). Each segment counts as a separate message for billing.

**Q: Can I send images or media via SMS?**  
A: Yes, use MMS (Multimedia Messaging Service). Include `media_url` parameter in `messages.create()`. Not all carriers support MMS.

**Q: How do I handle delivery status?**  
A: Use status callbacks. Set `status_callback` parameter to receive delivery status updates via webhook.

### Phone Numbers

**Q: How do I choose between local and toll-free numbers?**  
A: Local numbers are cheaper and work well for regional services. Toll-free numbers (1-800) are better for national services and may have higher costs.

**Q: Can I use my existing phone number?**  
A: Yes, you can port your existing number to Twilio. Contact Twilio support for porting assistance.

**Q: How do I release unused numbers?**  
A: Use `incoming_phone_numbers.update()` to release numbers, or delete them via Twilio Console. This stops monthly charges.

### Media Streams

**Q: What audio format does Media Streams use?**  
A: Media Streams uses PCM16 audio at 8kHz sample rate (μ-law or A-law encoding). You may need to convert to/from other formats.

**Q: How do I handle WebSocket reconnections?**  
A: Implement reconnection logic with exponential backoff. Track connection state and reconnect when disconnected. See `src/telephony/media_stream.py` for example.

**Q: What's the latency of Media Streams?**  
A: Typically 50-200ms depending on network conditions. Lower than traditional telephony but higher than direct WebSocket connections.

### Webhooks

**Q: How quickly must I respond to webhooks?**  
A: Respond within 10 seconds. Twilio will retry if no response is received. For long-running operations, return TwiML immediately and process asynchronously.

**Q: What happens if my webhook fails?**  
A: Twilio retries failed webhooks with exponential backoff. Check your webhook logs and ensure your endpoint is reliable.

**Q: Can I use HTTP instead of HTTPS?**  
A: Only for local development. Production must use HTTPS. Twilio requires HTTPS for webhook URLs in production.

### Error Handling

**Q: What do common Twilio error codes mean?**  
A: See [Error Code Reference](ERROR_CODES.md) for complete list. Common codes: `21211` (invalid phone number), `20429` (rate limit), `21608` (invalid from number).

**Q: How do I handle rate limits?**  
A: Implement exponential backoff. Twilio rate limits vary by account tier. Monitor your usage and upgrade if needed.

**Q: What if I get authentication errors?**  
A: Verify your `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct. Check they're set in environment variables or configuration.

### Configuration

**Q: Where do I set my Twilio credentials?**  
A: Set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` in `.env` file or environment variables. Never commit credentials to version control.

**Q: How do I configure webhook URLs?**  
A: Set webhook URLs in Twilio Console for your phone numbers, or programmatically via API. Use `status_callback` and `voice_url` parameters.

**Q: Can I use different webhook URLs for different numbers?**  
A: Yes, configure webhook URLs per phone number. Useful for different environments (dev, staging, production).

---

## Troubleshooting Guide

### Voice Call Issues

#### Issue: Calls Not Connecting
**Symptoms**: Call fails immediately or doesn't ring
**Causes**:
- Invalid phone numbers
- Account restrictions
- Insufficient account balance
- Webhook URL not accessible

**Solutions**:
1. Verify phone numbers in E.164 format (+1234567890)
2. Check Twilio account status and balance
3. Verify webhook URL is publicly accessible (use ngrok for local)
4. Check Twilio console for error details
5. Verify account has voice capabilities enabled

#### Issue: Webhook Not Receiving Requests
**Symptoms**: Twilio not calling your webhook
**Causes**:
- Webhook URL not set
- URL not publicly accessible
- SSL certificate issues
- Firewall blocking requests

**Solutions**:
1. Verify webhook URL in phone number settings
2. Use ngrok for local development: `ngrok http 8000`
3. Ensure HTTPS for production (Twilio requires HTTPS)
4. Check firewall allows incoming connections
5. Verify webhook URL returns 200 OK

#### Issue: Webhook Signature Validation Fails
**Symptoms**: Signature validation always fails
**Causes**:
- Incorrect auth token
- URL mismatch (query params, trailing slashes)
- Form data not included in validation
- Time skew

**Solutions**:
1. Verify `TWILIO_AUTH_TOKEN` matches Twilio console
2. Use exact URL from request (including query params)
3. Include all form data in validation
4. Check system clock is synchronized
5. Use `RequestValidator` from Twilio SDK

### Media Streams Issues

#### Issue: WebSocket Connection Fails
**Symptoms**: Media stream doesn't connect
**Causes**:
- WebSocket URL not accessible
- Incorrect URL format (ws:// vs wss://)
- Firewall blocking WebSocket
- TwiML not configured correctly

**Solutions**:
1. Verify WebSocket URL is publicly accessible
2. Use `wss://` for production (secure WebSocket)
3. Check firewall allows WebSocket connections
4. Verify TwiML includes `<Stream>` with correct URL
5. Check Twilio console for connection errors

#### Issue: No Audio Received
**Symptoms**: No audio data in media stream
**Causes**:
- Audio format mismatch
- µ-law decode failing
- Buffer issues
- Event handling not implemented

**Solutions**:
1. Verify audio format: 8kHz µ-law from Twilio
2. Check µ-law decode function is working
3. Implement `media` event handler
4. Verify `start` event received with callSid/streamSid
5. Check logs for audio events

#### Issue: Audio Not Sending to Call
**Symptoms**: Caller can't hear audio
**Causes**:
- Audio format incorrect (must be µ-law)
- Stream SID mismatch
- WebSocket not sending
- Audio not encoded correctly

**Solutions**:
1. Convert PCM16 to µ-law before sending
2. Verify streamSid matches from `start` event
3. Check WebSocket is still connected
4. Verify audio encoding: base64 encode µ-law bytes
5. Check message format matches Twilio spec

### SMS Issues

#### Issue: SMS Not Sending
**Symptoms**: Message not delivered
**Causes**:
- Invalid phone number
- Account restrictions
- Insufficient balance
- Carrier blocking

**Solutions**:
1. Verify phone number format (E.164)
2. Check account status and balance
3. Verify number has SMS capability
4. Check carrier delivery status
5. Review Twilio console for error details

#### Issue: SMS Not Receiving
**Symptoms**: Incoming SMS not reaching webhook
**Causes**:
- SMS webhook not configured
- Webhook URL not accessible
- Number not capable of SMS
- Carrier issues

**Solutions**:
1. Configure SMS webhook URL in phone number settings
2. Verify webhook URL is publicly accessible
3. Check number has SMS capability
4. Test webhook with ngrok
5. Check Twilio console for incoming messages

### Local Development Issues

#### Issue: ngrok Connection Issues
**Symptoms**: ngrok tunnel not working
**Causes**:
- ngrok not running
- Port mismatch
- Firewall blocking
- SSL certificate issues

**Solutions**:
1. Start ngrok: `ngrok http 8000`
2. Verify port matches your server
3. Check firewall allows ngrok
4. Use ngrok's HTTPS URL for webhooks
5. Update Twilio webhook URL to ngrok URL

#### Issue: Webhook Timeout
**Symptoms**: Webhook requests timing out
**Causes**:
- Slow response time
- Long-running operations
- Network issues
- Server overload

**Solutions**:
1. Return TwiML immediately (< 10 seconds)
2. Process long operations asynchronously
3. Optimize webhook handler performance
4. Use background tasks for heavy processing
5. Monitor server response times

---

## Resources

### Official Documentation

- [Twilio API Documentation](https://www.twilio.com/docs)
- [Voice API Reference](https://www.twilio.com/docs/voice/api)
- [Media Streams Guide](https://www.twilio.com/docs/voice/media-streams)
- [TwiML Reference](https://www.twilio.com/docs/voice/twiml)
- [Messaging API](https://www.twilio.com/docs/sms)
- [Phone Numbers API](https://www.twilio.com/docs/phone-numbers)

### SDKs and Libraries

- [Twilio Python SDK](https://github.com/twilio/twilio-python)
- [Twilio Python Documentation](https://www.twilio.com/docs/libraries/python)
- [OpenAPI Specification](https://www.twilio.com/docs/openapi)

### Developer Resources

- [Twilio Developer Hub](https://www.twilio.com/en-us/developers)
- [Twilio Console](https://console.twilio.com/)
- [Twilio Support](https://support.twilio.com/)

### Project-Specific Files

- `src/telephony/twilio_client.py`: Twilio service wrapper
- `src/telephony/media_stream.py`: Media Streams handler
- `src/api/webhooks/twilio_webhook.py`: Webhook handlers
- `src/agent/tools.py`: SMS and call tools
- `src/utils/config.py`: Configuration management

---

## Version History

- **2024-12**: Initial documentation created
- Current Twilio SDK version: `9.0.0`
- Media Streams API: Stable
- Voice API: v2010

---

## Notes

- Media Streams require WebSocket support
- TwiML responses must be valid XML
- Webhook URLs must be publicly accessible
- Phone numbers must be in E.164 format (`+[country][number]`)
- Rate limits apply to all API endpoints
- Costs vary by country and service type

For the most up-to-date information, refer to the [Twilio Documentation](https://www.twilio.com/docs).

