# Twilio API Capabilities Reference

Comprehensive reference guide for all Twilio API capabilities, endpoints, and features available for integration.

## Table of Contents

1. [API Overview](#api-overview)
2. [Voice API Capabilities](#voice-api-capabilities)
3. [Messaging API Capabilities](#messaging-api-capabilities)
4. [Phone Numbers API Capabilities](#phone-numbers-api-capabilities)
5. [Media Streams API Capabilities](#media-streams-api-capabilities)
6. [Video API Capabilities](#video-api-capabilities)
7. [Verify API Capabilities](#verify-api-capabilities)
8. [Lookup API Capabilities](#lookup-api-capabilities)
9. [TaskRouter API Capabilities](#taskrouter-api-capabilities)
10. [Serverless API Capabilities](#serverless-api-capabilities)
11. [IAM API Capabilities](#iam-api-capabilities)
12. [Email API Capabilities (SendGrid)](#email-api-capabilities-sendgrid)
13. [Chat API Capabilities](#chat-api-capabilities)
14. [Programmable Wireless API Capabilities](#programmable-wireless-api-capabilities)
15. [API Endpoints Reference](#api-endpoints-reference)
16. [Rate Limits & Quotas](#rate-limits--quotas)
17. [Pricing Overview](#pricing-overview)

---

## API Overview

Twilio provides a comprehensive suite of REST APIs organized by product. All APIs follow REST principles and use HTTP Basic Authentication.

### Base URL

```
https://api.twilio.com/2010-04-01
```

### Authentication

All API requests require HTTP Basic Authentication:
- **Username**: Account SID (`AC...`)
- **Password**: Auth Token

### Response Format

- **Success**: HTTP 200-299 with JSON response
- **Error**: HTTP 400-599 with error JSON

### Common Response Structure

```json
{
  "sid": "CA...",
  "account_sid": "AC...",
  "status": "completed",
  "date_created": "2024-01-01T00:00:00Z",
  "date_updated": "2024-01-01T00:00:00Z",
  "uri": "/2010-04-01/Accounts/AC.../Calls/CA...json"
}
```

---

## Voice API Capabilities

### Core Capabilities

1. **Make Outbound Calls**
   - Initiate calls to any phone number globally
   - Support for PSTN, SIP, and WebRTC endpoints
   - Custom call parameters and metadata

2. **Receive Inbound Calls**
   - Handle incoming calls to Twilio numbers
   - Route calls based on caller ID, time, or other criteria
   - Dynamic call handling with TwiML

3. **Call Control**
   - Modify calls in progress
   - Transfer calls
   - Conference multiple participants
   - Mute/unmute participants
   - Record calls

4. **Call Monitoring**
   - Real-time call status updates
   - Call quality metrics
   - Call logs and history
   - Call recordings

5. **Speech Recognition**
   - Speech-to-text conversion
   - Natural language understanding
   - Multi-language support
   - Custom vocabulary

6. **Text-to-Speech**
   - Multiple voice options
   - SSML support
   - Language and accent selection
   - Speed and pitch control

### Voice API Endpoints

#### Calls

```
POST   /Accounts/{AccountSid}/Calls.json
GET    /Accounts/{AccountSid}/Calls.json
GET    /Accounts/{AccountSid}/Calls/{CallSid}.json
POST   /Accounts/{AccountSid}/Calls/{CallSid}.json
DELETE /Accounts/{AccountSid}/Calls/{CallSid}.json
```

**Operations:**
- `create()`: Make a new call
- `list()`: List all calls
- `fetch()`: Get call details
- `update()`: Update call (redirect, cancel)
- `delete()`: Delete call record

#### Recordings

```
GET    /Accounts/{AccountSid}/Recordings.json
GET    /Accounts/{AccountSid}/Recordings/{RecordingSid}.json
DELETE /Accounts/{AccountSid}/Recordings/{RecordingSid}.json
```

**Operations:**
- `list()`: List all recordings
- `fetch()`: Get recording details
- `delete()`: Delete recording

#### Conferences

```
GET    /Accounts/{AccountSid}/Conferences.json
GET    /Accounts/{AccountSid}/Conferences/{ConferenceSid}.json
POST   /Accounts/{AccountSid}/Conferences/{ConferenceSid}/Participants.json
GET    /Accounts/{AccountSid}/Conferences/{ConferenceSid}/Participants.json
DELETE /Accounts/{AccountSid}/Conferences/{ConferenceSid}/Participants/{CallSid}.json
```

**Operations:**
- `list()`: List conferences
- `fetch()`: Get conference details
- `participants.create()`: Add participant
- `participants.list()`: List participants
- `participants.delete()`: Remove participant

#### Queues

```
POST   /Accounts/{AccountSid}/Queues.json
GET    /Accounts/{AccountSid}/Queues.json
GET    /Accounts/{AccountSid}/Queues/{QueueSid}.json
POST   /Accounts/{AccountSid}/Queues/{QueueSid}.json
DELETE /Accounts/{AccountSid}/Queues/{QueueSid}.json
```

**Operations:**
- `create()`: Create call queue
- `list()`: List queues
- `fetch()`: Get queue details
- `update()`: Update queue settings
- `delete()`: Delete queue

### Advanced Features

- **Call Recording**: Automatic or on-demand recording
- **Call Transcription**: Real-time or post-call transcription
- **Call Queuing**: Queue calls with custom hold music
- **Call Forwarding**: Forward calls to multiple numbers
- **Call Screening**: Screen calls before connecting
- **Call Whispering**: Whisper to agents before connecting
- **Call Barge**: Monitor or join calls
- **Call Coaching**: Coach agents during calls

---

## Messaging API Capabilities

### Core Capabilities

1. **SMS (Short Message Service)**
   - Send/receive text messages globally
   - Long message support (concatenated SMS)
   - Delivery status tracking
   - Message scheduling

2. **MMS (Multimedia Messaging Service)**
   - Send/receive images, videos, audio
   - Multiple media attachments
   - Media URL support
   - Media storage

3. **WhatsApp Business API**
   - Send/receive WhatsApp messages
   - Media support (images, videos, documents)
   - Template messages
   - Interactive messages

4. **RCS (Rich Communication Services)**
   - Rich media messages
   - Interactive buttons and cards
   - Read receipts
   - Typing indicators

5. **Facebook Messenger**
   - Send/receive Messenger messages
   - Media attachments
   - Quick replies
   - Persistent menu

6. **Apple Business Chat**
   - Send/receive messages via iMessage
   - Rich media support
   - Interactive elements

### Messaging API Endpoints

#### Messages

```
POST   /Accounts/{AccountSid}/Messages.json
GET    /Accounts/{AccountSid}/Messages.json
GET    /Accounts/{AccountSid}/Messages/{MessageSid}.json
POST   /Accounts/{AccountSid}/Messages/{MessageSid}.json
DELETE /Accounts/{AccountSid}/Messages/{MessageSid}.json
```

**Operations:**
- `create()`: Send message
- `list()`: List messages
- `fetch()`: Get message details
- `update()`: Update message (cancel scheduled)
- `delete()`: Delete message

#### Media

```
GET    /Accounts/{AccountSid}/Messages/{MessageSid}/Media.json
GET    /Accounts/{AccountSid}/Messages/{MessageSid}/Media/{MediaSid}.json
DELETE /Accounts/{AccountSid}/Messages/{MessageSid}/Media/{MediaSid}.json
```

**Operations:**
- `list()`: List media attachments
- `fetch()`: Get media details
- `delete()`: Delete media

#### Short Codes

```
GET    /Accounts/{AccountSid}/ShortCodes.json
GET    /Accounts/{AccountSid}/ShortCodes/{ShortCodeSid}.json
POST   /Accounts/{AccountSid}/ShortCodes/{ShortCodeSid}.json
```

**Operations:**
- `list()`: List short codes
- `fetch()`: Get short code details
- `update()`: Update short code configuration

### Advanced Features

- **Message Scheduling**: Schedule messages for future delivery
- **Message Queuing**: Queue messages for batch sending
- **Delivery Receipts**: Track message delivery status
- **Read Receipts**: Know when messages are read (WhatsApp, RCS)
- **Message Templates**: Pre-approved message templates
- **Content Templates**: Reusable message content
- **Link Shortening**: Automatic URL shortening
- **Message Filtering**: Filter messages by criteria

---

## Phone Numbers API Capabilities

### Core Capabilities

1. **Search Available Numbers**
   - Search by country, area code, or pattern
   - Filter by capabilities (voice, SMS, MMS)
   - Local, toll-free, and mobile numbers
   - Number recommendations

2. **Purchase Numbers**
   - Purchase phone numbers instantly
   - Bulk number purchasing
   - Number porting (bring your own number)

3. **Manage Numbers**
   - Configure webhook URLs
   - Set voice/SMS capabilities
   - Configure call routing
   - Update number settings

4. **Release Numbers**
   - Release unused numbers
   - Bulk number release
   - Number transfer between accounts

5. **Number Lookup**
   - Get number details
   - Check number capabilities
   - Verify number ownership

### Phone Numbers API Endpoints

#### Incoming Phone Numbers

```
POST   /Accounts/{AccountSid}/IncomingPhoneNumbers.json
GET    /Accounts/{AccountSid}/IncomingPhoneNumbers.json
GET    /Accounts/{AccountSid}/IncomingPhoneNumbers/{PhoneNumberSid}.json
POST   /Accounts/{AccountSid}/IncomingPhoneNumbers/{PhoneNumberSid}.json
DELETE /Accounts/{AccountSid}/IncomingPhoneNumbers/{PhoneNumberSid}.json
```

**Operations:**
- `create()`: Purchase number
- `list()`: List owned numbers
- `fetch()`: Get number details
- `update()`: Update number configuration
- `delete()`: Release number

#### Available Phone Numbers

```
GET    /Accounts/{AccountSid}/AvailablePhoneNumbers/{CountryCode}/Local.json
GET    /Accounts/{AccountSid}/AvailablePhoneNumbers/{CountryCode}/TollFree.json
GET    /Accounts/{AccountSid}/AvailablePhoneNumbers/{CountryCode}/Mobile.json
```

**Operations:**
- `local.list()`: Search local numbers
- `toll_free.list()`: Search toll-free numbers
- `mobile.list()`: Search mobile numbers

### Advanced Features

- **Number Porting**: Port existing numbers to Twilio
- **Number Masking**: Mask real numbers for privacy
- **Number Validation**: Validate phone number format
- **Number Formatting**: Format numbers in different styles
- **Number Capabilities**: Check voice/SMS/MMS support
- **Number Pricing**: Get pricing for numbers

---

## Media Streams API Capabilities

### Core Capabilities

1. **Real-Time Audio Streaming**
   - Bidirectional audio streaming
   - WebSocket-based connection
   - Low-latency audio transmission
   - Multiple track support

2. **Audio Format Support**
   - µ-law (G.711)
   - PCM16
   - Opus
   - Custom formats

3. **Stream Control**
   - Start/stop streams
   - Pause/resume streams
   - Stream metadata
   - Custom parameters

4. **Multi-Stream Support**
   - Multiple concurrent streams
   - Stream isolation
   - Independent stream control

### Media Streams Features

- **Bidirectional Audio**: Send and receive audio simultaneously
- **Real-Time Processing**: Process audio in real-time
- **Low Latency**: Sub-second latency
- **High Quality**: High-quality audio transmission
- **Custom Metadata**: Pass custom data with streams
- **Stream Events**: Receive stream lifecycle events

### Use Cases

- Voice AI assistants
- Real-time transcription
- Voice analytics
- Call monitoring
- Voice biometrics
- Interactive voice response (IVR)

---

## Video API Capabilities

### Core Capabilities

1. **Video Rooms**
   - Create video conference rooms
   - Join/leave rooms
   - Multiple participants
   - Screen sharing

2. **Video Recording**
   - Record video sessions
   - Multiple recording formats
   - Recording composition
   - Recording storage

3. **Video Tracks**
   - Audio/video tracks
   - Track control (mute/unmute)
   - Track recording
   - Track composition

4. **Video Composition**
   - Custom layouts
   - Multiple video sources
   - Overlays and graphics
   - Background replacement

### Video API Endpoints

```
POST   /v1/Rooms
GET    /v1/Rooms
GET    /v1/Rooms/{RoomSid}
POST   /v1/Rooms/{RoomSid}
POST   /v1/Rooms/{RoomSid}/Participants
GET    /v1/Rooms/{RoomSid}/Participants
GET    /v1/Rooms/{RoomSid}/Participants/{ParticipantSid}
POST   /v1/Rooms/{RoomSid}/Participants/{ParticipantSid}
GET    /v1/Rooms/{RoomSid}/Recordings
GET    /v1/Rooms/{RoomSid}/Recordings/{RecordingSid}
```

### Advanced Features

- **Screen Sharing**: Share screen in video calls
- **Recording**: Record video sessions
- **Composition**: Custom video layouts
- **Bandwidth Control**: Adaptive bitrate
- **Network Quality**: Network quality indicators
- **Access Control**: Room access control

---

## Verify API Capabilities

### Core Capabilities

1. **Phone Verification**
   - Send verification codes via SMS
   - Send verification codes via voice
   - Verify codes
   - Check verification status

2. **Two-Factor Authentication (2FA)**
   - SMS-based 2FA
   - Voice-based 2FA
   - TOTP support
   - Push notifications

3. **Fraud Prevention**
   - Rate limiting
   - Suspicious activity detection
   - Phone number validation
   - Carrier validation

### Verify API Endpoints

```
POST   /v2/Services/{ServiceSid}/Verifications
POST   /v2/Services/{ServiceSid}/VerificationCheck
GET    /v2/Services/{ServiceSid}/Verifications/{Sid}
```

### Advanced Features

- **Multi-Channel**: SMS, voice, email, WhatsApp
- **Custom Templates**: Custom verification messages
- **Rate Limiting**: Prevent abuse
- **Fraud Detection**: Detect suspicious activity
- **Analytics**: Verification analytics

---

## Lookup API Capabilities

### Core Capabilities

1. **Phone Number Lookup**
   - Carrier information
   - Number type (mobile, landline, VoIP)
   - Country information
   - Line type information

2. **Number Formatting**
   - Format numbers in different styles
   - National format
   - International format
   - E.164 format

3. **Number Validation**
   - Validate number format
   - Check if number is valid
   - Check if number is reachable
   - Check number capabilities

### Lookup API Endpoints

```
GET    /v1/PhoneNumbers/{PhoneNumber}
```

**Query Parameters:**
- `Type`: carrier, caller-name, line-type-intelligence
- `CountryCode`: Country code for formatting

### Advanced Features

- **Carrier Lookup**: Get carrier information
- **Caller Name**: Get caller name (US only)
- **Line Type**: Determine line type (mobile, landline, etc.)
- **Number Formatting**: Format numbers automatically
- **International Support**: Works globally

---

## TaskRouter API Capabilities

### Core Capabilities

1. **Task Distribution**
   - Distribute tasks to workers
   - Skill-based routing
   - Priority-based routing
   - Time-based routing

2. **Worker Management**
   - Create/manage workers
   - Worker skills and attributes
   - Worker availability
   - Worker capacity

3. **Workflow Management**
   - Define routing workflows
   - Task queues
   - Task priorities
   - Task timeouts

4. **Activity Management**
   - Worker activities (idle, busy, offline)
   - Activity transitions
   - Activity statistics

### TaskRouter API Endpoints

```
POST   /v1/Workspaces/{WorkspaceSid}/Tasks
GET    /v1/Workspaces/{WorkspaceSid}/Tasks
GET    /v1/Workspaces/{WorkspaceSid}/Tasks/{TaskSid}
POST   /v1/Workspaces/{WorkspaceSid}/Tasks/{TaskSid}
POST   /v1/Workspaces/{WorkspaceSid}/Workers
GET    /v1/Workspaces/{WorkspaceSid}/Workers
GET    /v1/Workspaces/{WorkspaceSid}/Workers/{WorkerSid}
POST   /v1/Workspaces/{WorkspaceSid}/Workers/{WorkerSid}
POST   /v1/Workspaces/{WorkspaceSid}/Workflows
GET    /v1/Workspaces/{WorkspaceSid}/Workflows
```

### Advanced Features

- **Intelligent Routing**: AI-powered task routing
- **Multi-Channel**: Support multiple channels
- **Real-Time Updates**: Real-time task/worker updates
- **Analytics**: Task and worker analytics
- **Custom Attributes**: Custom task/worker attributes

---

## Serverless API Capabilities

### Core Capabilities

1. **Functions**
   - Deploy serverless functions
   - Runtime environments
   - Function versions
   - Function logs

2. **Assets**
   - Static asset hosting
   - Asset versions
   - Asset deployment

3. **Environments**
   - Multiple environments (dev, staging, prod)
   - Environment variables
   - Environment isolation

4. **Builds**
   - Automated builds
   - Build status
   - Build artifacts

### Serverless API Endpoints

```
POST   /v1/Services
GET    /v1/Services
GET    /v1/Services/{ServiceSid}
POST   /v1/Services/{ServiceSid}
DELETE /v1/Services/{ServiceSid}
POST   /v1/Services/{ServiceSid}/Functions
GET    /v1/Services/{ServiceSid}/Functions
POST   /v1/Services/{ServiceSid}/Assets
GET    /v1/Services/{ServiceSid}/Assets
POST   /v1/Services/{ServiceSid}/Environments
GET    /v1/Services/{ServiceSid}/Environments
POST   /v1/Services/{ServiceSid}/Builds
GET    /v1/Services/{ServiceSid}/Builds
```

### Advanced Features

- **Auto-Deploy**: Automatic deployments
- **Versioning**: Function and asset versioning
- **Environment Variables**: Secure environment variables
- **Logging**: Function execution logs
- **Monitoring**: Function performance monitoring

---

## IAM API Capabilities

### Core Capabilities

1. **Account Management**
   - Create/manage accounts
   - Subaccount management
   - Account settings
   - Account usage

2. **API Key Management**
   - Create/manage API keys
   - Key rotation
   - Key permissions
   - Key usage tracking

3. **Access Control**
   - User management
   - Role-based access control
   - Permission management
   - Access logging

### IAM API Endpoints

```
POST   /v1/Accounts
GET    /v1/Accounts
GET    /v1/Accounts/{AccountSid}
POST   /v1/Accounts/{AccountSid}
POST   /v1/Accounts/{AccountSid}/Keys
GET    /v1/Accounts/{AccountSid}/Keys
GET    /v1/Accounts/{AccountSid}/Keys/{KeySid}
POST   /v1/Accounts/{AccountSid}/Keys/{KeySid}
DELETE /v1/Accounts/{AccountSid}/Keys/{KeySid}
```

### Advanced Features

- **Subaccounts**: Isolated subaccounts
- **API Keys**: Secure API key management
- **Access Control**: Fine-grained permissions
- **Audit Logs**: Access audit logs
- **Usage Tracking**: Track API usage per key

---

## Email API Capabilities (SendGrid)

### Core Capabilities

1. **Send Emails**
   - Transactional emails
   - Marketing emails
   - Bulk emails
   - Scheduled emails

2. **Email Templates**
   - Create/manage templates
   - Dynamic content
   - Template versions
   - Template testing

3. **Email Analytics**
   - Open rates
   - Click rates
   - Bounce rates
   - Unsubscribe rates

4. **Email Validation**
   - Email address validation
   - Domain validation
   - Spam score
   - Deliverability checks

### Email API Endpoints

```
POST   /v3/mail/send
POST   /v3/templates
GET    /v3/templates
GET    /v3/templates/{TemplateId}
PATCH  /v3/templates/{TemplateId}
DELETE /v3/templates/{TemplateId}
GET    /v3/stats
```

### Advanced Features

- **Transactional Emails**: Automated emails
- **Marketing Campaigns**: Email marketing
- **Analytics**: Detailed email analytics
- **Templates**: Reusable email templates
- **Validation**: Email validation service

---

## Chat API Capabilities

### Core Capabilities

1. **Chat Channels**
   - Create/manage channels
   - Public and private channels
   - Channel members
   - Channel messages

2. **Real-Time Messaging**
   - Send/receive messages
   - Message history
   - Typing indicators
   - Read receipts

3. **User Management**
   - Create/manage users
   - User roles
   - User presence
   - User attributes

4. **Multi-Channel**
   - SMS integration
   - WhatsApp integration
   - Web chat
   - Mobile apps

### Chat API Endpoints

```
POST   /v2/Services/{ServiceSid}/Channels
GET    /v2/Services/{ServiceSid}/Channels
GET    /v2/Services/{ServiceSid}/Channels/{ChannelSid}
POST   /v2/Services/{ServiceSid}/Channels/{ChannelSid}
DELETE /v2/Services/{ServiceSid}/Channels/{ChannelSid}
POST   /v2/Services/{ServiceSid}/Channels/{ChannelSid}/Messages
GET    /v2/Services/{ServiceSid}/Channels/{ChannelSid}/Messages
POST   /v2/Services/{ServiceSid}/Users
GET    /v2/Services/{ServiceSid}/Users
```

### Advanced Features

- **Real-Time**: WebSocket-based real-time messaging
- **Multi-Channel**: Support multiple channels
- **Message History**: Persistent message history
- **User Roles**: Role-based access control
- **Presence**: User presence indicators

---

## Programmable Wireless API Capabilities

### Core Capabilities

1. **SIM Management**
   - Activate/deactivate SIMs
   - SIM configuration
   - SIM status
   - SIM usage

2. **Data Usage**
   - Monitor data usage
   - Data usage alerts
   - Usage reports
   - Usage limits

3. **Device Control**
   - Device commands
   - Device status
   - Device configuration
   - Device updates

4. **Network Management**
   - Network selection
   - Network quality
   - Network statistics
   - Network optimization

### Programmable Wireless API Endpoints

```
POST   /v1/Sims
GET    /v1/Sims
GET    /v1/Sims/{SimSid}
POST   /v1/Sims/{SimSid}
GET    /v1/Sims/{SimSid}/UsageRecords
GET    /v1/Sims/{SimSid}/DataSessions
POST   /v1/Commands
GET    /v1/Commands
```

### Advanced Features

- **SIM Management**: Full SIM lifecycle management
- **Data Monitoring**: Real-time data usage monitoring
- **Device Control**: Remote device control
- **Network Optimization**: Automatic network selection
- **Usage Alerts**: Data usage alerts

---

## API Endpoints Reference

### Base URLs

- **REST API**: `https://api.twilio.com/2010-04-01`
- **Video API**: `https://video.twilio.com/v1`
- **Verify API**: `https://verify.twilio.com/v2`
- **Lookup API**: `https://lookups.twilio.com/v1`
- **TaskRouter API**: `https://taskrouter.twilio.com/v1`
- **Serverless API**: `https://serverless.twilio.com/v1`
- **Chat API**: `https://chat.twilio.com/v2`
- **Wireless API**: `https://wireless.twilio.com/v1`

### HTTP Methods

- **GET**: Retrieve resources
- **POST**: Create resources or perform actions
- **PUT**: Update resources (full update)
- **PATCH**: Update resources (partial update)
- **DELETE**: Delete resources

### Common Query Parameters

- `PageSize`: Number of results per page (default: 50, max: 1000)
- `Page`: Page number (for pagination)
- `PageToken`: Token for pagination
- `Limit`: Maximum number of results

### Response Pagination

```json
{
  "first_page_uri": "/2010-04-01/Accounts/AC.../Calls.json?PageSize=50&Page=0",
  "next_page_uri": "/2010-04-01/Accounts/AC.../Calls.json?PageSize=50&Page=1",
  "previous_page_uri": null,
  "page": 0,
  "page_size": 50,
  "uri": "/2010-04-01/Accounts/AC.../Calls.json",
  "calls": [...]
}
```

---

## Rate Limits & Quotas

### Rate Limits

- **API Requests**: Varies by endpoint and account type
- **Default**: 100 requests per second per account
- **Burst**: Higher limits for short bursts
- **Per-Endpoint**: Some endpoints have specific limits

### Quotas

- **Concurrent Calls**: Based on account type
- **SMS Messages**: Based on account type and country
- **API Requests**: Based on account type
- **Storage**: Based on account type

### Handling Rate Limits

```python
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import time

def make_request_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Make API request
            return client.calls.create(...)
        except TwilioRestException as e:
            if e.status == 429:  # Too Many Requests
                retry_after = int(e.headers.get('Retry-After', 1))
                time.sleep(retry_after * (2 ** attempt))  # Exponential backoff
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## Pricing Overview

### Voice Calls

- **Inbound**: Varies by country ($0.0085-$0.05 per minute)
- **Outbound**: Varies by country ($0.013-$0.10 per minute)
- **Toll-Free**: Higher rates
- **Recording**: Additional cost per minute

### SMS

- **SMS**: Varies by country ($0.0075-$0.10 per message)
- **MMS**: Higher rates than SMS
- **Short Codes**: Monthly fee + per-message cost
- **Long Messages**: Multiple segments charged separately

### Phone Numbers

- **Local Numbers**: $1.00-$2.00 per month
- **Toll-Free Numbers**: $2.00-$3.00 per month
- **Short Codes**: $500-$1000 per month

### Media Streams

- **Streaming**: $0.001 per minute
- **Additional**: Based on data usage

### Video

- **Video Minutes**: $0.004 per participant-minute
- **Recording**: Additional storage costs

### Verify

- **SMS Verification**: $0.05 per verification
- **Voice Verification**: $0.05 per verification

**Note**: Pricing varies by country, account type, and usage volume. Check [Twilio Pricing](https://www.twilio.com/pricing) for current rates.

---

## Resources

### Official Documentation

- [Twilio API Documentation](https://www.twilio.com/docs)
- [API Reference](https://www.twilio.com/docs/usage/api)
- [REST API Reference](https://www.twilio.com/docs/voice/api)
- [OpenAPI Specification](https://www.twilio.com/docs/openapi)

### SDKs

- [Python SDK](https://github.com/twilio/twilio-python)
- [Node.js SDK](https://github.com/twilio/twilio-node)
- [Java SDK](https://github.com/twilio/twilio-java)
- [C# SDK](https://github.com/twilio/twilio-csharp)
- [Ruby SDK](https://github.com/twilio/twilio-ruby)
- [PHP SDK](https://github.com/twilio/twilio-php)
- [Go SDK](https://github.com/twilio/twilio-go)

### Developer Resources

- [Twilio Console](https://console.twilio.com/)
- [Twilio Support](https://support.twilio.com/)
- [Twilio Community](https://www.twilio.com/community)
- [Twilio Blog](https://www.twilio.com/blog)

---

## Summary

Twilio provides a comprehensive suite of APIs for:

- **Voice**: Calls, conferences, recordings, speech recognition
- **Messaging**: SMS, MMS, WhatsApp, RCS, Facebook Messenger
- **Video**: Video rooms, recording, composition
- **Phone Numbers**: Search, purchase, manage numbers
- **Media Streams**: Real-time bidirectional audio
- **Verify**: Phone verification and 2FA
- **Lookup**: Phone number information
- **TaskRouter**: Intelligent task routing
- **Serverless**: Functions and assets
- **IAM**: Account and access management
- **Email**: Transactional and marketing emails
- **Chat**: Real-time chat functionality
- **Wireless**: IoT device management

All APIs follow REST principles, use HTTP Basic Authentication, and return JSON responses. Rate limits and pricing vary by service and account type.

