#!/usr/bin/env python
"""
Neon smoke test: DB sanity checks + optional API calls.

Usage (DB only):
  APP_ENV=production DATABASE_URL=postgresql://...sslmode=require \\
    python scripts/neon_smoke.py

Usage (DB + API):
  APP_ENV=production DATABASE_URL=... BASE_URL=https://your-app.vercel.app \\
    GODFATHER_API_TOKEN=... X_USER_ID=smoke_user \\
    python scripts/neon_smoke.py
"""

import os
import sys
import uuid
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.database import models as m
from src.database.database import Base

try:
    import requests
except Exception:
    requests = None


DATABASE_URL = os.getenv("DATABASE_URL")
BASE_URL = os.getenv("BASE_URL")  # Optional, enables API checks
X_USER_ID = os.getenv("X_USER_ID", "smoke_user")
API_TOKEN = os.getenv("GODFATHER_API_TOKEN")


def get_session():
    if not DATABASE_URL:
        sys.exit("DATABASE_URL env var is required.")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return Session()


def db_sanity() -> Dict[str, int]:
    """Return row counts for key tables."""
    db = get_session()
    try:
        counts = {
            "contacts": db.query(m.Contact).count(),
            "messages": db.query(m.Message).count(),
            "projects": db.query(m.Project).count(),
            "project_tasks": db.query(m.ProjectTask).count(),
            "cost_events": db.query(m.CostEvent).count(),
            "budgets": db.query(m.Budget).count(),
        }
        sample_contact = db.query(m.Contact).first()
        print("DB counts:", counts)
        if sample_contact:
            print(f"Sample contact: {sample_contact.name} ({sample_contact.id})")
        else:
            print("No contacts found.")
        return counts
    except SQLAlchemyError as err:
        print(f"DB sanity failed: {err}", file=sys.stderr)
        raise
    finally:
        db.close()


def api_call(method: str, path: str, json_body: Optional[dict] = None):
    if not BASE_URL:
        return {"skipped": True}
    if not requests:
        print("requests not installed; API checks skipped.")
        return {"skipped": True}

    url = BASE_URL.rstrip("/") + path
    headers = {"X-User-ID": X_USER_ID}
    if API_TOKEN:
        headers["X-Godfather-Token"] = API_TOKEN

    try:
        resp = requests.request(
            method,
            url,
            json=json_body,
            headers=headers,
            timeout=10,
        )
        print(f"{method} {path} -> {resp.status_code}")
        return {"status": resp.status_code, "body": resp.text}
    except Exception as err:
        print(f"{method} {path} failed: {err}", file=sys.stderr)
        return {"error": str(err)}


def api_smoke():
    """Minimal API checks (non-destructive, aside from a single test contact)."""
    if not BASE_URL:
        print("API checks skipped (set BASE_URL to enable).")
        return

    api_call("GET", "/health")

    # Create a unique contact to verify DB writes through API
    contact_name = f"Smoke Contact {uuid.uuid4().hex[:8]}"
    api_call(
        "POST",
        "/api/contacts/",
        json_body={"name": contact_name, "phone_number": "+15551234567"},
    )
    api_call("GET", "/api/contacts/?search=Smoke")
    api_call("GET", "/api/projects/")
    api_call("GET", "/api/cost/summary")


def main():
    db_sanity()
    api_smoke()
    print("Smoke checks complete.")


if __name__ == "__main__":
    main()

