"""Agent personality and skills loader from markdown files"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from src.utils.logging import get_logger

logger = get_logger(__name__)


class AgentPersonality:
    """Agent personality configuration loaded from markdown files"""

    def __init__(self, name: str, personality_data: Dict[str, Any]):
        """
        Initialize agent personality
        
        Args:
            name: Personality name
            personality_data: Parsed personality data
        """
        self.name = name
        self.data = personality_data

    @property
    def traits(self) -> List[str]:
        """Get personality traits"""
        return self.data.get("traits", [])

    @property
    def skills(self) -> List[str]:
        """Get agent skills"""
        return self.data.get("skills", [])

    @property
    def system_prompt(self) -> str:
        """Get system prompt for this personality"""
        return self.data.get("system_prompt", "")

    @property
    def voice_config(self) -> Dict[str, Any]:
        """Get voice configuration"""
        return self.data.get("voice_config", {})

    @property
    def conversation_patterns(self) -> Dict[str, str]:
        """Get conversation patterns"""
        return self.data.get("conversation_patterns", {})

    @property
    def guidelines(self) -> Dict[str, List[str]]:
        """Get response guidelines"""
        return self.data.get("guidelines", {})


class AgentPersonalityLoader:
    """Load agent personalities from markdown files"""

    def __init__(self, personalities_dir: Optional[str] = None):
        """
        Initialize personality loader
        
        Args:
            personalities_dir: Directory containing personality markdown files
        """
        if personalities_dir is None:
            # Default to docs/agents/personalities
            project_root = Path(__file__).parent.parent.parent
            personalities_dir = project_root / "docs" / "agents" / "personalities"
        
        self.personalities_dir = Path(personalities_dir)
        self.personalities: Dict[str, AgentPersonality] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all personality files"""
        if not self.personalities_dir.exists():
            logger.warning(
                "personalities_directory_not_found",
                directory=str(self.personalities_dir)
            )
            return

        for md_file in self.personalities_dir.glob("*.md"):
            try:
                personality = self._load_personality(md_file)
                if personality:
                    self.personalities[personality.name] = personality
                    logger.info(
                        "personality_loaded",
                        name=personality.name,
                        file=str(md_file)
                    )
            except Exception as e:
                logger.error(
                    "personality_load_error",
                    file=str(md_file),
                    error=str(e)
                )

    def _load_personality(self, file_path: Path) -> Optional[AgentPersonality]:
        """
        Load personality from markdown file
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            AgentPersonality instance or None
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract personality name from filename
        name = file_path.stem.upper().replace("_", " ")

        # Parse markdown content
        personality_data = self._parse_markdown(content)

        return AgentPersonality(name, personality_data)

    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """
        Parse markdown content into structured data
        
        Args:
            content: Markdown content
            
        Returns:
            Parsed personality data
        """
        data = {
            "traits": [],
            "skills": [],
            "system_prompt": "",
            "voice_config": {},
            "conversation_patterns": {},
            "guidelines": {"do": [], "don't": []},
        }

        # Extract sections
        sections = self._extract_sections(content)

        # Parse personality traits
        if "Personality Traits" in sections:
            traits_section = sections["Personality Traits"]
            data["traits"] = self._extract_list_items(traits_section)

        # Parse skills
        if "Skills & Capabilities" in sections:
            skills_section = sections["Skills & Capabilities"]
            data["skills"] = self._extract_list_items(skills_section)

        # Parse system prompt from overview and traits
        overview = sections.get("Overview", "")
        traits_text = sections.get("Personality Traits", "")
        data["system_prompt"] = self._build_system_prompt(overview, traits_text, sections)

        # Parse voice configuration
        if "Voice Configuration" in sections:
            voice_section = sections["Voice Configuration"]
            data["voice_config"] = self._parse_voice_config(voice_section)

        # Parse conversation patterns
        if "Conversation Patterns" in sections:
            patterns_section = sections["Conversation Patterns"]
            data["conversation_patterns"] = self._extract_code_blocks(patterns_section)

        # Parse guidelines
        if "Response Guidelines" in sections:
            guidelines_section = sections["Response Guidelines"]
            data["guidelines"] = self._parse_guidelines(guidelines_section)

        return data

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract markdown sections"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif line.startswith("### "):
                # Subsection - append to current section
                current_content.append(line)
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_list_items(self, content: str) -> List[str]:
        """Extract list items from markdown"""
        items = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                item = line[2:].strip()
                # Remove bold markers
                item = re.sub(r"\*\*(.*?)\*\*", r"\1", item)
                items.append(item)
        return items

    def _extract_code_blocks(self, content: str) -> Dict[str, str]:
        """Extract code blocks as conversation patterns"""
        patterns = {}
        in_code_block = False
        current_pattern = None
        current_content = []

        for line in content.split("\n"):
            if line.strip().startswith("```"):
                if in_code_block:
                    if current_pattern:
                        patterns[current_pattern] = "\n".join(current_content)
                    current_content = []
                    in_code_block = False
                else:
                    in_code_block = True
                    # Try to extract pattern name from preceding line
                    if current_pattern is None:
                        current_pattern = "default"
            elif in_code_block:
                current_content.append(line)
            elif line.strip().startswith("###"):
                current_pattern = line.strip()[4:].strip()

        if in_code_block and current_pattern:
            patterns[current_pattern] = "\n".join(current_content)

        return patterns

    def _parse_voice_config(self, content: str) -> Dict[str, Any]:
        """Parse voice configuration section"""
        config = {}
        for line in content.split("\n"):
            if "**Voice**:" in line:
                match = re.search(r"\*\*Voice\*\*:\s*`?(\w+)`?", line)
                if match:
                    config["voice"] = match.group(1)
            elif "**Temperature**:" in line:
                match = re.search(r"\*\*Temperature\*\*:\s*`?([\d.]+)`?", line)
                if match:
                    config["temperature"] = float(match.group(1))
            elif "**Response Delay**:" in line:
                match = re.search(r"\*\*Response Delay\*\*:\s*`?([\d.]+)s?`?", line)
                if match:
                    config["response_delay"] = float(match.group(1))
            elif "**Language**:" in line:
                match = re.search(r"\*\*Language\*\*:\s*`?([\w-]+)`?", line)
                if match:
                    config["language"] = match.group(1)
        return config

    def _parse_guidelines(self, content: str) -> Dict[str, List[str]]:
        """Parse response guidelines"""
        guidelines = {"do": [], "don't": []}
        current_list = None

        for line in content.split("\n"):
            line = line.strip()
            if "Do's" in line or "✅" in line:
                current_list = "do"
            elif "Don'ts" in line or "❌" in line:
                current_list = "don't"
            elif line.startswith("✅") or line.startswith("❌"):
                item = line[1:].strip()
                if current_list:
                    guidelines[current_list].append(item)

        return guidelines

    def _build_system_prompt(
        self, overview: str, traits_text: str, all_sections: Dict[str, str]
    ) -> str:
        """Build system prompt from personality data"""
        prompt_parts = []

        # Add overview
        if overview:
            prompt_parts.append(overview.split("\n")[0] if overview else "")

        # Add personality traits
        if traits_text:
            prompt_parts.append("\n## Personality")
            traits = self._extract_list_items(traits_text)
            for trait in traits[:5]:  # Limit to top 5
                prompt_parts.append(f"- {trait}")

        # Add communication style
        if "Communication Style" in all_sections:
            style_section = all_sections["Communication Style"]
            prompt_parts.append("\n## Communication Style")
            style_items = self._extract_list_items(style_section)
            for item in style_items[:3]:
                prompt_parts.append(f"- {item}")

        return "\n".join(prompt_parts)

    def get_personality(self, name: str) -> Optional[AgentPersonality]:
        """
        Get personality by name
        
        Args:
            name: Personality name (case-insensitive)
            
        Returns:
            AgentPersonality or None
        """
        # Try exact match first
        if name in self.personalities:
            return self.personalities[name]

        # Try case-insensitive match
        name_lower = name.lower()
        for key, personality in self.personalities.items():
            if key.lower() == name_lower:
                return personality

        return None

    def list_personalities(self) -> List[str]:
        """
        List all available personalities
        
        Returns:
            List of personality names
        """
        return list(self.personalities.keys())

    def get_default_personality(self) -> Optional[AgentPersonality]:
        """
        Get default personality (first available)
        
        Returns:
            AgentPersonality or None
        """
        if self.personalities:
            return list(self.personalities.values())[0]
        return None


# Global instance
_personality_loader: Optional[AgentPersonalityLoader] = None


def get_personality_loader() -> AgentPersonalityLoader:
    """Get global personality loader instance"""
    global _personality_loader
    if _personality_loader is None:
        _personality_loader = AgentPersonalityLoader()
    return _personality_loader

