"""Email integration module for Gmail and Outlook"""

from src.email.gmail import (
    is_gmail_connected,
    start_gmail_oauth,
    finish_gmail_oauth,
    send_gmail_message,
    list_gmail_messages,
    get_gmail_message
)

from src.email.outlook import (
    is_outlook_connected,
    start_outlook_oauth,
    finish_outlook_oauth,
    send_outlook_message,
    list_outlook_messages,
    get_outlook_message
)

__all__ = [
    "is_gmail_connected",
    "start_gmail_oauth",
    "finish_gmail_oauth",
    "send_gmail_message",
    "list_gmail_messages",
    "get_gmail_message",
    "is_outlook_connected",
    "start_outlook_oauth",
    "finish_outlook_oauth",
    "send_outlook_message",
    "list_outlook_messages",
    "get_outlook_message",
]

