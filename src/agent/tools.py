"""Tools for the AI agent to execute tasks (side effects live here)."""

from typing import Dict, Any, Optional
from src.telephony.twilio_client import TwilioService
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.errors import TelephonyError, TaskError
from src.tools.web_research import web_research
# Calendar imports are lazy so the app can start without Google deps installed.

logger = get_logger(__name__)
settings = get_settings()
twilio_service = TwilioService()


async def make_call(
    to_number: str,
    message: Optional[str] = None,
    from_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make a phone call to a number.
    
    Args:
        to_number: Phone number to call (E.164 format, e.g., +1234567890)
        message: Optional message to say during the call
        from_number: Optional number to call from (defaults to configured Twilio number)
    
    Returns:
        Dictionary with call information including call_sid and status
    """
    try:
        logger.info("making_call", to_number=to_number, message=message)
        
        # Validate phone number
        if not twilio_service.validate_phone_number(to_number):
            raise TaskError(f"Invalid phone number format: {to_number}")
        
        # Initiate call
        result = twilio_service.initiate_call(
            to_number=to_number,
            from_number=from_number,
        )
        
        logger.info("call_initiated", call_sid=result.get("call_sid"), to_number=to_number)
        return {
            "success": True,
            "call_sid": result.get("call_sid"),
            "status": result.get("status"),
            "to": result.get("to"),
            "from": result.get("from"),
        }
    except Exception as e:
        logger.error("make_call_error", error=str(e), to_number=to_number)
        raise TaskError(f"Failed to make call: {str(e)}") from e


async def send_sms(
    to_number: str,
    message: str,
    from_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an SMS text message.
    
    Args:
        to_number: Phone number to send to (E.164 format)
        message: Message content
        from_number: Optional number to send from (defaults to configured Twilio number)
    
    Returns:
        Dictionary with message information including message_sid
    """
    try:
        logger.info("sending_sms", to_number=to_number, message_length=len(message))
        
        # Validate phone number
        if not twilio_service.validate_phone_number(to_number):
            raise TaskError(f"Invalid phone number format: {to_number}")
        
        from_number = from_number or twilio_service.phone_number
        
        # Send SMS via Twilio
        from twilio.rest import Client as TwilioClient
        from src.utils.config import get_settings
        settings = get_settings()
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message_obj = client.messages.create(
            to=to_number,
            from_=from_number,
            body=message
        )
        
        # Log cost event (if db available from context)
        # Note: We'll need to pass db through context or use a different approach
        # For now, cost logging will happen at the messaging service level
        try:
            from src.cost.cost_event_logger import CostEventLogger
            from src.database.database import SessionLocal
            db = SessionLocal()
            try:
                cost_logger = CostEventLogger()
                # Calculate segments (SMS is ~160 chars per segment)
                segments = (len(message) + 159) // 160
                cost_logger.log_cost_event(
                    db=db,
                    provider="twilio",
                    service="sms",
                    metric_type="messages",
                    units=segments,
                    event_id=message_obj.sid,
                    metadata={
                        "message_sid": message_obj.sid,
                        "to_number": to_number,
                        "from_number": from_number,
                        "segments": segments,
                        "message_length": len(message)
                    }
                )
            finally:
                db.close()
        except Exception as cost_error:
            logger.warning("cost_logging_failed", error=str(cost_error))
        
        logger.info("sms_sent", message_sid=message_obj.sid, to_number=to_number)
        return {
            "success": True,
            "message_sid": message_obj.sid,
            "status": message_obj.status,
            "to": message_obj.to,
            "from": message_obj.from_,
        }
    except Exception as e:
        logger.error("send_sms_error", error=str(e), to_number=to_number)
        raise TaskError(f"Failed to send SMS: {str(e)}") from e


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    provider: Optional[str] = None,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Send an email message. Tries Gmail first, then Outlook, then SMTP fallback.
    
    Args:
        to_email: Email address to send to
        subject: Email subject
        body: Email body content
        from_email: Optional sender email (defaults to configured email)
        provider: Optional provider preference ("gmail", "outlook", or "smtp")
        cc: Optional list of CC email addresses
        bcc: Optional list of BCC email addresses
    
    Returns:
        Dictionary with email send status
    """
    try:
        logger.info("sending_email", to_email=to_email, subject=subject, provider=provider)
        
        # Try Gmail if available and not explicitly requesting another provider
        if provider is None or provider.lower() == "gmail":
            try:
                from src.email.gmail import send_gmail_message, is_gmail_connected
                if is_gmail_connected():
                    result = send_gmail_message(
                        to=to_email,
                        subject=subject,
                        body=body,
                        cc=cc,
                        bcc=bcc
                    )
                    logger.info("email_sent_via_gmail", to_email=to_email, message_id=result.get("id"))
                    email_result = {
                        "success": True,
                        "provider": "gmail",
                        "to": to_email,
                        "subject": subject,
                        "message_id": result.get("id"),
                        "thread_id": result.get("threadId")
                    }
                    
                    # Capture email interaction in memory system
                    try:
                        from src.memory.interaction_capture import capture_email_interaction
                        from src.database.database import SessionLocal
                        db = SessionLocal()
                        try:
                            await capture_email_interaction(db, to_email, subject, body)
                        finally:
                            db.close()
                    except Exception as memory_error:
                        logger.warning("email_memory_capture_failed", error=str(memory_error), to_email=to_email)
                    
                    # Log cost event
                    try:
                        from src.cost.cost_event_logger import CostEventLogger
                        from src.database.database import SessionLocal
                        db = SessionLocal()
                        try:
                            cost_logger = CostEventLogger()
                            # Gmail API is free for basic usage, but log for tracking
                            cost_logger.log_cost_event(
                                db=db,
                                provider="gmail",
                                service="email",
                                metric_type="messages",
                                units=1,
                                event_id=result.get("id"),
                                metadata={
                                    "to_email": to_email,
                                    "subject": subject,
                                    "provider": "gmail",
                                    "message_id": result.get("id"),
                                    "thread_id": result.get("threadId")
                                }
                            )
                        finally:
                            db.close()
                    except Exception as cost_error:
                        logger.warning("email_cost_logging_failed", error=str(cost_error))
                    
                    return email_result
            except Exception as e:
                logger.warning("gmail_send_failed", error=str(e))
                if provider == "gmail":
                    raise TaskError(f"Failed to send email via Gmail: {str(e)}") from e
        
        # Try Outlook if available and not explicitly requesting SMTP
        if provider is None or provider.lower() == "outlook":
            try:
                from src.email.outlook import send_outlook_message, is_outlook_connected
                if is_outlook_connected():
                    result = send_outlook_message(
                        to=to_email,
                        subject=subject,
                        body=body,
                        cc=cc,
                        bcc=bcc
                    )
                    logger.info("email_sent_via_outlook", to_email=to_email)
                    email_result = {
                        "success": True,
                        "provider": "outlook",
                        "to": to_email,
                        "subject": subject,
                        **result
                    }
                    
                    # Capture email interaction in memory system
                    try:
                        from src.memory.interaction_capture import capture_email_interaction
                        from src.database.database import SessionLocal
                        db = SessionLocal()
                        try:
                            await capture_email_interaction(db, to_email, subject, body)
                        finally:
                            db.close()
                    except Exception as memory_error:
                        logger.warning("email_memory_capture_failed", error=str(memory_error), to_email=to_email)
                    
                    # Log cost event
                    try:
                        from src.cost.cost_event_logger import CostEventLogger
                        from src.database.database import SessionLocal
                        db = SessionLocal()
                        try:
                            cost_logger = CostEventLogger()
                            # Microsoft Graph API is free for basic usage, but log for tracking
                            cost_logger.log_cost_event(
                                db=db,
                                provider="outlook",
                                service="email",
                                metric_type="messages",
                                units=1,
                                metadata={
                                    "to_email": to_email,
                                    "subject": subject,
                                    "provider": "outlook"
                                }
                            )
                        finally:
                            db.close()
                    except Exception as cost_error:
                        logger.warning("email_cost_logging_failed", error=str(cost_error))
                    
                    return email_result
            except Exception as e:
                logger.warning("outlook_send_failed", error=str(e))
                if provider == "outlook":
                    raise TaskError(f"Failed to send email via Outlook: {str(e)}") from e
        
        # Fallback to SMTP
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            raise TaskError("No email provider available. Please connect Gmail or Outlook, or configure SMTP.")
        
        from_email = from_email or settings.SMTP_FROM_EMAIL
        if not from_email:
            raise TaskError("SMTP_FROM_EMAIL not configured")
        
        # Send email using SMTP
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = ", ".join(cc)
        if bcc:
            msg['Bcc'] = ", ".join(bcc)
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        recipients = [to_email]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        server.sendmail(from_email, recipients, msg.as_string())
        server.quit()
        
        logger.info("email_sent_via_smtp", to_email=to_email, subject=subject)
        result = {
            "success": True,
            "provider": "smtp",
            "to": to_email,
            "from": from_email,
            "subject": subject,
        }
        
        # Capture email interaction in memory system
        try:
            from src.memory.interaction_capture import capture_email_interaction
            from src.database.database import SessionLocal
            db = SessionLocal()
            try:
                await capture_email_interaction(db, to_email, subject, body)
            finally:
                db.close()
        except Exception as memory_error:
            logger.warning("email_memory_capture_failed", error=str(memory_error), to_email=to_email)
        
        # Log cost event
        try:
            from src.cost.cost_event_logger import CostEventLogger
            from src.database.database import SessionLocal
            db = SessionLocal()
            try:
                cost_logger = CostEventLogger()
                # Estimate email cost (SMTP is typically free, but log for tracking)
                cost_logger.log_cost_event(
                    db=db,
                    provider="smtp",
                    service="email",
                    metric_type="messages",
                    units=1,
                    metadata={
                        "to_email": to_email,
                        "from_email": from_email,
                        "subject": subject,
                        "provider": "smtp"
                    }
                )
            finally:
                db.close()
        except Exception as cost_error:
            logger.warning("email_cost_logging_failed", error=str(cost_error))
        
        return result
    except Exception as e:
        logger.error("send_email_error", error=str(e), to_email=to_email)
        raise TaskError(f"Failed to send email: {str(e)}") from e


async def web_research_tool(url: str, allow_hosts_csv: Optional[str] = None) -> Dict[str, Any]:
    """Fetch allowlisted URL text for research/summarization (read-only)."""
    try:
        return await web_research(url=url, allow_hosts_csv=allow_hosts_csv)
    except Exception as e:
        logger.error("web_research_error", error=str(e), url=url)
        raise TaskError(f"Failed to research url: {str(e)}") from e


async def calendar_create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
    attendees_emails: Optional[list[str]] = None,
    timezone: str = "UTC",
    add_google_meet: bool = True,
) -> Dict[str, Any]:
    """Create a Google Calendar event and return link/meet info."""
    try:
        from src.calendar.google_calendar import create_event, is_connected

        if not is_connected():
            raise TaskError("Google Calendar not connected. Please connect it in the UI first.")
        ev = create_event(
            summary=summary,
            start_iso=start_iso,
            end_iso=end_iso,
            description=description,
            location=location,
            attendees_emails=attendees_emails,
            timezone_str=timezone,
            add_google_meet=add_google_meet,
        )
        return {"success": True, "event_id": ev.get("id"), "link": ev.get("htmlLink"), "meet": ev.get("hangoutLink")}
    except Exception as e:
        logger.error("calendar_create_error", error=str(e))
        raise TaskError(f"Failed to create calendar event: {str(e)}") from e


async def calendar_list_upcoming(limit: int = 10) -> Dict[str, Any]:
    """List upcoming events."""
    try:
        from src.calendar.google_calendar import list_upcoming, is_connected

        if not is_connected():
            raise TaskError("Google Calendar not connected. Please connect it in the UI first.")
        return {"success": True, "events": list_upcoming(max_results=limit)}
    except Exception as e:
        logger.error("calendar_list_error", error=str(e))
        raise TaskError(f"Failed to list events: {str(e)}") from e


async def read_email(
    provider: str,
    message_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Read emails from Gmail or Outlook. Can read a specific message or list/search messages.
    
    Args:
        provider: Email provider ("gmail" or "outlook")
        message_id: Optional specific message ID to read
        query: Optional search query (Gmail: "from:example@gmail.com", Outlook: OData filter)
        limit: Maximum number of messages to return (when listing)
    
    Returns:
        Dictionary with email(s) information
    """
    try:
        provider_lower = provider.lower()
        
        if provider_lower == "gmail":
            from src.email.gmail import (
                get_gmail_message,
                list_gmail_messages,
                is_gmail_connected
            )
            
            if not is_gmail_connected():
                raise TaskError("Gmail not connected. Please connect Gmail in the UI first.")
            
            if message_id:
                # Get specific message
                message = get_gmail_message(message_id, format="full")
                
                # Extract readable content
                payload = message.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                
                # Get body text
                body_text = ""
                body_html = ""
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("mimeType") == "text/plain":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                import base64
                                body_text = base64.urlsafe_b64decode(data).decode("utf-8")
                        elif part.get("mimeType") == "text/html":
                            data = part.get("body", {}).get("data", "")
                            if data:
                                import base64
                                body_html = base64.urlsafe_b64decode(data).decode("utf-8")
                else:
                    # Single part message
                    if payload.get("mimeType") == "text/plain":
                        data = payload.get("body", {}).get("data", "")
                        if data:
                            import base64
                            body_text = base64.urlsafe_b64decode(data).decode("utf-8")
                
                return {
                    "success": True,
                    "provider": "gmail",
                    "message": {
                        "id": message.get("id"),
                        "thread_id": message.get("threadId"),
                        "subject": headers.get("Subject", ""),
                        "from": headers.get("From", ""),
                        "to": headers.get("To", ""),
                        "date": headers.get("Date", ""),
                        "body": body_text or body_html,
                        "snippet": message.get("snippet", "")
                    }
                }
            else:
                # List messages
                result = list_gmail_messages(query=query, max_results=limit)
                messages = result.get("messages", [])
                
                # Get full details for each message
                full_messages = []
                for msg in messages:
                    try:
                        full_msg = get_gmail_message(msg["id"], format="metadata")
                        payload = full_msg.get("payload", {})
                        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                        full_messages.append({
                            "id": full_msg.get("id"),
                            "thread_id": full_msg.get("threadId"),
                            "subject": headers.get("Subject", ""),
                            "from": headers.get("From", ""),
                            "to": headers.get("To", ""),
                            "date": headers.get("Date", ""),
                            "snippet": full_msg.get("snippet", "")
                        })
                    except Exception as e:
                        logger.warning("failed_to_get_message_details", message_id=msg.get("id"), error=str(e))
                
                return {
                    "success": True,
                    "provider": "gmail",
                    "messages": full_messages,
                    "count": len(full_messages)
                }
        
        elif provider_lower == "outlook":
            from src.email.outlook import (
                get_outlook_message,
                list_outlook_messages,
                is_outlook_connected
            )
            
            if not is_outlook_connected():
                raise TaskError("Outlook not connected. Please connect Outlook in the UI first.")
            
            if message_id:
                # Get specific message
                message = get_outlook_message(message_id)
                
                return {
                    "success": True,
                    "provider": "outlook",
                    "message": {
                        "id": message.get("id"),
                        "subject": message.get("subject", ""),
                        "from": message.get("from", {}).get("emailAddress", {}).get("address", ""),
                        "to": [addr.get("emailAddress", {}).get("address", "") for addr in message.get("toRecipients", [])],
                        "date": message.get("receivedDateTime", ""),
                        "body": message.get("body", {}).get("content", ""),
                        "body_preview": message.get("bodyPreview", "")
                    }
                }
            else:
                # List messages
                result = list_outlook_messages(filter_query=query, top=limit)
                messages = result.get("messages", [])
                
                # Format messages for readability
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        "id": msg.get("id"),
                        "subject": msg.get("subject", ""),
                        "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
                        "to": [addr.get("emailAddress", {}).get("address", "") for addr in msg.get("toRecipients", [])],
                        "date": msg.get("receivedDateTime", ""),
                        "body_preview": msg.get("bodyPreview", ""),
                        "is_read": msg.get("isRead", False)
                    })
                
                return {
                    "success": True,
                    "provider": "outlook",
                    "messages": formatted_messages,
                    "count": len(formatted_messages)
                }
        
        else:
            raise TaskError(f"Unsupported email provider: {provider}. Use 'gmail' or 'outlook'.")
    
    except Exception as e:
        logger.error("read_email_error", error=str(e), provider=provider)
        raise TaskError(f"Failed to read email: {str(e)}") from e


async def list_emails(
    provider: str,
    query: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List emails from Gmail or Outlook. This is a convenience wrapper around read_email.
    
    Args:
        provider: Email provider ("gmail" or "outlook")
        query: Optional search query
        limit: Maximum number of messages to return
    
    Returns:
        Dictionary with list of emails
    """
    return await read_email(provider=provider, query=query, limit=limit)


# Tool definitions for OpenAI Agents SDK
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "make_call",
            "description": "Make a phone call to a specified number. Use this when the user wants to call someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_number": {
                        "type": "string",
                        "description": "Phone number to call in E.164 format (e.g., +1234567890)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional message or purpose for the call"
                    },
                    "from_number": {
                        "type": "string",
                        "description": "Optional phone number to call from (defaults to configured number)"
                    }
                },
                "required": ["to_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_sms",
            "description": "Send an SMS text message to a phone number. Use this when the user wants to text someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_number": {
                        "type": "string",
                        "description": "Phone number to send to in E.164 format (e.g., +1234567890)"
                    },
                    "message": {
                        "type": "string",
                        "description": "The text message content"
                    },
                    "from_number": {
                        "type": "string",
                        "description": "Optional phone number to send from (defaults to configured number)"
                    }
                },
                "required": ["to_number", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email message. Automatically uses Gmail if connected, then Outlook, otherwise falls back to SMTP. Use this when the user wants to email someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Email address to send to"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Optional sender email (defaults to configured email)"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Optional email provider preference: 'gmail', 'outlook', or 'smtp'. If not specified, tries Gmail first, then Outlook, then SMTP.",
                        "enum": ["gmail", "outlook", "smtp"]
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of CC email addresses"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of BCC email addresses"
                    }
                },
                "required": ["to_email", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_email",
            "description": "Read emails from Gmail or Outlook. Can read a specific message by ID or search/list messages. Use this when the user wants to check their email, read a specific email, or search for emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Email provider to use: 'gmail' or 'outlook'",
                        "enum": ["gmail", "outlook"]
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Optional specific message ID to read. If not provided, will list/search messages instead."
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query. For Gmail: use Gmail search syntax (e.g., 'from:example@gmail.com', 'subject:meeting'). For Outlook: use OData filter syntax (e.g., 'from/emailAddress/address eq \\'example@outlook.com\\'')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return when listing (default: 10)"
                    }
                },
                "required": ["provider"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_emails",
            "description": "List emails from Gmail or Outlook. This is a convenience function for listing emails with optional search. Use this when the user wants to see their recent emails or search for specific emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Email provider to use: 'gmail' or 'outlook'",
                        "enum": ["gmail", "outlook"]
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query. For Gmail: use Gmail search syntax (e.g., 'from:example@gmail.com'). For Outlook: use OData filter syntax."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return (default: 10)"
                    }
                },
                "required": ["provider"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_research",
            "description": "Fetch and extract readable text from an allowlisted public URL for research/summarization.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch (https://...)"},
                    "allow_hosts_csv": {"type": "string", "description": "Optional extra allowlisted hosts (comma-separated)"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_create_event",
            "description": "Create a Google Calendar event (optionally with a Google Meet link) and invite attendees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_iso": {"type": "string", "description": "Start time ISO8601 (e.g. 2025-01-01T15:00:00-05:00)"},
                    "end_iso": {"type": "string", "description": "End time ISO8601"},
                    "description": {"type": "string", "description": "Event description"},
                    "location": {"type": "string", "description": "Event location"},
                    "attendees_emails": {"type": "array", "items": {"type": "string"}, "description": "Attendee emails"},
                    "timezone": {"type": "string", "description": "IANA timezone, e.g. America/New_York"},
                    "add_google_meet": {"type": "boolean", "description": "Whether to attach a Google Meet link"},
                },
                "required": ["summary", "start_iso", "end_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_list_upcoming",
            "description": "List upcoming Google Calendar events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max events to return"},
                },
                "required": [],
            },
        },
    },
]

# Tool handler mapping
TOOL_HANDLERS = {
    "make_call": make_call,
    "send_sms": send_sms,
    "send_email": send_email,
    "read_email": read_email,
    "list_emails": list_emails,
    "web_research": web_research_tool,
    "calendar_create_event": calendar_create_event,
    "calendar_list_upcoming": calendar_list_upcoming,
}

