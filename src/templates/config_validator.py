"""Configuration validator"""

from typing import Dict, Any, List

from src.utils.errors import ConfigurationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigValidator:
    """Validates business configuration templates"""

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration and return list of errors
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate business section
        if "business" not in config:
            errors.append("Missing 'business' section")
        else:
            business = config["business"]
            if "name" not in business:
                errors.append("Business section missing 'name'")
            if "type" not in business:
                errors.append("Business section missing 'type'")

        # Validate AI section
        if "ai" not in config:
            errors.append("Missing 'ai' section")
        else:
            ai = config["ai"]
            if "model" not in ai:
                errors.append("AI section missing 'model'")
            if "system_prompt" not in ai:
                errors.append("AI section missing 'system_prompt'")

        # Validate voice section (optional but should be valid if present)
        if "voice" in config:
            voice = config["voice"]
            valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            if "voice" in voice and voice["voice"] not in valid_voices:
                errors.append(f"Invalid voice: {voice['voice']}. Must be one of {valid_voices}")

        # Validate escalation section (optional)
        if "escalation" in config:
            escalation = config["escalation"]
            if "triggers" in escalation:
                for trigger in escalation["triggers"]:
                    if "type" not in trigger:
                        errors.append("Escalation trigger missing 'type'")

        return errors

    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration and raise exception if invalid
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = self.validate(config)
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_message)

