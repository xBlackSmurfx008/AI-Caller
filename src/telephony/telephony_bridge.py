"""Bridge between Twilio Media Streams and OpenAI Realtime API"""

import asyncio
import struct
from typing import Optional, Callable

from src.ai.openai_client import OpenAIRealtimeClient
from src.ai.conversation_manager import ConversationManager
from src.telephony.media_stream import MediaStreamHandler
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TelephonyBridge:
    """Bridge connecting Twilio Media Streams to OpenAI Realtime API"""

    def __init__(
        self,
        call_id: str,
        call_sid: str,
        openai_client: OpenAIRealtimeClient,
        conversation_manager: ConversationManager,
        media_stream_handler: MediaStreamHandler,
    ):
        """
        Initialize telephony bridge
        
        Args:
            call_id: Internal call ID
            call_sid: Twilio call SID
            openai_client: OpenAI Realtime API client
            conversation_manager: Conversation manager
            media_stream_handler: Media stream handler
        """
        self.call_id = call_id
        self.call_sid = call_sid
        self.openai_client = openai_client
        self.conversation_manager = conversation_manager
        self.media_stream_handler = media_stream_handler
        self.session_id = f"{call_id}_{call_sid}"
        self.is_active = False

    async def start(
        self,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
    ) -> None:
        """
        Start the bridge connection
        
        Args:
            system_prompt: System prompt for OpenAI
            instructions: Additional instructions
        """
        try:
            # Create OpenAI session
            await self.openai_client.create_session(
                session_id=self.session_id,
                system_prompt=system_prompt,
                instructions=instructions,
                on_audio=self._handle_openai_audio,
                on_transcript=self._handle_openai_transcript,
            )

            self.is_active = True
            logger.info("telephony_bridge_started", call_id=self.call_id, call_sid=self.call_sid)

        except Exception as e:
            logger.error("telephony_bridge_start_failed", error=str(e), call_id=self.call_id)
            raise

    async def _handle_openai_audio(
        self,
        session_id: str,
        audio_data: bytes,
    ) -> None:
        """
        Handle audio from OpenAI and send to Twilio
        
        Args:
            session_id: OpenAI session ID
            audio_data: PCM16 audio data
        """
        if not self.is_active:
            return

        try:
            # Convert audio format if needed (OpenAI uses PCM16, Twilio expects PCM16)
            # Both use 16-bit PCM, but we may need to adjust sample rate
            # OpenAI typically uses 24kHz, Twilio uses 8kHz
            converted_audio = self._convert_audio_format(
                audio_data,
                from_sample_rate=24000,
                to_sample_rate=8000,
            )

            # Send to Twilio media stream
            await self.media_stream_handler.send_audio(
                call_sid=self.call_sid,
                audio_data=converted_audio,
                sample_rate=8000,
            )

        except Exception as e:
            logger.error("openai_audio_handling_error", error=str(e), call_id=self.call_id)

    async def _handle_openai_transcript(
        self,
        session_id: str,
        transcript: str,
        speaker: str,
        is_delta: bool = False,
    ) -> None:
        """
        Handle transcript from OpenAI
        
        Args:
            session_id: OpenAI session ID
            transcript: Transcript text
            speaker: "user" or "assistant"
            is_delta: Whether this is a delta update
        """
        if not self.is_active:
            return

        try:
            # Map OpenAI speaker to our format
            our_speaker = "ai" if speaker == "assistant" else "customer"

            # Store transcript in conversation manager
            if not is_delta:
                # Complete transcript
                await self.conversation_manager.add_interaction(
                    speaker=our_speaker,
                    text=transcript,
                )
            # Note: For deltas, we might want to accumulate them
            # For now, we'll only store complete transcripts

        except Exception as e:
            logger.error("openai_transcript_handling_error", error=str(e), call_id=self.call_id)

    async def handle_twilio_audio(
        self,
        audio_data: bytes,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Handle audio from Twilio and send to OpenAI
        
        Args:
            audio_data: PCM16 audio data from Twilio (8kHz)
            metadata: Optional metadata
        """
        if not self.is_active:
            return

        try:
            # Convert audio format if needed
            # Twilio uses 8kHz, OpenAI Realtime API expects 24kHz
            converted_audio = self._convert_audio_format(
                audio_data,
                from_sample_rate=8000,
                to_sample_rate=24000,
            )

            # Send to OpenAI Realtime API
            await self.openai_client.send_audio(
                session_id=self.session_id,
                audio_data=converted_audio,
            )

        except Exception as e:
            logger.error("twilio_audio_handling_error", error=str(e), call_id=self.call_id)

    def _convert_audio_format(
        self,
        audio_data: bytes,
        from_sample_rate: int,
        to_sample_rate: int,
    ) -> bytes:
        """
        Convert audio format (simple resampling)
        
        Note: This is a simplified implementation.
        For production, consider using a proper audio library like librosa or pydub.
        
        Args:
            audio_data: Input PCM16 audio data
            from_sample_rate: Source sample rate
            to_sample_rate: Target sample rate
            
        Returns:
            Converted audio data
        """
        if from_sample_rate == to_sample_rate:
            return audio_data

        # Simple linear interpolation resampling
        # This is a basic implementation - for production, use proper resampling
        try:
            # Unpack 16-bit PCM samples
            samples = struct.unpack(f"<{len(audio_data) // 2}h", audio_data)

            # Calculate resampling ratio
            ratio = to_sample_rate / from_sample_rate

            # Resample (linear interpolation)
            if ratio > 1:
                # Upsample
                new_samples = []
                for i in range(len(samples)):
                    new_samples.append(samples[i])
                    # Interpolate additional samples
                    if i < len(samples) - 1:
                        for j in range(1, int(ratio)):
                            interpolated = int(
                                samples[i] + (samples[i + 1] - samples[i]) * (j / ratio)
                            )
                            new_samples.append(interpolated)
            else:
                # Downsample
                step = int(1 / ratio)
                new_samples = samples[::step]

            # Pack back to bytes
            return struct.pack(f"<{len(new_samples)}h", *new_samples)

        except Exception as e:
            logger.error("audio_conversion_error", error=str(e))
            # Return original if conversion fails
            return audio_data

    async def send_text(self, text: str) -> None:
        """
        Send text message to OpenAI
        
        Args:
            text: Text to send
        """
        if not self.is_active:
            return

        try:
            await self.openai_client.send_text(
                session_id=self.session_id,
                text=text,
            )
        except Exception as e:
            logger.error("text_send_error", error=str(e), call_id=self.call_id)

    async def interrupt(self) -> None:
        """Interrupt current OpenAI response"""
        if not self.is_active:
            return

        try:
            await self.openai_client.interrupt(self.session_id)
        except Exception as e:
            logger.error("interrupt_error", error=str(e), call_id=self.call_id)

    async def stop(self) -> None:
        """Stop the bridge connection"""
        if not self.is_active:
            return

        try:
            self.is_active = False
            await self.openai_client.close_session(self.session_id)
            logger.info("telephony_bridge_stopped", call_id=self.call_id, call_sid=self.call_sid)
        except Exception as e:
            logger.error("telephony_bridge_stop_error", error=str(e), call_id=self.call_id)

