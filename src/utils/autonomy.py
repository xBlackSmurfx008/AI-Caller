"""Runtime autonomy settings helpers (DB overrides)."""

from __future__ import annotations

from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from src.database.models import AIAutonomyConfig
from src.utils.config import get_settings


def get_autonomy_config(db: Session) -> Optional[AIAutonomyConfig]:
    """Return the most recently updated autonomy config, if present."""
    return db.query(AIAutonomyConfig).order_by(AIAutonomyConfig.updated_at.desc()).first()


def get_auto_execute_high_risk(db: Session) -> bool:
    """
    Returns whether to auto-execute high-risk actions.

    Priority:
    - DB override if present
    - env setting fallback (AUTO_EXECUTE_HIGH_RISK)
    """
    cfg = get_autonomy_config(db)
    if cfg is not None and cfg.auto_execute_high_risk is not None:
        return bool(cfg.auto_execute_high_risk)
    return bool(getattr(get_settings(), "AUTO_EXECUTE_HIGH_RISK", True))


def config_to_dict(cfg: AIAutonomyConfig) -> Dict[str, Any]:
    return {
        "id": cfg.id,
        "level": cfg.level,
        "auto_execute_high_risk": bool(cfg.auto_execute_high_risk),
        "settings": cfg.settings or {},
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


