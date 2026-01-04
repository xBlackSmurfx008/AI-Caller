"""
AI Module - OpenAI integration and agent capabilities.

This module provides:
- ModelManager: Manages different OpenAI models for different purposes
- SkillManager: Registry of AI agent skills and tools
- Voice Agent: Real-time voice-to-voice conversations
"""

from src.ai.model_manager import (
    ModelManager,
    ModelPurpose,
    ModelConfig,
    get_model_manager,
)
from src.ai.skill_manager import (
    SkillManager,
    SkillCategory,
    SkillRisk,
    Skill,
    get_skill_manager,
)

__all__ = [
    # Model management
    "ModelManager",
    "ModelPurpose",
    "ModelConfig",
    "get_model_manager",
    # Skill management
    "SkillManager",
    "SkillCategory",
    "SkillRisk",
    "Skill",
    "get_skill_manager",
]

