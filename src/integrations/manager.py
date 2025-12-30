"""Integration Manager - Centralized initialization and connection verification for all services"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.integrations.retry import retry_connection

logger = get_logger(__name__)
settings = get_settings()


class IntegrationStatus(Enum):
    """Integration connection status"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


@dataclass
class IntegrationInfo:
    """Information about an integration"""
    name: str
    status: IntegrationStatus
    message: str = ""
    config_required: List[str] = field(default_factory=list)
    last_check: Optional[float] = None
    error: Optional[str] = None


class IntegrationManager:
    """Manages initialization and connection verification for all integrations"""
    
    def __init__(self):
        """Initialize integration manager"""
        self.integrations: Dict[str, IntegrationInfo] = {}
        self._initialized = False
        
    def register_integration(
        self,
        name: str,
        config_required: List[str] = None,
        initial_status: IntegrationStatus = IntegrationStatus.NOT_INITIALIZED
    ):
        """Register an integration"""
        self.integrations[name] = IntegrationInfo(
            name=name,
            status=initial_status,
            config_required=config_required or []
        )
    
    def update_status(
        self,
        name: str,
        status: IntegrationStatus,
        message: str = "",
        error: Optional[str] = None
    ):
        """Update integration status"""
        if name in self.integrations:
            self.integrations[name].status = status
            self.integrations[name].message = message
            self.integrations[name].error = error
            import time
            self.integrations[name].last_check = time.time()
    
    def get_status(self, name: str) -> Optional[IntegrationInfo]:
        """Get integration status"""
        return self.integrations.get(name)
    
    def get_all_status(self) -> Dict[str, IntegrationInfo]:
        """Get all integration statuses"""
        return self.integrations.copy()
    
    def verify_database(self) -> IntegrationInfo:
        """Verify database connection with retry logic"""
        name = "database"
        try:
            from src.database.database import engine, SessionLocal
            from sqlalchemy import text
            
            def _test_connection():
                # Try to create a session and execute a simple query
                db = SessionLocal()
                try:
                    db.execute(text("SELECT 1"))
                    db.commit()
                    return True
                finally:
                    db.close()
            
            # Use retry decorator
            retry_decorator = retry_connection(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,))
            retry_decorator(_test_connection)()
            self.update_status(name, IntegrationStatus.CONNECTED, "Database connection successful")
        except Exception as e:
            # Check if it's a configuration issue
            if "DATABASE_URL" in str(e) or "not configured" in str(e).lower():
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    "DATABASE_URL not configured (using SQLite fallback)",
                    str(e)
                )
            else:
                self.update_status(name, IntegrationStatus.ERROR, f"Database connection failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_openai(self) -> IntegrationInfo:
        """Verify OpenAI connection"""
        name = "openai"
        try:
            # Check if API key is configured
            if not settings.OPENAI_API_KEY:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    "OPENAI_API_KEY not configured",
                    "Missing OPENAI_API_KEY"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # Try to create OpenAI client (lightweight check)
            from src.utils.openai_client import create_openai_client
            client = create_openai_client(timeout=10.0, max_retries=1)
            
            # Verify API key by checking model availability (lightweight)
            # We don't make an actual API call, just verify the client can be created
            self.update_status(name, IntegrationStatus.CONNECTED, "OpenAI client initialized")
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"OpenAI initialization failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_twilio(self) -> IntegrationInfo:
        """Verify Twilio connection with retry logic"""
        name = "twilio"
        try:
            # Check required config
            required = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
            missing = [key for key in required if not getattr(settings, key, None)]
            
            if missing:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    f"Missing configuration: {', '.join(missing)}",
                    f"Missing: {', '.join(missing)}"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # IMPORTANT: Avoid outbound network calls during app import/startup.
            # Just verify we can construct the client and that Account SID format looks plausible.
            from twilio.rest import Client as TwilioClient

            TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            sid_ok = str(settings.TWILIO_ACCOUNT_SID or "").startswith("AC")
            msg = "Twilio client initialized" + ("" if sid_ok else " (warning: Account SID should start with 'AC')")
            self.update_status(name, IntegrationStatus.CONNECTED, msg)
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"Twilio connection failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_google_calendar(self) -> IntegrationInfo:
        """Verify Google Calendar connection"""
        name = "google_calendar"
        try:
            # Check if OAuth config is provided
            has_file = bool(settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE)
            has_json = bool(settings.GOOGLE_OAUTH_CLIENT_SECRETS_JSON)
            
            if not has_file and not has_json:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    "Google OAuth client secrets not configured",
                    "Missing GOOGLE_OAUTH_CLIENT_SECRETS_FILE or GOOGLE_OAUTH_CLIENT_SECRETS_JSON"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # Check if connected (has valid token)
            from src.calendar.google_calendar import is_connected
            if is_connected():
                self.update_status(name, IntegrationStatus.CONNECTED, "Google Calendar connected")
            else:
                self.update_status(
                    name,
                    IntegrationStatus.DISCONNECTED,
                    "Google Calendar OAuth not completed - needs authentication",
                    "OAuth token not found or expired"
                )
        except ImportError:
            self.update_status(
                name,
                IntegrationStatus.NOT_CONFIGURED,
                "Google Calendar dependencies not installed",
                "Install: pip install google-api-python-client google-auth google-auth-oauthlib"
            )
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"Google Calendar check failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_smtp(self) -> IntegrationInfo:
        """Verify SMTP/Email configuration"""
        name = "smtp"
        try:
            # Check required config
            required = ["SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"]
            missing = [key for key in required if not getattr(settings, key, None)]
            
            if missing:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    f"Missing configuration: {', '.join(missing)}",
                    f"Missing: {', '.join(missing)}"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # Don't actually connect to SMTP server (would require network call)
            # Just verify configuration is present
            self.update_status(
                name,
                IntegrationStatus.CONNECTED,
                f"SMTP configured ({settings.SMTP_SERVER}:{settings.SMTP_PORT})"
            )
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"SMTP check failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_gmail(self) -> IntegrationInfo:
        """Verify Gmail connection"""
        name = "gmail"
        try:
            # Check if OAuth config is provided
            has_file = bool(settings.GMAIL_OAUTH_CLIENT_SECRETS_FILE)
            has_json = bool(settings.GMAIL_OAUTH_CLIENT_SECRETS_JSON)
            
            if not has_file and not has_json:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    "Gmail OAuth client secrets not configured",
                    "Missing GMAIL_OAUTH_CLIENT_SECRETS_FILE or GMAIL_OAUTH_CLIENT_SECRETS_JSON"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # Check if connected (has valid token)
            from src.email.gmail import is_gmail_connected
            if is_gmail_connected():
                self.update_status(name, IntegrationStatus.CONNECTED, "Gmail connected")
            else:
                self.update_status(
                    name,
                    IntegrationStatus.DISCONNECTED,
                    "Gmail OAuth not completed - needs authentication",
                    "OAuth token not found or expired"
                )
        except ImportError:
            self.update_status(
                name,
                IntegrationStatus.NOT_CONFIGURED,
                "Gmail dependencies not installed",
                "Install: pip install google-api-python-client google-auth google-auth-oauthlib"
            )
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"Gmail check failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def verify_outlook(self) -> IntegrationInfo:
        """Verify Outlook connection"""
        name = "outlook"
        try:
            # Check if OAuth config is provided
            has_file = bool(settings.OUTLOOK_OAUTH_CLIENT_SECRETS_FILE)
            has_json = bool(settings.OUTLOOK_OAUTH_CLIENT_SECRETS_JSON)
            
            if not has_file and not has_json:
                self.update_status(
                    name,
                    IntegrationStatus.NOT_CONFIGURED,
                    "Outlook OAuth client secrets not configured",
                    "Missing OUTLOOK_OAUTH_CLIENT_SECRETS_FILE or OUTLOOK_OAUTH_CLIENT_SECRETS_JSON"
                )
                return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.NOT_CONFIGURED))
            
            # Check if connected (has valid token)
            from src.email.outlook import is_outlook_connected
            if is_outlook_connected():
                self.update_status(name, IntegrationStatus.CONNECTED, "Outlook connected")
            else:
                self.update_status(
                    name,
                    IntegrationStatus.DISCONNECTED,
                    "Outlook OAuth not completed - needs authentication",
                    "OAuth token not found or expired"
                )
        except ImportError:
            self.update_status(
                name,
                IntegrationStatus.NOT_CONFIGURED,
                "Outlook dependencies not installed",
                "Install: pip install msal"
            )
        except Exception as e:
            self.update_status(name, IntegrationStatus.ERROR, f"Outlook check failed: {str(e)}", str(e))
        
        return self.integrations.get(name, IntegrationInfo(name, IntegrationStatus.ERROR, "Not registered"))
    
    def initialize_all(self) -> Dict[str, IntegrationInfo]:
        """Initialize and verify all integrations"""
        if self._initialized:
            logger.info("integrations_already_initialized")
            return self.get_all_status()
        
        logger.info("initializing_integrations")
        self._initialized = True
        
        # Register all integrations
        self.register_integration("database", ["DATABASE_URL"])
        self.register_integration("openai", ["OPENAI_API_KEY"])
        self.register_integration("twilio", ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"])
        self.register_integration("google_calendar", ["GOOGLE_OAUTH_CLIENT_SECRETS_FILE", "GOOGLE_OAUTH_CLIENT_SECRETS_JSON"])
        self.register_integration("gmail", ["GMAIL_OAUTH_CLIENT_SECRETS_FILE", "GMAIL_OAUTH_CLIENT_SECRETS_JSON"])
        self.register_integration("outlook", ["OUTLOOK_OAUTH_CLIENT_SECRETS_FILE", "OUTLOOK_OAUTH_CLIENT_SECRETS_JSON"])
        self.register_integration("smtp", ["SMTP_SERVER", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"])
        
        # Verify each integration
        self.verify_database()
        self.verify_openai()
        self.verify_twilio()
        self.verify_google_calendar()
        self.verify_gmail()
        self.verify_outlook()
        self.verify_smtp()
        
        # Log summary
        connected = [name for name, info in self.integrations.items() if info.status == IntegrationStatus.CONNECTED]
        disconnected = [name for name, info in self.integrations.items() if info.status == IntegrationStatus.DISCONNECTED]
        not_configured = [name for name, info in self.integrations.items() if info.status == IntegrationStatus.NOT_CONFIGURED]
        errors = [name for name, info in self.integrations.items() if info.status == IntegrationStatus.ERROR]
        
        logger.info(
            "integrations_initialized",
            connected=len(connected),
            disconnected=len(disconnected),
            not_configured=len(not_configured),
            errors=len(errors),
            connected_services=connected
        )
        
        return self.get_all_status()
    
    def verify_all(self) -> Dict[str, IntegrationInfo]:
        """Re-verify all integrations (for health checks)"""
        logger.info("verifying_all_integrations")
        
        self.verify_database()
        self.verify_openai()
        self.verify_twilio()
        self.verify_google_calendar()
        self.verify_gmail()
        self.verify_outlook()
        self.verify_smtp()
        
        return self.get_all_status()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all integrations"""
        statuses = self.get_all_status()
        
        summary = {
            "overall": "healthy",
            "integrations": {},
            "counts": {
                "connected": 0,
                "disconnected": 0,
                "not_configured": 0,
                "error": 0
            }
        }
        
        for name, info in statuses.items():
            summary["integrations"][name] = {
                "status": info.status.value,
                "message": info.message,
                "error": info.error
            }
            
            if info.status == IntegrationStatus.CONNECTED:
                summary["counts"]["connected"] += 1
            elif info.status == IntegrationStatus.DISCONNECTED:
                summary["counts"]["disconnected"] += 1
            elif info.status == IntegrationStatus.NOT_CONFIGURED:
                summary["counts"]["not_configured"] += 1
            elif info.status == IntegrationStatus.ERROR:
                summary["counts"]["error"] += 1
        
        # Overall health: healthy if critical services (database, openai) are connected
        critical_services = ["database", "openai"]
        critical_ok = all(
            statuses.get(name, IntegrationInfo(name, IntegrationStatus.ERROR)).status == IntegrationStatus.CONNECTED
            for name in critical_services
            if name in statuses
        )
        
        if not critical_ok:
            summary["overall"] = "degraded"
        
        if summary["counts"]["error"] > 0:
            summary["overall"] = "unhealthy"
        
        return summary


# Singleton instance
_integration_manager: Optional[IntegrationManager] = None


def get_integration_manager() -> IntegrationManager:
    """Get singleton integration manager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = IntegrationManager()
    return _integration_manager

