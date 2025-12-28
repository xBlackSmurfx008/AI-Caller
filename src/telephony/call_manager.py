"""Call manager for handling active calls and OpenAI voice agent connections"""

import asyncio
from typing import Dict, Optional
from sqlalchemy.orm import Session

from src.ai.openai_client import OpenAIRealtimeClient
from src.ai.conversation_manager import ConversationManager
from src.ai.agent_personality import get_personality_loader
from src.telephony.telephony_bridge import TelephonyBridge
from src.telephony.media_stream import MediaStreamHandler
from src.database.database import get_db
from src.database.models import Call, BusinessConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CallManager:
    """Manages active calls and their OpenAI voice agent connections"""

    def __init__(self):
        """Initialize call manager"""
        self.active_bridges: Dict[str, TelephonyBridge] = {}
        self.media_stream_handler = MediaStreamHandler()
        self.personality_loader = get_personality_loader()

    async def start_call_bridge(
        self,
        call_id: str,
        call_sid: str,
        db: Optional[Session] = None,
    ) -> TelephonyBridge:
        """
        Start OpenAI voice agent bridge for a call
        
        Args:
            call_id: Internal call ID
            call_sid: Twilio call SID
            db: Database session
            
        Returns:
            TelephonyBridge instance
        """
        if db is None:
            db = next(get_db())

        try:
            # Get call record
            call = db.query(Call).filter(Call.id == call_id).first()
            if not call:
                raise ValueError(f"Call {call_id} not found")

            # Get business config if available
            business_config = None
            system_prompt = None
            instructions = None
            agent_personality_name = None
            voice = "alloy"
            temperature = 0.8

            if call.business_id:
                business_config = db.query(BusinessConfig).filter(
                    BusinessConfig.id == call.business_id
                ).first()

            # Get agent personality from metadata or business config
            if call.meta_data:
                agent_personality_name = call.meta_data.get("agent_personality")
            
            # If no personality in metadata, try business config
            if not agent_personality_name and business_config:
                config_data = business_config.config_data or {}
                agent_personality_name = config_data.get("agent_personality")
                voice = config_data.get("voice", voice)
                temperature = config_data.get("temperature", temperature)

            # Load personality if specified
            personality = None
            if agent_personality_name:
                personality = self.personality_loader.get_personality(agent_personality_name)
                if personality:
                    system_prompt = personality.system_prompt
                    voice_config = personality.voice_config
                    if voice_config:
                        voice = voice_config.get("voice", voice)
                        temperature = voice_config.get("temperature", temperature)

            # Build system prompt
            if not system_prompt:
                if business_config:
                    config_data = business_config.config_data or {}
                    system_prompt = config_data.get("system_prompt", "You are a helpful AI assistant.")
                else:
                    system_prompt = "You are a helpful AI assistant handling a phone call. Be professional, friendly, and concise."

            # Add business context if available
            if business_config:
                instructions = f"Business: {business_config.name}\n"
                instructions += f"Type: {business_config.type}\n"

            # Create OpenAI client
            openai_client = OpenAIRealtimeClient(business_id=call.business_id)

            # Create conversation manager
            conversation_manager = ConversationManager(call_id=call_id)

            # Create telephony bridge
            bridge = TelephonyBridge(
                call_id=call_id,
                call_sid=call_sid,
                openai_client=openai_client,
                conversation_manager=conversation_manager,
                media_stream_handler=self.media_stream_handler,
            )

            # Start the bridge
            await bridge.start(
                system_prompt=system_prompt,
                instructions=instructions,
            )

            # Store bridge
            self.active_bridges[call_sid] = bridge

            logger.info(
                "call_bridge_started",
                call_id=call_id,
                call_sid=call_sid,
                personality=agent_personality_name,
            )

            return bridge

        except Exception as e:
            logger.error(
                "call_bridge_start_failed",
                error=str(e),
                call_id=call_id,
                call_sid=call_sid,
            )
            raise

    async def handle_media_stream_audio(
        self,
        call_sid: str,
        audio_data: bytes,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Handle audio from Twilio media stream and route to OpenAI
        
        Args:
            call_sid: Twilio call SID
            audio_data: Audio data bytes
            metadata: Optional metadata
        """
        bridge = self.active_bridges.get(call_sid)
        if not bridge:
            logger.warning("no_bridge_for_call", call_sid=call_sid)
            return

        try:
            await bridge.handle_twilio_audio(audio_data, metadata)
        except Exception as e:
            logger.error(
                "media_stream_audio_error",
                error=str(e),
                call_sid=call_sid,
            )

    async def stop_call_bridge(self, call_sid: str) -> None:
        """
        Stop OpenAI voice agent bridge for a call
        
        Args:
            call_sid: Twilio call SID
        """
        bridge = self.active_bridges.pop(call_sid, None)
        if bridge:
            try:
                await bridge.stop()
                logger.info("call_bridge_stopped", call_sid=call_sid)
            except Exception as e:
                logger.error(
                    "call_bridge_stop_error",
                    error=str(e),
                    call_sid=call_sid,
                )

    def get_bridge(self, call_sid: str) -> Optional[TelephonyBridge]:
        """
        Get bridge for a call
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            TelephonyBridge or None
        """
        return self.active_bridges.get(call_sid)

    def is_call_active(self, call_sid: str) -> bool:
        """
        Check if call has active bridge
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if bridge is active
        """
        return call_sid in self.active_bridges


# Global instance
_call_manager: Optional[CallManager] = None


def get_call_manager() -> CallManager:
    """Get global call manager instance"""
    global _call_manager
    if _call_manager is None:
        _call_manager = CallManager()
    return _call_manager

