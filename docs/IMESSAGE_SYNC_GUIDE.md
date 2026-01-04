## iMessage Sync Playbook (90-day refresh)

Use this when you want to ingest recent iMessages/SMS into AI Caller.

### Prereqs
- Mac signed into the same Apple ID as your iPhone.
- Messages in iCloud enabled on iPhone + Mac.
- Full Disk Access granted to Terminal (or Cursor) so `chat.db` can be read.
- Connector file: `scripts/mac_imessage_connector.py`
- Auth + URL:
  - `AI_CALLER_API_URL` (e.g., `https://ai-caller-ten.vercel.app`)
  - `AI_CALLER_AUTH_TOKEN` (Godfather token)

### One-time FDA check
1) System Settings → Privacy & Security → Full Disk Access  
2) Add Terminal.app (or Cursor.app) → Quit and reopen the app.
3) Verify access:
   ```bash
   sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message LIMIT 1;"
   ```

### Reset checkpoint to resync last ~90 days
`ROWID` 0 will pull everything; for ~90 days you can start near the low ROWIDs seen in the DB (e.g., 5–10), but 0 is safest.
```bash
cat > ~/.ai_caller_imessage_checkpoint.json <<'EOF'
{
  "last_rowid": 0,
  "last_sync": "1970-01-01T00:00:00.000000",
  "total_synced": 0
}
EOF
```

### Run the connector (hosted API)
```bash
cd "/Users/mr.008/Desktop/Projects/AI Caller"
export AI_CALLER_API_URL="https://ai-caller-ten.vercel.app"
export AI_CALLER_AUTH_TOKEN="ai-caller-auth-2025-secure"
./venv/bin/python3 scripts/mac_imessage_connector.py
```

If you have a lot of backlog, re-run until it says “No new messages to sync”.

### Run against local API (for debugging)
```bash
export AI_CALLER_API_URL="http://localhost:8000"
./venv/bin/python3 scripts/mac_imessage_connector.py
```

### Troubleshooting
- If you see `authorization denied` on `chat.db`: FDA not applied to the app you’re using; add it and restart the app.
- If uploads return `skipped`: check server logs; ensure the `meta_data` field matches the Interaction model (already fixed).
- Slow first run: large `chat.db` is normal; let it finish.

