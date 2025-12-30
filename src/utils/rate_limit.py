"""Rate limiting utilities for API endpoints"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "contacts_list": "100/minute",
    "contacts_create": "30/minute",
    "contacts_bulk": "10/minute",
    "contacts_upload": "5/minute",
    "contacts_update": "50/minute",
    "contacts_delete": "30/minute",
    "messaging_send": "20/minute",  # Limit outbound message creation
    "messaging_approve": "30/minute",  # Limit approvals
    "messaging_conversations": "100/minute",  # List conversations
    "messaging_drafts": "30/minute",  # Get drafts
    "messaging_suggestions": "30/minute",  # Get suggestions
}


def get_rate_limit(limit_name: str) -> str:
    """Get rate limit string for a given limit name"""
    return RATE_LIMITS.get(limit_name, "100/minute")

