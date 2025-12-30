"""Custom exception classes"""

from typing import Optional, Dict, Any


class AICallerError(Exception):
    """Base exception for AI Caller system"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper().replace("ERROR", "_ERROR")
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class TelephonyError(AICallerError):
    """Telephony-related errors"""
    pass


class OpenAIError(AICallerError):
    """OpenAI API errors"""
    pass


class ConfigurationError(AICallerError):
    """Configuration errors"""
    pass


class ValidationError(AICallerError):
    """Validation errors"""
    pass


class NotFoundError(AICallerError):
    """Resource not found errors"""
    pass


class TaskError(AICallerError):
    """Task execution errors"""
    pass
