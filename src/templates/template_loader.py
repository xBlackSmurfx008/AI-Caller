"""Template loader for business configurations"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.errors import ConfigurationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TemplateLoader:
    """Loads and manages business configuration templates"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize template loader
        
        Args:
            templates_dir: Directory containing template files
        """
        if templates_dir is None:
            # Default to config/templates directory
            base_path = Path(__file__).parent.parent.parent
            templates_dir = str(base_path / "config" / "templates")

        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, Dict[str, Any]] = {}

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a template by name
        
        Args:
            template_name: Name of template (without .yaml extension)
            
        Returns:
            Template configuration dictionary
        """
        if template_name in self.templates:
            return self.templates[template_name]

        template_path = self.templates_dir / f"{template_name}.yaml"

        if not template_path.exists():
            # Try default template
            default_path = self.templates_dir / "default.yaml"
            if default_path.exists():
                logger.warning(
                    "template_not_found_using_default",
                    template_name=template_name,
                )
                template_path = default_path
            else:
                raise ConfigurationError(f"Template not found: {template_name}")

        try:
            with open(template_path, "r") as f:
                template = yaml.safe_load(f)

            # Validate template
            self._validate_template(template)

            # Cache template
            self.templates[template_name] = template

            logger.info("template_loaded", template_name=template_name)
            return template

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse template {template_name}: {str(e)}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load template {template_name}: {str(e)}") from e

    def load_default(self) -> Dict[str, Any]:
        """
        Load default template
        
        Returns:
            Default template configuration
        """
        return self.load_template("default")

    def _validate_template(self, template: Dict[str, Any]) -> None:
        """
        Validate template structure
        
        Args:
            template: Template dictionary
            
        Raises:
            ConfigurationError: If template is invalid
        """
        required_sections = ["business", "ai"]

        for section in required_sections:
            if section not in template:
                raise ConfigurationError(f"Missing required section: {section}")

        # Validate AI section
        ai_section = template.get("ai", {})
        if "system_prompt" not in ai_section and "model" not in ai_section:
            raise ConfigurationError("AI section must contain 'system_prompt' or 'model'")

    def get_system_prompt(self, template: Dict[str, Any]) -> str:
        """
        Extract system prompt from template
        
        Args:
            template: Template dictionary
            
        Returns:
            System prompt string
        """
        ai_section = template.get("ai", {})
        return ai_section.get("system_prompt", "You are a helpful assistant.")

    def get_ai_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI configuration from template
        
        Args:
            template: Template dictionary
            
        Returns:
            AI configuration dictionary
        """
        return template.get("ai", {})

    def get_voice_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get voice configuration from template
        
        Args:
            template: Template dictionary
            
        Returns:
            Voice configuration dictionary
        """
        return template.get("voice", {})

    def get_knowledge_base_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get knowledge base configuration from template
        
        Args:
            template: Template dictionary
            
        Returns:
            Knowledge base configuration dictionary
        """
        return template.get("knowledge_base", {})

    def get_qa_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get QA configuration from template
        
        Args:
            template: Template dictionary
            
        Returns:
            QA configuration dictionary
        """
        return template.get("quality_assurance", {})

    def get_escalation_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get escalation configuration from template
        
        Args:
            template: Template dictionary
            
        Returns:
            Escalation configuration dictionary
        """
        return template.get("escalation", {})

    def list_templates(self) -> list[str]:
        """
        List available templates
        
        Returns:
            List of template names
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for file in self.templates_dir.glob("*.yaml"):
            templates.append(file.stem)

        return templates

