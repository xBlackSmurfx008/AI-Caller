"""
Skill Manager - Registry of AI agent capabilities and tools.

This module manages:
- Available skills/tools the AI can use
- Skill dependencies (e.g., "send_email" requires email provider)
- Skill approval requirements
- Runtime skill availability based on integrations
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SkillCategory(str, Enum):
    """Categories of skills."""
    TELEPHONY = "telephony"
    MESSAGING = "messaging"
    EMAIL = "email"
    CALENDAR = "calendar"
    RESEARCH = "research"
    MEMORY = "memory"
    SCHEDULING = "scheduling"
    RELATIONSHIP = "relationship"


class SkillRisk(str, Enum):
    """Risk level of skills."""
    LOW = "low"       # Read-only, no side effects
    MEDIUM = "medium"  # Side effects, but reversible
    HIGH = "high"     # Irreversible actions (calls, emails, etc.)


@dataclass
class Skill:
    """Definition of an AI skill/capability."""
    name: str
    description: str
    category: SkillCategory
    risk: SkillRisk
    handler: Optional[Callable[..., Awaitable[Any]]] = None
    
    # Dependencies
    requires_integration: Optional[str] = None  # e.g., "twilio", "gmail"
    requires_oauth: bool = False
    
    # Approval
    requires_approval: bool = True
    auto_execute_if_godfather: bool = True
    
    # OpenAI function schema
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    enabled: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0


class SkillManager:
    """
    Manages AI agent skills and capabilities.
    
    Usage:
        manager = SkillManager()
        
        # Check available skills
        skills = manager.get_available_skills()
        
        # Get skill for execution
        skill = manager.get_skill("make_call")
        
        # Execute a skill
        result = await manager.execute_skill("send_sms", to_number="+1234567890", message="Hello")
    """
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._integration_status: Dict[str, bool] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Register all default skills."""
        # Import handlers
        from src.agent.tools import TOOL_HANDLERS
        
        # Telephony skills
        self.register_skill(Skill(
            name="make_call",
            description="Make an outbound phone call to a number",
            category=SkillCategory.TELEPHONY,
            risk=SkillRisk.HIGH,
            handler=TOOL_HANDLERS.get("make_call"),
            requires_integration="twilio",
            requires_approval=True,
            auto_execute_if_godfather=True,
            parameters={
                "type": "object",
                "properties": {
                    "to_number": {"type": "string", "description": "Phone number in E.164 format"},
                    "message": {"type": "string", "description": "Message to deliver on the call"},
                    "from_number": {"type": "string", "description": "Caller ID (optional)"},
                },
                "required": ["to_number"],
            },
        ))
        
        self.register_skill(Skill(
            name="send_sms",
            description="Send an SMS text message",
            category=SkillCategory.MESSAGING,
            risk=SkillRisk.HIGH,
            handler=TOOL_HANDLERS.get("send_sms"),
            requires_integration="twilio",
            requires_approval=True,
            auto_execute_if_godfather=True,
            parameters={
                "type": "object",
                "properties": {
                    "to_number": {"type": "string", "description": "Phone number in E.164 format"},
                    "message": {"type": "string", "description": "Text message content"},
                    "from_number": {"type": "string", "description": "Sender number (optional)"},
                },
                "required": ["to_number", "message"],
            },
        ))
        
        # Email skills
        self.register_skill(Skill(
            name="send_email",
            description="Send an email message via Gmail, Outlook, or SMTP",
            category=SkillCategory.EMAIL,
            risk=SkillRisk.HIGH,
            handler=TOOL_HANDLERS.get("send_email"),
            requires_integration="email",  # Generic - checks gmail/outlook/smtp
            requires_approval=True,
            auto_execute_if_godfather=True,
            parameters={
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body content"},
                    "provider": {"type": "string", "enum": ["gmail", "outlook", "smtp"], "description": "Email provider"},
                },
                "required": ["to_email", "subject", "body"],
            },
        ))
        
        self.register_skill(Skill(
            name="read_email",
            description="Read emails from inbox (Gmail or Outlook)",
            category=SkillCategory.EMAIL,
            risk=SkillRisk.LOW,
            handler=TOOL_HANDLERS.get("read_email"),
            requires_integration="email",
            requires_oauth=True,
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "enum": ["gmail", "outlook"], "description": "Email provider"},
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max emails to return"},
                },
                "required": ["provider"],
            },
        ))
        
        # Calendar skills
        self.register_skill(Skill(
            name="calendar_create_event",
            description="Create a calendar event with optional Google Meet",
            category=SkillCategory.CALENDAR,
            risk=SkillRisk.MEDIUM,
            handler=TOOL_HANDLERS.get("calendar_create_event"),
            requires_integration="google_calendar",
            requires_oauth=True,
            requires_approval=True,
            auto_execute_if_godfather=True,
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_iso": {"type": "string", "description": "Start time ISO8601"},
                    "end_iso": {"type": "string", "description": "End time ISO8601"},
                    "description": {"type": "string", "description": "Event description"},
                    "attendees_emails": {"type": "array", "items": {"type": "string"}, "description": "Attendee emails"},
                    "add_google_meet": {"type": "boolean", "description": "Add Google Meet link"},
                },
                "required": ["summary", "start_iso", "end_iso"],
            },
        ))
        
        self.register_skill(Skill(
            name="calendar_list_upcoming",
            description="List upcoming calendar events",
            category=SkillCategory.CALENDAR,
            risk=SkillRisk.LOW,
            handler=TOOL_HANDLERS.get("calendar_list_upcoming"),
            requires_integration="google_calendar",
            requires_oauth=True,
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max events to return"},
                },
                "required": [],
            },
        ))
        
        # Research skills
        self.register_skill(Skill(
            name="web_research",
            description="Search the web for information",
            category=SkillCategory.RESEARCH,
            risk=SkillRisk.LOW,
            handler=TOOL_HANDLERS.get("web_research"),
            requires_integration=None,
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results"},
                },
                "required": ["query"],
            },
        ))
        
        logger.info("skills_registered", count=len(self._skills))
    
    def register_skill(self, skill: Skill) -> None:
        """Register a new skill."""
        self._skills[skill.name] = skill
        logger.debug("skill_registered", skill=skill.name, category=skill.category.value)
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def get_available_skills(self, check_integrations: bool = True) -> List[Skill]:
        """
        Get all available skills.
        
        Args:
            check_integrations: If True, filter by integration availability
            
        Returns:
            List of available skills
        """
        skills = []
        for skill in self._skills.values():
            if not skill.enabled:
                continue
            if check_integrations and skill.requires_integration:
                if not self._check_integration(skill.requires_integration):
                    continue
            skills.append(skill)
        return skills
    
    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """Get skills in a specific category."""
        return [s for s in self._skills.values() if s.category == category and s.enabled]
    
    def get_openai_tools(self, check_integrations: bool = True) -> List[Dict[str, Any]]:
        """
        Get skills formatted as OpenAI function calling tools.
        
        Returns:
            List of tool definitions for OpenAI API
        """
        tools = []
        for skill in self.get_available_skills(check_integrations):
            tools.append({
                "type": "function",
                "function": {
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": skill.parameters,
                },
            })
        return tools
    
    def get_realtime_tools(self, check_integrations: bool = True) -> List[Dict[str, Any]]:
        """
        Get skills formatted for OpenAI Realtime API.
        
        Returns:
            List of tool definitions for Realtime API
        """
        tools = []
        for skill in self.get_available_skills(check_integrations):
            tools.append({
                "type": "function",
                "name": skill.name,
                "description": skill.description,
                "parameters": skill.parameters,
            })
        return tools
    
    async def execute_skill(
        self,
        name: str,
        is_godfather: bool = False,
        skip_approval: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a skill.
        
        Args:
            name: Skill name
            is_godfather: Whether the requester is the Godfather
            skip_approval: Skip approval check
            **kwargs: Skill parameters
            
        Returns:
            Execution result
        """
        skill = self.get_skill(name)
        if not skill:
            return {"error": f"Unknown skill: {name}"}
        
        if not skill.enabled:
            return {"error": f"Skill disabled: {name}"}
        
        if skill.requires_integration:
            if not self._check_integration(skill.requires_integration):
                return {"error": f"Integration not available: {skill.requires_integration}"}
        
        # Check approval requirements
        needs_approval = skill.requires_approval
        if is_godfather and skill.auto_execute_if_godfather:
            needs_approval = False
        if skip_approval:
            needs_approval = False
        
        if needs_approval:
            return {
                "requires_approval": True,
                "skill": name,
                "parameters": kwargs,
                "reason": f"Skill '{name}' requires approval",
            }
        
        # Execute
        if not skill.handler:
            return {"error": f"Skill handler not configured: {name}"}
        
        try:
            result = await skill.handler(**kwargs)
            skill.last_used = datetime.utcnow()
            skill.usage_count += 1
            return {"success": True, "result": result}
        except Exception as e:
            logger.error("skill_execution_failed", skill=name, error=str(e))
            return {"error": str(e)}
    
    def update_integration_status(self, integration: str, available: bool) -> None:
        """Update the availability status of an integration."""
        self._integration_status[integration] = available
    
    def _check_integration(self, integration: str) -> bool:
        """Check if an integration is available."""
        # Check cached status first
        if integration in self._integration_status:
            return self._integration_status[integration]
        
        # Otherwise, try to determine from settings
        if integration == "twilio":
            return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)
        elif integration == "gmail":
            return bool(settings.GMAIL_OAUTH_CLIENT_SECRETS_JSON or settings.GMAIL_OAUTH_CLIENT_SECRETS_FILE)
        elif integration == "google_calendar":
            return bool(settings.GOOGLE_OAUTH_CLIENT_SECRETS_JSON or settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE)
        elif integration == "outlook":
            return bool(settings.OUTLOOK_OAUTH_CLIENT_SECRETS_JSON or settings.OUTLOOK_OAUTH_CLIENT_SECRETS_FILE)
        elif integration == "smtp":
            return bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
        elif integration == "email":
            # Any email provider
            return self._check_integration("gmail") or self._check_integration("outlook") or self._check_integration("smtp")
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get skill manager status."""
        available = self.get_available_skills()
        by_category = {}
        for cat in SkillCategory:
            by_category[cat.value] = len([s for s in available if s.category == cat])
        
        return {
            "total_skills": len(self._skills),
            "available_skills": len(available),
            "by_category": by_category,
            "integrations": {
                "twilio": self._check_integration("twilio"),
                "gmail": self._check_integration("gmail"),
                "google_calendar": self._check_integration("google_calendar"),
                "outlook": self._check_integration("outlook"),
                "smtp": self._check_integration("smtp"),
            },
        }


# Singleton instance
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Get the singleton SkillManager instance."""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager

