# Email Integrations Setup Guide

This guide explains how to set up Gmail and Outlook email integrations for the AI Caller system.

## Overview

The system supports two email providers:
- **Gmail** - Using Gmail API with OAuth2
- **Outlook** - Using Microsoft Graph API with OAuth2

Both integrations use OAuth2 for secure authentication and support:
- Sending emails
- Reading emails
- Listing messages
- Full email management

## Prerequisites

### Required Packages

Install the required packages:

```bash
# For Gmail
pip install google-api-python-client google-auth google-auth-oauthlib

# For Outlook
pip install msal
```

Or install all at once:
```bash
pip install -r requirements.txt
```

## Gmail Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/gmail.send` and `https://www.googleapis.com/auth/gmail.readonly`
   - Add test users (for testing before verification)
4. Create OAuth client ID:
   - Application type: "Web application"
   - Name: "AI Caller Gmail Integration"
   - Authorized redirect URIs: `http://localhost:8000/api/gmail/oauth/callback` (or your production URL)
5. Download the credentials JSON file

### Step 3: Configure Environment Variables

You have two options:

**Option A: File-based (Recommended for development)**
```bash
GMAIL_OAUTH_CLIENT_SECRETS_FILE=/path/to/credentials.json
GMAIL_OAUTH_TOKEN_FILE=secrets/gmail_token.json
```

**Option B: Inline JSON (Recommended for production)**
```bash
GMAIL_OAUTH_CLIENT_SECRETS_JSON='{"web":{"client_id":"...","client_secret":"...","auth_uri":"...","token_uri":"..."}}'
GMAIL_OAUTH_TOKEN_FILE=secrets/gmail_token.json
```

### Step 4: Connect Gmail

1. Start your application
2. Navigate to: `GET /api/gmail/oauth/start`
   - This returns an `auth_url`
3. Open the `auth_url` in your browser
4. Sign in with your Gmail account and grant permissions
5. You'll be redirected to the callback URL
6. Check connection status: `GET /api/gmail/status`

## Outlook Setup

### Step 1: Register Application in Azure

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in:
   - Name: "AI Caller Outlook Integration"
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: `http://localhost:8000/api/outlook/oauth/callback` (Web platform)
5. Click "Register"

### Step 2: Configure API Permissions

1. In your app registration, go to "API permissions"
2. Click "Add a permission" > "Microsoft Graph" > "Delegated permissions"
3. Add the following permissions:
   - `Mail.Send`
   - `Mail.Read`
4. Click "Add permissions"
5. Click "Grant admin consent" (if you have admin rights)

### Step 3: Create Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Add description and expiration
4. **Copy the secret value immediately** (you won't be able to see it again)

### Step 4: Get Application Details

Note down:
- **Application (client) ID** - from Overview page
- **Client secret value** - from Step 3
- **Directory (tenant) ID** - from Overview page (optional, can use "common")

### Step 5: Configure Environment Variables

You have two options:

**Option A: File-based (Recommended for development)**
Create a JSON file with:
```json
{
  "client_id": "your-application-id",
  "client_secret": "your-client-secret",
  "tenant": "common"
}
```

Then set:
```bash
OUTLOOK_OAUTH_CLIENT_SECRETS_FILE=/path/to/outlook-config.json
OUTLOOK_OAUTH_TOKEN_FILE=secrets/outlook_token.json
```

**Option B: Inline JSON (Recommended for production)**
```bash
OUTLOOK_OAUTH_CLIENT_SECRETS_JSON='{"client_id":"...","client_secret":"...","tenant":"common"}'
OUTLOOK_OAUTH_TOKEN_FILE=secrets/outlook_token.json
```

### Step 6: Connect Outlook

1. Start your application
2. Navigate to: `GET /api/outlook/oauth/start`
   - This returns an `auth_url`
3. Open the `auth_url` in your browser
4. Sign in with your Microsoft account and grant permissions
5. You'll be redirected to the callback URL
6. Check connection status: `GET /api/outlook/status`

## API Endpoints

### Gmail Endpoints

- `GET /api/gmail/status` - Check connection status
- `GET /api/gmail/oauth/start` - Start OAuth flow
- `GET /api/gmail/oauth/callback` - OAuth callback (automatic)
- `POST /api/gmail/send` - Send email
- `GET /api/gmail/messages` - List messages
- `GET /api/gmail/messages/{message_id}` - Get specific message

### Outlook Endpoints

- `GET /api/outlook/status` - Check connection status
- `GET /api/outlook/oauth/start` - Start OAuth flow
- `GET /api/outlook/oauth/callback` - OAuth callback (automatic)
- `POST /api/outlook/send` - Send email
- `GET /api/outlook/messages` - List messages
- `GET /api/outlook/messages/{message_id}` - Get specific message

## Usage Examples

### Send Email via Gmail

```bash
curl -X POST http://localhost:8000/api/gmail/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email",
    "body_html": "<p>This is a test email</p>"
  }'
```

### Send Email via Outlook

```bash
curl -X POST http://localhost:8000/api/outlook/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email",
    "body_html": "<p>This is a test email</p>"
  }'
```

### List Gmail Messages

```bash
curl "http://localhost:8000/api/gmail/messages?query=from:example@gmail.com&max_results=10"
```

### List Outlook Messages

```bash
curl "http://localhost:8000/api/outlook/messages?top=10&skip=0"
```

## Integration Status

Check integration status via the health endpoint:

```bash
curl http://localhost:8000/api/health/integrations
```

This will show the status of both Gmail and Outlook integrations:
- `connected` - OAuth completed and token valid
- `disconnected` - OAuth not completed or token expired
- `not_configured` - OAuth credentials not provided
- `error` - Configuration or connection error

## Troubleshooting

### Gmail Issues

**"Missing Gmail OAuth client secrets"**
- Ensure `GMAIL_OAUTH_CLIENT_SECRETS_FILE` or `GMAIL_OAUTH_CLIENT_SECRETS_JSON` is set
- Verify the JSON file is valid

**"Gmail OAuth not completed"**
- Complete the OAuth flow by visiting `/api/gmail/oauth/start`
- Ensure redirect URI matches what's configured in Google Cloud Console

**"Gmail token is invalid"**
- Delete `secrets/gmail_token.json` and reconnect
- Tokens may expire; the system will attempt to refresh automatically

### Outlook Issues

**"Missing Outlook OAuth client secrets"**
- Ensure `OUTLOOK_OAUTH_CLIENT_SECRETS_FILE` or `OUTLOOK_OAUTH_CLIENT_SECRETS_JSON` is set
- Verify the JSON contains `client_id`, `client_secret`, and optionally `tenant`

**"Outlook OAuth not completed"**
- Complete the OAuth flow by visiting `/api/outlook/oauth/start`
- Ensure redirect URI matches what's configured in Azure Portal

**"Outlook token is invalid"**
- Delete `secrets/outlook_token.json` and reconnect
- Tokens may expire; the system will attempt to refresh automatically

**"Missing client_id/appId" or "Missing client_secret/password"**
- Verify your config JSON has the correct field names
- Use `client_id` and `client_secret` (or `appId` and `password`)

## Security Notes

1. **Never commit token files** - The `secrets/` directory should be in `.gitignore`
2. **Use environment variables** - For production, use environment variables or secrets management
3. **Rotate secrets** - Regularly rotate OAuth client secrets
4. **Limit scopes** - Only request the minimum required permissions
5. **HTTPS in production** - Always use HTTPS for OAuth redirect URIs in production

## Production Deployment

For production:

1. Update redirect URIs in both Google Cloud Console and Azure Portal to your production URL
2. Use environment variables or secrets management for credentials
3. Ensure `secrets/` directory is writable by your application
4. Set up proper logging and monitoring for OAuth flows
5. Consider implementing token refresh monitoring

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/overview)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform Documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/)

