# Messaging User Guide

## Overview

The Messaging system provides a unified inbox for SMS, MMS, and WhatsApp messages through Twilio integration. All messages are automatically ingested into the memory system for relationship tracking and AI-powered suggestions.

## Features

### Unified Inbox
- View all conversations across SMS, MMS, and WhatsApp in one place
- Conversations grouped by contact and channel
- Unread message tracking
- Real-time updates (polling every 30 seconds)

### Message Composition
- Compose messages manually or use AI-generated drafts
- Support for SMS and WhatsApp channels
- Approval workflow for outbound messages (safety feature)
- Media support (MMS)

### AI-Powered Features
- **Message Drafts**: AI generates personalized message drafts based on contact memory
- **Channel Recommendations**: AI suggests best channel (SMS vs WhatsApp) based on context
- **Tone Guidance**: AI provides tone recommendations for messages
- **Risk Flags**: AI identifies potential risks before sending

### Memory Integration
- All conversations automatically summarized
- Contact memory updated with each interaction
- Sentiment tracking
- Action items and commitments extracted

## Getting Started

### 1. Configure Twilio

1. Set up Twilio account and get credentials
2. Configure environment variables:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `TWILIO_WEBHOOK_URL` (your deployed URL)

3. Configure webhooks in Twilio Console:
   - **Inbound Messages**: `POST https://your-domain.com/webhooks/twilio/inbound-message`
   - **Status Callbacks**: `POST https://your-domain.com/webhooks/twilio/message-status`

4. (Optional) Enable WhatsApp in Twilio Console

### 2. Access Messaging

Navigate to **Inbox** in the main navigation to view your unified inbox.

## Using the Inbox

### Viewing Conversations

1. Click **Inbox** in navigation
2. See list of all conversations on the left
3. Unread count badge shows number of unread messages
4. Click a conversation to view messages

### Reading Messages

- Messages are displayed in chronological order
- Inbound messages (from contacts) on the left
- Outbound messages (from you) on the right
- Timestamps shown for each message
- Media attachments shown as links

### Marking as Read

- Conversations are automatically marked as read when opened
- Or manually mark via the conversation view

## Sending Messages

### Method 1: AI-Generated Drafts

1. Select a conversation
2. Click **Compose**
3. View AI-generated drafts (if available)
4. Review draft, rationale, and risk flags
5. Click **Use This Draft**
6. Approve the message when prompted
7. Message is sent

### Method 2: Manual Composition

1. Select a conversation
2. Click **Compose**
3. Choose channel (SMS or WhatsApp)
4. Type your message
5. Click **Create Draft**
6. Approve the message when prompted
7. Message is sent

### Approval Workflow

**All outbound messages require approval** (safety feature):

1. After creating a draft, message status shows "Pending approval"
2. Click **✓** to approve and send
3. Click **✗** to reject
4. Once approved, message is sent via Twilio
5. Status updates: Pending → Sent → Delivered

## Understanding Message Status

- **Pending**: Draft created, awaiting approval
- **Sent**: Message sent to Twilio, in transit
- **Delivered**: Message delivered to recipient
- **Failed**: Message failed to send (check error details)

## AI Features Explained

### Message Drafts

AI generates drafts based on:
- Contact's memory and relationship history
- Active projects and goals
- Outstanding actions and commitments
- Sentiment trends
- Known preferences

### Channel Recommendations

AI recommends channel based on:
- Contact preferences (if known)
- Relationship formality
- Message urgency
- Channel reliability

### Risk Flags

AI identifies potential risks:
- Over-asking (too many requests)
- Sensitive topics
- Timing concerns
- Relationship status

## Best Practices

1. **Review AI Drafts**: Always review AI-generated drafts before sending
2. **Check Risk Flags**: Pay attention to risk warnings
3. **Use Appropriate Channel**: Follow AI channel recommendations
4. **Approve Carefully**: Review message before approving
5. **Monitor Status**: Check message delivery status

## Troubleshooting

### Messages Not Appearing

- Check Twilio webhook configuration
- Verify webhook URL is accessible
- Check server logs for errors

### Messages Not Sending

- Verify Twilio credentials
- Check phone number format (E.164)
- Ensure contact has valid phone number
- Check Twilio account balance

### Approval Not Working

- Verify message is in "pending" status
- Check network connection
- Review server logs for errors

## API Reference

### Endpoints

- `GET /api/messaging/conversations` - List all conversations
- `GET /api/messaging/conversations/{contact_id}/{channel}` - Get conversation messages
- `POST /api/messaging/send` - Create message draft
- `POST /api/messaging/approve` - Approve/reject message
- `GET /api/messaging/drafts/{contact_id}` - Get AI drafts
- `GET /api/messaging/suggestions/{contact_id}` - Get messaging suggestions
- `POST /api/messaging/conversations/{contact_id}/{channel}/read` - Mark as read

### Rate Limits

- Send: 20 requests/minute
- Approve: 30 requests/minute
- Conversations: 100 requests/minute
- Drafts: 30 requests/minute
- Suggestions: 30 requests/minute

## Security

- All webhooks validate Twilio signatures
- Outbound messages require explicit approval
- Do-not-message flag prevents sending to restricted contacts
- All actions logged for audit

## Support

For issues or questions:
1. Check server logs
2. Verify Twilio configuration
3. Review error messages in UI
4. Check API documentation at `/docs`

