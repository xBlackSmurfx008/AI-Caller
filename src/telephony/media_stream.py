"""Media stream handler for Twilio Media Streams"""

import asyncio
import base64
import json
import struct
from typing import Optional, Callable, Dict, Any, Awaitable

from fastapi import WebSocket, WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MediaStreamHandler:
    """Handler for Twilio Media Streams"""

    def __init__(self):
        """Initialize media stream handler"""
        # Keyed by Twilio CallSid
        self.active_streams: Dict[str, Dict[str, Any]] = {}

    def generate_twiml(self, websocket_url: str, parameters: Optional[Dict[str, str]] = None) -> str:
        """
        Generate TwiML for starting media stream
        
        Args:
            websocket_url: WebSocket URL for media stream
            parameters: Optional custom parameters sent to Twilio in the `start` event
            
        Returns:
            TwiML XML string
        """
        # Use raw TwiML to avoid SDK version mismatches and to support <Connect><Stream>
        # required for bidirectional Media Streams.
        #
        # Twilio provides CallSid/StreamSid in the initial `start` event payload; it does NOT
        # template variables like {{CallSid}} into the Stream URL.
        websocket_url_escaped = (
            websocket_url.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        params_xml = ""
        if parameters:
            # Twilio expects <Parameter name="..." value="..."/> under <Stream>
            safe_items = []
            for k, v in parameters.items():
                if v is None:
                    continue
                k2 = str(k).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
                v2 = str(v).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
                safe_items.append(f'<Parameter name="{k2}" value="{v2}" />')
            params_xml = "".join(safe_items)

        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Say>Connecting to AI assistant...</Say>"
            "<Connect>"
            f'<Stream url="{websocket_url_escaped}">{params_xml}</Stream>'
            "</Connect>"
            "</Response>"
        )

    async def handle_media_stream(
        self,
        websocket: WebSocket,
        audio_handler: Optional[Callable] = None,
        on_start: Optional[Callable[[str, str, dict], Awaitable[None]]] = None,
        on_stop: Optional[Callable[[str, str, dict], Awaitable[None]]] = None,
    ) -> None:
        """
        Handle incoming media stream from Twilio
        
        Args:
            websocket: WebSocket connection
            audio_handler: Optional callback for processing audio
            on_start: Optional callback invoked after a `start` event (call_sid, stream_sid, event)
            on_stop: Optional callback invoked after a `stop` event (call_sid, stream_sid, event)
        """
        await websocket.accept()
        call_sid: Optional[str] = None
        stream_sid: Optional[str] = None
        logger.info("media_stream_connected")

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                event_type = data.get("event")

                if event_type == "media":
                    # Handle audio data
                    media = data.get("media", {}) or {}
                    audio_b64 = media.get("payload")
                    
                    # We need a callSid mapping from the initial `start` event.
                    if not call_sid or not stream_sid:
                        continue

                    if audio_b64 and audio_handler:
                        # Decode base64 audio (Twilio Media Streams uses 8kHz µ-law)
                        try:
                            ulaw_audio = base64.b64decode(audio_b64)
                            pcm16_audio = _ulaw_bytes_to_pcm16_bytes(ulaw_audio)
                            await audio_handler(call_sid, pcm16_audio, data)
                        except Exception as e:
                            logger.error(
                                "audio_processing_error",
                                error=str(e),
                                call_sid=call_sid,
                                stream_sid=stream_sid,
                            )

                elif event_type == "start":
                    start = data.get("start", {}) or {}
                    # Twilio typically sends these in the nested `start` object
                    call_sid = start.get("callSid") or data.get("callSid")
                    stream_sid = start.get("streamSid") or data.get("streamSid")

                    if call_sid and stream_sid:
                        self.active_streams[call_sid] = {
                            "websocket": websocket,
                            "stream_sid": stream_sid,
                        }
                        logger.info("media_stream_started", call_sid=call_sid, stream_sid=stream_sid)
                        if on_start:
                            try:
                                await on_start(call_sid, stream_sid, data)
                            except Exception as e:
                                logger.error("media_stream_on_start_error", error=str(e), call_sid=call_sid, stream_sid=stream_sid)
                    else:
                        logger.warning("media_stream_start_missing_ids", start_event=data)

                elif event_type == "stop":
                    # stop event often includes streamSid at top-level; keep best-effort
                    stop_stream_sid = data.get("streamSid") or (data.get("stop", {}) or {}).get("streamSid")
                    logger.info("media_stream_stopped", call_sid=call_sid, stream_sid=stop_stream_sid or stream_sid)
                    if call_sid and stream_sid and on_stop:
                        try:
                            await on_stop(call_sid, stream_sid, data)
                        except Exception as e:
                            logger.error("media_stream_on_stop_error", error=str(e), call_sid=call_sid, stream_sid=stream_sid)
                    break

        except WebSocketDisconnect:
            logger.info("media_stream_disconnected", call_sid=call_sid, stream_sid=stream_sid)
        except Exception as e:
            logger.error("media_stream_error", error=str(e), call_sid=call_sid, stream_sid=stream_sid)
        finally:
            if call_sid:
                self.active_streams.pop(call_sid, None)

    async def send_audio(
        self,
        call_sid: str,
        audio_data: bytes,
        sample_rate: int = 8000,
    ) -> bool:
        """
        Send audio data to Twilio media stream
        
        Args:
            call_sid: Twilio call SID
            audio_data: Audio data bytes (PCM, 16-bit, mono)
            sample_rate: Sample rate (default 8000 for Twilio)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if call_sid not in self.active_streams:
            logger.warning("no_active_stream", call_sid=call_sid)
            return False

        entry = self.active_streams.get(call_sid) or {}
        websocket: Optional[WebSocket] = entry.get("websocket")
        stream_sid: Optional[str] = entry.get("stream_sid")

        if websocket is None or stream_sid is None:
            logger.warning("no_active_stream", call_sid=call_sid)
            return False

        try:
            # Twilio expects 8kHz µ-law frames in the payload.
            # We assume `audio_data` is PCM16 @ 8kHz. Convert to µ-law.
            ulaw_audio = _pcm16_bytes_to_ulaw_bytes(audio_data)
            audio_b64 = base64.b64encode(ulaw_audio).decode("utf-8")

            # Create media message
            message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": audio_b64,
                },
            }

            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("audio_send_error", error=str(e), call_sid=call_sid)
            return False


# --- µ-law (G.711) helpers (stdlib-only; `audioop` removed in Python 3.13+) ---

_ULAW_BIAS = 0x84
_ULAW_CLIP = 32635


def _ulaw_decode_byte(b: int) -> int:
    """Decode one 8-bit µ-law byte to a 16-bit signed PCM sample (int)."""
    b = (~b) & 0xFF
    sign = b & 0x80
    exponent = (b >> 4) & 0x07
    mantissa = b & 0x0F
    magnitude = ((mantissa << 1) + 1) << (exponent + 2)
    magnitude -= _ULAW_BIAS
    return -magnitude if sign else magnitude


def _ulaw_encode_sample(pcm: int) -> int:
    """Encode one 16-bit signed PCM sample (int) into an 8-bit µ-law byte."""
    sign = 0
    if pcm < 0:
        sign = 0x80
        pcm = -pcm
    if pcm > _ULAW_CLIP:
        pcm = _ULAW_CLIP
    pcm = pcm + _ULAW_BIAS

    # Determine exponent (segment)
    exponent = 7
    exp_mask = 0x4000
    for e in range(7):
        if pcm & exp_mask:
            exponent = e
            break
        exp_mask >>= 1

    mantissa = (pcm >> (exponent + 3)) & 0x0F
    ulaw = ~(sign | ((7 - exponent) << 4) | mantissa) & 0xFF
    return ulaw


def _ulaw_bytes_to_pcm16_bytes(ulaw: bytes) -> bytes:
    if not ulaw:
        return b""
    out = bytearray(len(ulaw) * 2)
    o = 0
    for b in ulaw:
        s = _ulaw_decode_byte(b)
        struct.pack_into("<h", out, o, s)
        o += 2
    return bytes(out)


def _pcm16_bytes_to_ulaw_bytes(pcm16: bytes) -> bytes:
    if not pcm16:
        return b""
    if len(pcm16) % 2 != 0:
        pcm16 = pcm16[:-1]
    samples = struct.unpack(f"<{len(pcm16)//2}h", pcm16)
    out = bytearray(len(samples))
    for i, s in enumerate(samples):
        out[i] = _ulaw_encode_sample(int(s))
    return bytes(out)

    def is_stream_active(self, call_sid: str) -> bool:
        """
        Check if media stream is active for a call
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            True if stream is active
        """
        return call_sid in self.active_streams

    def close_stream(self, call_sid: str) -> None:
        """
        Close media stream for a call
        
        Args:
            call_sid: Twilio call SID
        """
        if call_sid in self.active_streams:
            entry = self.active_streams.pop(call_sid)
            websocket = entry.get("websocket")
            if websocket:
                asyncio.create_task(websocket.close())
            logger.info("media_stream_closed", call_sid=call_sid)

