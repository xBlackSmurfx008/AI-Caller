"""Utility to apply agent personality to OpenAI sessions"""

from typing import Optional, Dict, Any, Tuple
from src.ai.agent_personality import get_personality_loader
from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_personality_config(
    personality_name: Optional[str] = None,
    business_id: Optional[str] = None,
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Get personality configuration for OpenAI session
    
    Args:
        personality_name: Name of personality to use
        business_id: Business configuration ID (for fallback)
        
    Returns:
        Tuple of (system_prompt, voice_config)
    """
    system_prompt = None
    voice_config = {}
    
    if personality_name:
        try:
            loader = get_personality_loader()
            personality = loader.get_personality(personality_name)
            
            if personality:
                # Get system prompt from personality
                system_prompt = personality.system_prompt
                
                # Get voice configuration
                voice_config = personality.voice_config.copy()
                
                logger.info(
                    "personality_applied",
                    personality_name=personality_name,
                    has_prompt=bool(system_prompt),
                    voice_config=voice_config,
                )
            else:
                logger.warning(
                    "personality_not_found",
                    personality_name=personality_name,
                )
        except Exception as e:
            logger.error(
                "personality_load_error",
                personality_name=personality_name,
                error=str(e),
            )
    
    return system_prompt, voice_config


def apply_personality_to_session(
    personality_name: Optional[str] = None,
    base_system_prompt: Optional[str] = None,
    base_voice_config: Optional[Dict[str, Any]] = None,
    business_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Apply personality to session configuration
    
    Args:
        personality_name: Name of personality to apply
        base_system_prompt: Base system prompt (from template)
        base_voice_config: Base voice configuration (from template)
        business_id: Business configuration ID
        
    Returns:
        Tuple of (final_system_prompt, final_voice_config)
    """
    # Start with base configuration
    final_system_prompt = base_system_prompt or "You are a helpful AI assistant."
    final_voice_config = base_voice_config or {}
    
    # Apply personality if specified
    if personality_name:
        personality_prompt, personality_voice = get_personality_config(
            personality_name=personality_name,
            business_id=business_id,
        )
        
        # Merge system prompts
        if personality_prompt:
            if base_system_prompt:
                # Combine base and personality prompts
                final_system_prompt = f"{base_system_prompt}\n\n## Agent Personality\n{personality_prompt}"
            else:
                final_system_prompt = personality_prompt
        
        # Merge voice configuration (personality overrides base)
        if personality_voice:
            final_voice_config.update(personality_voice)
    
    return final_system_prompt, final_voice_config

