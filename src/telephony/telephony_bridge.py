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
        # Resampler state for continuous streams (audioop.ratecv)
        self._twilio_to_openai_state = None
        self._openai_to_twilio_state = None

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
        Convert audio sample rate for PCM16 mono audio.

        Notes:
        - `audioop` was removed in Python 3.13+. This code must run on Python 3.14 in your env.
        - We therefore implement a simple, deterministic resampler that is correct for the
          common 8kHz <-> 24kHz conversion used by Twilio <-> OpenAI.
        
        Args:
            audio_data: Input PCM16 audio data
            from_sample_rate: Source sample rate
            to_sample_rate: Target sample rate
            
        Returns:
            Converted audio data
        """
        if from_sample_rate == to_sample_rate:
            return audio_data

        try:
            # Fast paths for the only rates we care about right now.
            if from_sample_rate == 8000 and to_sample_rate == 24000:
                return _pcm16_resample_x3(audio_data)
            if from_sample_rate == 24000 and to_sample_rate == 8000:
                return _pcm16_resample_div3(audio_data)

            # Generic fallback (linear interpolation) for other ratios.
            return _pcm16_resample_linear(audio_data, from_sample_rate, to_sample_rate)

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


def _pcm16_unpack_mono(pcm16: bytes) -> list[int]:
    if not pcm16:
        return []
    if len(pcm16) % 2 != 0:
        pcm16 = pcm16[:-1]
    return list(struct.unpack(f"<{len(pcm16)//2}h", pcm16))


def _pcm16_pack_mono(samples: list[int]) -> bytes:
    if not samples:
        return b""
    # Clamp to int16
    clamped = [max(-32768, min(32767, int(s))) for s in samples]
    return struct.pack(f"<{len(clamped)}h", *clamped)


def _pcm16_resample_x3(pcm16_8k: bytes) -> bytes:
    """
    Upsample PCM16 mono from 8kHz -> 24kHz (exact factor 3).
    Uses linear interpolation between adjacent samples.
    """
    src = _pcm16_unpack_mono(pcm16_8k)
    if len(src) < 2:
        return pcm16_8k
    out: list[int] = []
    for i in range(len(src) - 1):
        s0 = src[i]
        s1 = src[i + 1]
        out.append(s0)
        out.append(int(s0 + (s1 - s0) * (1 / 3)))
        out.append(int(s0 + (s1 - s0) * (2 / 3)))
    out.append(src[-1])
    return _pcm16_pack_mono(out)


def _pcm16_resample_div3(pcm16_24k: bytes) -> bytes:
    """
    Downsample PCM16 mono from 24kHz -> 8kHz (exact factor 3).
    Simple decimation (take every 3rd sample).
    """
    src = _pcm16_unpack_mono(pcm16_24k)
    if not src:
        return b""
    out = src[::3]
    return _pcm16_pack_mono(out)


def _pcm16_resample_linear(pcm16: bytes, from_hz: int, to_hz: int) -> bytes:
    """Generic linear interpolation resampler for PCM16 mono."""
    src = _pcm16_unpack_mono(pcm16)
    if len(src) < 2 or from_hz <= 0 or to_hz <= 0:
        return pcm16
    ratio = to_hz / from_hz
    out_len = max(1, int(len(src) * ratio))
    out: list[int] = []
    for j in range(out_len):
        pos = j / ratio
        i = int(pos)
        frac = pos - i
        if i >= len(src) - 1:
            out.append(src[-1])
        else:
            out.append(int(src[i] + (src[i + 1] - src[i]) * frac))
    return _pcm16_pack_mono(out)

