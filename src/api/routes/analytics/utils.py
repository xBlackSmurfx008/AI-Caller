"""Utility functions for analytics routes"""

from typing import Optional
from datetime import datetime, timedelta


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def get_date_range(from_date: Optional[str], to_date: Optional[str], default_days: int = 7) -> tuple[datetime, datetime]:
    """Get date range with defaults"""
    if to_date:
        end = parse_date(to_date)
    else:
        end = datetime.utcnow()
    
    if from_date:
        start = parse_date(from_date)
    else:
        start = end - timedelta(days=default_days)
    
    return start, end

