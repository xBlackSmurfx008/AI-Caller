"""Small persistent store for Godfather identity (in gitignored secrets/)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


DEFAULT_PATH = "secrets/godfather.json"


@dataclass
class GodfatherIdentity:
    phone_numbers_csv: str = ""
    email: str = ""


def load_identity(path: str = DEFAULT_PATH) -> GodfatherIdentity:
    if not os.path.exists(path):
        return GodfatherIdentity()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GodfatherIdentity(
            phone_numbers_csv=str(data.get("phone_numbers_csv") or ""),
            email=str(data.get("email") or ""),
        )
    except Exception as e:
        logger.error("godfather_identity_load_failed", error=str(e))
        return GodfatherIdentity()


def save_identity(identity: GodfatherIdentity, path: str = DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"phone_numbers_csv": identity.phone_numbers_csv, "email": identity.email},
            f,
            indent=2,
        )


