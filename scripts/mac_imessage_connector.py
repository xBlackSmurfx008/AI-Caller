#!/usr/bin/env python3
"""
Mac iMessage Connector - Syncs iMessage/SMS history to AI Caller backend

SETUP:
1. Enable "Messages in iCloud" on iPhone (Settings → Apple ID → iCloud → Messages)
2. Enable "Messages in iCloud" on Mac (Messages → Settings → iMessage → Enable Messages in iCloud)
3. Grant Full Disk Access to Terminal/Python:
   System Settings → Privacy & Security → Full Disk Access → add Terminal.app (or your Python)
4. Set environment variables (or edit the CONFIG section below):
   export AI_CALLER_API_URL="https://your-backend.vercel.app"
   export AI_CALLER_AUTH_TOKEN="your-godfather-token"
5. Run: python3 mac_imessage_connector.py
6. For automatic runs, install the LaunchAgent (see mac_imessage_connector.plist)

NOTES:
- The connector reads ~/Library/Messages/chat.db (requires Full Disk Access)
- It tracks last-synced message using a local checkpoint file
- Deduplication is also handled server-side by message_guid
- Safe to run multiple times; only new messages are uploaded
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ======================== CONFIG ========================
# Override via environment variables or edit directly

API_URL = os.environ.get("AI_CALLER_API_URL", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("AI_CALLER_AUTH_TOKEN", "ai-caller-auth-2025-secure")

# Path to Messages database (default macOS location)
MESSAGES_DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

# Checkpoint file to track last synced message
CHECKPOINT_FILE = os.path.expanduser("~/.ai_caller_imessage_checkpoint.json")

# How far back to look on first run (days)
INITIAL_LOOKBACK_DAYS = 90

# Max messages per batch upload
BATCH_SIZE = 100

# ========================================================

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip3 install httpx")
    sys.exit(1)


def log(msg: str) -> None:
    """Simple timestamped logging."""
    print(f"[{datetime.now().isoformat()}] {msg}")


def load_checkpoint() -> Dict[str, Any]:
    """Load checkpoint (last synced ROWID and timestamp)."""
    if Path(CHECKPOINT_FILE).exists():
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log(f"Warning: Failed to load checkpoint: {e}")
    return {}


def save_checkpoint(data: Dict[str, Any]) -> None:
    """Save checkpoint."""
    try:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Warning: Failed to save checkpoint: {e}")


def apple_time_to_datetime(apple_timestamp: int) -> datetime:
    """
    Convert Apple's weird timestamp format to datetime.
    Apple uses nanoseconds since 2001-01-01 (Mac Absolute Time).
    """
    if apple_timestamp is None:
        return datetime.now()
    # Apple epoch is 2001-01-01 00:00:00 UTC
    # Convert nanoseconds to seconds
    seconds = apple_timestamp / 1_000_000_000
    apple_epoch = datetime(2001, 1, 1)
    return apple_epoch + timedelta(seconds=seconds)


def fetch_messages_since(db_path: str, since_rowid: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch messages from chat.db since a given ROWID.
    
    Returns list of message dicts with:
    - rowid, guid, text, is_from_me, date, handle_id, service, chat_identifier
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Messages database not found: {db_path}")
    
    # Connect read-only to avoid any locking issues
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query messages with handle (phone/email) and chat info
    query = """
    SELECT 
        m.ROWID as rowid,
        m.guid as guid,
        m.text as text,
        m.is_from_me as is_from_me,
        m.date as date,
        m.service as service,
        h.id as handle,
        c.chat_identifier as chat_identifier
    FROM message m
    LEFT JOIN handle h ON m.handle_id = h.ROWID
    LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    LEFT JOIN chat c ON cmj.chat_id = c.ROWID
    WHERE m.ROWID > ?
    ORDER BY m.ROWID ASC
    LIMIT ?
    """
    
    cursor.execute(query, (since_rowid, limit))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        # Skip messages without text or handle (system messages, etc.)
        if not row["text"] or not row["handle"]:
            continue
        
        msg = {
            "rowid": row["rowid"],
            "message_guid": row["guid"],
            "text": row["text"],
            "is_from_me": bool(row["is_from_me"]),
            "sent_at_iso": apple_time_to_datetime(row["date"]).isoformat() if row["date"] else None,
            "service": row["service"],
            "handle": row["handle"],
            "chat_identifier": row["chat_identifier"],
        }
        messages.append(msg)
    
    return messages


def get_initial_rowid(db_path: str, lookback_days: int) -> int:
    """Get the ROWID to start from based on lookback days."""
    if not Path(db_path).exists():
        return 0
    
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    # Calculate the Apple timestamp for N days ago
    cutoff = datetime.now() - timedelta(days=lookback_days)
    apple_epoch = datetime(2001, 1, 1)
    seconds_since_epoch = (cutoff - apple_epoch).total_seconds()
    apple_timestamp = int(seconds_since_epoch * 1_000_000_000)
    
    cursor.execute(
        "SELECT MIN(ROWID) FROM message WHERE date >= ?",
        (apple_timestamp,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        # Return one less so we include that message
        return max(0, result[0] - 1)
    return 0


def upload_batch(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upload a batch of messages to the backend."""
    url = f"{API_URL.rstrip('/')}/api/imessage/ingest"
    
    # Transform to expected format
    events = []
    for msg in messages:
        events.append({
            "message_guid": msg["message_guid"],
            "chat_identifier": msg.get("chat_identifier"),
            "handle": msg["handle"],
            "is_from_me": msg["is_from_me"],
            "text": msg["text"] or "",
            "service": msg.get("service"),
            "sent_at_iso": msg.get("sent_at_iso"),
        })
    
    payload = {
        "events": events,
        "source": "mac_connector",
        "uploaded_at_iso": datetime.utcnow().isoformat(),
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    
    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def sync_messages() -> None:
    """Main sync function."""
    log("Starting iMessage sync...")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    last_rowid = checkpoint.get("last_rowid", 0)
    
    # If first run, determine starting point
    if last_rowid == 0:
        log(f"First run - looking back {INITIAL_LOOKBACK_DAYS} days")
        last_rowid = get_initial_rowid(MESSAGES_DB_PATH, INITIAL_LOOKBACK_DAYS)
        log(f"Starting from ROWID: {last_rowid}")
    
    total_uploaded = 0
    
    while True:
        # Fetch batch
        messages = fetch_messages_since(MESSAGES_DB_PATH, last_rowid, BATCH_SIZE)
        
        if not messages:
            log("No new messages to sync")
            break
        
        log(f"Found {len(messages)} new messages (ROWID {last_rowid + 1} to {messages[-1]['rowid']})")
        
        # Upload batch
        try:
            result = upload_batch(messages)
            ingested = result.get("ingested", 0)
            skipped = result.get("skipped", 0)
            # Debug: print server response for visibility
            print(f"Server response: {result}")
            log(f"Uploaded: {ingested} ingested, {skipped} skipped")
            total_uploaded += ingested
        except httpx.HTTPStatusError as e:
            log(f"ERROR: Upload failed with status {e.response.status_code}: {e.response.text}")
            break
        except Exception as e:
            log(f"ERROR: Upload failed: {e}")
            break
        
        # Update checkpoint
        last_rowid = messages[-1]["rowid"]
        save_checkpoint({
            "last_rowid": last_rowid,
            "last_sync": datetime.utcnow().isoformat(),
            "total_synced": checkpoint.get("total_synced", 0) + len(messages),
        })
        
        # If we got fewer than BATCH_SIZE, we're caught up
        if len(messages) < BATCH_SIZE:
            break
    
    log(f"Sync complete. Total uploaded this run: {total_uploaded}")


def main() -> None:
    """Entry point."""
    # Validate config
    if not Path(MESSAGES_DB_PATH).exists():
        print(f"ERROR: Messages database not found at {MESSAGES_DB_PATH}")
        print("Make sure you have Full Disk Access enabled for Terminal/Python.")
        print("System Settings → Privacy & Security → Full Disk Access")
        sys.exit(1)
    
    if not API_URL or not AUTH_TOKEN:
        print("ERROR: AI_CALLER_API_URL and AI_CALLER_AUTH_TOKEN must be set")
        sys.exit(1)
    
    log(f"API URL: {API_URL}")
    log(f"Messages DB: {MESSAGES_DB_PATH}")
    
    try:
        sync_messages()
    except PermissionError:
        print("\nERROR: Permission denied reading Messages database.")
        print("You need to grant Full Disk Access to Terminal (or your Python interpreter):")
        print("  1. Open System Settings → Privacy & Security → Full Disk Access")
        print("  2. Click + and add Terminal.app (or the Python app you're using)")
        print("  3. Restart Terminal and try again")
        sys.exit(1)
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

