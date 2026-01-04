# iMessage Connector Setup Guide

This guide explains how to set up the Mac iMessage Connector so your AI Orchestrator can learn from your iMessage/SMS history.

## Overview

The connector runs on your Mac, reads your local Messages database (`~/Library/Messages/chat.db`), and uploads new messages to your AI Caller backend. The Orchestrator then uses this data to:

- Understand your communication patterns
- Track conversation threads and sentiment
- Detect commitments and follow-up opportunities
- Generate better relationship recommendations

## Prerequisites

1. **Mac that stays on** (or is on frequently) - this is where the connector runs
2. **Same Apple ID** on iPhone and Mac
3. **Messages in iCloud** enabled on both devices
4. **Full Disk Access** granted to Terminal/Python
5. **Python 3.8+** with `httpx` installed

## Step 1: Enable Messages in iCloud

### On iPhone:
1. Settings → [Your Name] → iCloud → Show All
2. Toggle **Messages** ON
3. Wait for initial sync to complete (may take a while)

### On Mac:
1. Open **Messages** app
2. Messages menu → **Settings** (or Preferences)
3. Go to **iMessage** tab
4. Check **Enable Messages in iCloud**
5. Click **Sync Now** to force initial sync

### Verify Sync:
- Send a test message from iPhone
- Check that it appears on Mac within a few minutes
- If not syncing, try: Messages → Settings → iMessage → Sync Now

## Step 2: Grant Full Disk Access

The connector needs to read `~/Library/Messages/chat.db`, which requires Full Disk Access.

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Privacy & Security** → **Full Disk Access**
3. Click the **+** button
4. Add **Terminal.app** (or your preferred terminal app)
5. If using a custom Python (e.g., Homebrew), also add that Python executable
6. **Restart Terminal** after granting access

### Test Access:
```bash
# This should work without "Operation not permitted" error
sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message;"
```

## Step 3: Install Dependencies

```bash
pip3 install httpx
```

## Step 4: Configure the Connector

Edit `scripts/mac_imessage_connector.py` and update the CONFIG section, or set environment variables:

```bash
# Your backend URL (local dev or Vercel)
export AI_CALLER_API_URL="https://your-app.vercel.app"

# Your auth token (from env.example or GODFATHER_API_TOKEN)
export AI_CALLER_AUTH_TOKEN="your-secret-token"
```

## Step 5: Test Manual Run

```bash
cd /path/to/AI\ Caller
python3 scripts/mac_imessage_connector.py
```

You should see output like:
```
[2025-01-03T14:30:00] Starting iMessage sync...
[2025-01-03T14:30:00] First run - looking back 30 days
[2025-01-03T14:30:00] Starting from ROWID: 12345
[2025-01-03T14:30:01] Found 50 new messages (ROWID 12346 to 12395)
[2025-01-03T14:30:02] Uploaded: 48 ingested, 2 skipped
[2025-01-03T14:30:02] Sync complete. Total uploaded this run: 48
```

## Step 6: Set Up Automatic Runs (LaunchAgent)

For the Orchestrator to always have fresh data, the connector should run regularly. We provide a LaunchAgent template.

### Install the LaunchAgent:

1. Edit `scripts/com.aicaller.imessage-connector.plist`:
   - Replace `YOUR_USERNAME` with your actual macOS username
   - Update `AI_CALLER_API_URL` to your backend URL
   - Update `AI_CALLER_AUTH_TOKEN` to your token

2. Copy to LaunchAgents folder:
   ```bash
   cp scripts/com.aicaller.imessage-connector.plist ~/Library/LaunchAgents/
   ```

3. Load the agent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.aicaller.imessage-connector.plist
   ```

4. Verify it's running:
   ```bash
   launchctl list | grep imessage
   # Should show: - 0 com.aicaller.imessage-connector
   ```

### Check Logs:
```bash
tail -f /tmp/imessage-connector.log
tail -f /tmp/imessage-connector.err
```

### Stop/Restart:
```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.aicaller.imessage-connector.plist

# Start
launchctl load ~/Library/LaunchAgents/com.aicaller.imessage-connector.plist
```

## Step 7: Verify Data in Backend

After the connector runs, you can verify data was ingested:

```bash
# Check interactions via API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-app.vercel.app/api/memory/interactions?channel=imessage&limit=5"
```

## Troubleshooting

### "Permission denied" or "Operation not permitted"
- Full Disk Access not granted or Terminal not restarted
- Solution: Re-add Terminal to Full Disk Access, then restart Terminal

### "Messages database not found"
- Messages not enabled or chat.db doesn't exist yet
- Solution: Open Messages app, send/receive a message, then check again

### "Connection refused" or "401 Unauthorized"
- Backend not running or wrong token
- Solution: Verify `AI_CALLER_API_URL` and `AI_CALLER_AUTH_TOKEN`

### Messages not syncing from iPhone
1. On iPhone: Settings → Messages → Text Message Forwarding → Enable for your Mac
2. On Mac: Messages → Settings → iMessage → Enable Messages in iCloud → Sync Now
3. Make sure both devices are on the same Apple ID
4. Check iCloud status at apple.com/support/systemstatus

### Connector runs but 0 messages uploaded
- All messages may already be synced (check checkpoint file)
- Reset checkpoint: `rm ~/.ai_caller_imessage_checkpoint.json`

## How It Works

1. **Connector reads** `~/Library/Messages/chat.db` (SQLite database)
2. **Tracks progress** using a local checkpoint file (last ROWID synced)
3. **Uploads batches** to `/api/imessage/ingest` endpoint
4. **Backend stores** as `Interaction` records (channel = "imessage")
5. **Deduplication** happens both client-side (ROWID checkpoint) and server-side (message_guid)
6. **Orchestrator** uses interactions during 4x/day runs to update contact memory

## Security Notes

- The connector only reads message content, not attachments
- Data is transmitted over HTTPS to your backend
- Auth token should be kept secret (use environment variables, not hardcoded)
- The local checkpoint file contains no message content, just sync state

## SMS vs iMessage

- **iMessage** (blue bubbles): Syncs automatically via Messages in iCloud
- **SMS** (green bubbles): Requires **Text Message Forwarding** enabled on iPhone:
  - Settings → Messages → Text Message Forwarding → Toggle ON for your Mac

Both types appear in the same `chat.db` database once synced.

