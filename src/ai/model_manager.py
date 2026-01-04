"""
AI Model Manager - Manages different OpenAI models for different purposes.

This module provides a unified interface for:
- Chat models (gpt-4o, gpt-4-turbo) for text-based task planning
- Realtime models (gpt-4o-realtime-preview) for voice-to-voice conversations
- Structured output models for JSON responses
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from openai import OpenAI

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ModelPurpose(str, Enum):
    """Purpose/use-case for model selection."""
    CHAT = "chat"                    # Standard chat completions
    PLANNING = "planning"            # Task planning with tool calls
    VOICE_REALTIME = "voice_realtime"  # Real-time voice conversations
    STRUCTURED_OUTPUT = "structured"  # JSON structured responses
    EMBEDDING = "embedding"          # Text embeddings


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    purpose: ModelPurpose
    supports_tools: bool = True
    supports_streaming: bool = True
    supports_json_mode: bool = True
    max_tokens: int = 4096
    default_temperature: float = 0.7
    voice: Optional[str] = None  # For realtime models
    
    
# Model registry with capabilities
MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # Chat/Planning models
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        purpose=ModelPurpose.CHAT,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=True,
        max_tokens=16384,
        default_temperature=0.7,
    ),
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        purpose=ModelPurpose.CHAT,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=True,
        max_tokens=16384,
        default_temperature=0.7,
    ),
    "gpt-4-turbo": ModelConfig(
        name="gpt-4-turbo",
        purpose=ModelPurpose.CHAT,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=True,
        max_tokens=4096,
        default_temperature=0.7,
    ),
    "gpt-4-turbo-preview": ModelConfig(
        name="gpt-4-turbo-preview",
        purpose=ModelPurpose.PLANNING,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=True,
        max_tokens=4096,
        default_temperature=0.3,
    ),
    # Realtime voice models
    "gpt-4o-realtime-preview": ModelConfig(
        name="gpt-4o-realtime-preview",
        purpose=ModelPurpose.VOICE_REALTIME,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=False,
        max_tokens=4096,
        default_temperature=0.8,
        voice="alloy",
    ),
    "gpt-4o-realtime-preview-2024-12-17": ModelConfig(
        name="gpt-4o-realtime-preview-2024-12-17",
        purpose=ModelPurpose.VOICE_REALTIME,
        supports_tools=True,
        supports_streaming=True,
        supports_json_mode=False,
        max_tokens=4096,
        default_temperature=0.8,
        voice="alloy",
    ),
}


class ModelManager:
    """
    Manages OpenAI model selection and configuration.
    
    Usage:
        manager = ModelManager()
        
        # Get model for chat
        chat_model = manager.get_model(ModelPurpose.CHAT)
        
        # Get model for voice
        voice_model = manager.get_model(ModelPurpose.VOICE_REALTIME)
        
        # Create client for specific purpose
        client, config = manager.create_client_for_purpose(ModelPurpose.PLANNING)
    """
    
    def __init__(self):
        self._clients: Dict[str, OpenAI] = {}
        self._load_settings()
    
    def _load_settings(self):
        """Load model settings from environment."""
        # Chat model (for planning, orchestration, text tasks)
        self.chat_model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o')
        
        # Realtime model (for voice conversations)
        self.realtime_model = getattr(settings, 'OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
        
        # Voice settings
        self.realtime_voice = getattr(settings, 'OPENAI_REALTIME_VOICE', 'alloy')
        self.realtime_api_url = getattr(settings, 'OPENAI_REALTIME_API_URL', 'wss://api.openai.com/v1/realtime')
        
        logger.info("model_manager_initialized", 
                   chat_model=self.chat_model, 
                   realtime_model=self.realtime_model,
                   voice=self.realtime_voice)
    
    def get_model(self, purpose: ModelPurpose) -> str:
        """
        Get the appropriate model name for a given purpose.
        
        Args:
            purpose: The intended use case
            
        Returns:
            Model name string
        """
        if purpose == ModelPurpose.VOICE_REALTIME:
            return self.realtime_model
        elif purpose in (ModelPurpose.CHAT, ModelPurpose.PLANNING, ModelPurpose.STRUCTURED_OUTPUT):
            return self._ensure_chat_compatible(self.chat_model)
        else:
            return self.chat_model
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return MODEL_REGISTRY.get(model_name)
    
    def _ensure_chat_compatible(self, model: str) -> str:
        """
        Ensure the model is compatible with chat completions API.
        Realtime models should NOT be used for chat.
        """
        model_lower = model.lower()
        
        # Realtime models are not compatible with chat API
        if 'realtime' in model_lower:
            logger.warning("realtime_model_for_chat_fallback", 
                         configured=model, 
                         fallback="gpt-4o")
            return "gpt-4o"
        
        # Legacy instruct/completion models
        non_chat = ('instruct', 'text-', 'davinci', 'curie', 'babbage', 'ada')
        if any(sub in model_lower for sub in non_chat):
            logger.warning("non_chat_model_fallback", 
                         configured=model, 
                         fallback="gpt-4o-mini")
            return "gpt-4o-mini"
        
        return model
    
    def create_client(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> OpenAI:
        """Create an OpenAI client."""
        return OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            timeout=timeout,
            max_retries=max_retries,
        )
    
    def create_client_for_purpose(
        self,
        purpose: ModelPurpose,
        **kwargs
    ) -> tuple[OpenAI, ModelConfig]:
        """
        Create a client configured for a specific purpose.
        
        Args:
            purpose: The intended use case
            **kwargs: Additional client configuration
            
        Returns:
            Tuple of (OpenAI client, ModelConfig)
        """
        model_name = self.get_model(purpose)
        config = self.get_model_config(model_name) or ModelConfig(
            name=model_name,
            purpose=purpose,
        )
        
        client = self.create_client(**kwargs)
        return client, config
    
    def get_realtime_config(self) -> Dict[str, Any]:
        """
        Get configuration for OpenAI Realtime API connection.
        
        Returns:
            Dict with websocket URL, model, voice, and headers
        """
        return {
            "url": self.realtime_api_url,
            "model": self.realtime_model,
            "voice": self.realtime_voice,
            "headers": {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            },
            "session_config": {
                "modalities": ["audio", "text"],
                "voice": self.realtime_voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "input_audio_transcription": {"model": "whisper-1"},
            },
        }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with their capabilities."""
        return [
            {
                "name": config.name,
                "purpose": config.purpose.value,
                "supports_tools": config.supports_tools,
                "supports_streaming": config.supports_streaming,
                "voice": config.voice,
            }
            for config in MODEL_REGISTRY.values()
        ]


# Singleton instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the singleton ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

