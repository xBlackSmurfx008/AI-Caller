"""Media stream handler for Twilio Media Streams"""

import asyncio
import base64
import json
from typing import Optional, Callable, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Start, Stream

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MediaStreamHandler:
    """Handler for Twilio Media Streams"""

    def __init__(self):
        """Initialize media stream handler"""
        self.active_streams: Dict[str, WebSocket] = {}

    def generate_twiml(self, websocket_url: str) -> str:
        """
        Generate TwiML for starting media stream
        
        Args:
            websocket_url: WebSocket URL for media stream
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        start = Start()
        stream = Stream(url=websocket_url)
        stream.parameter(name="callSid", value="{{CallSid}}")
        stream.parameter(name="from", value="{{From}}")
        stream.parameter(name="to", value="{{To}}")
        start.stream(stream)
        response.append(start)
        response.say("Connecting to AI assistant...")
        return str(response)

    async def handle_media_stream(
        self,
        websocket: WebSocket,
        call_sid: str,
        audio_handler: Optional[Callable] = None,
    ) -> None:
        """
        Handle incoming media stream from Twilio
        
        Args:
            websocket: WebSocket connection
            call_sid: Twilio call SID
            audio_handler: Optional callback for processing audio
        """
        await websocket.accept()
        self.active_streams[call_sid] = websocket

        logger.info("media_stream_connected", call_sid=call_sid)

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                event_type = data.get("event")

                if event_type == "media":
                    # Handle audio data
                    payload = data.get("payload", {})
                    audio_data = payload.get("payload")
                    
                    if audio_data and audio_handler:
                        # Decode base64 audio
                        try:
                            decoded_audio = base64.b64decode(audio_data)
                            await audio_handler(call_sid, decoded_audio, data)
                        except Exception as e:
                            logger.error(
                                "audio_processing_error",
                                error=str(e),
                                call_sid=call_sid,
                            )

                elif event_type == "start":
                    logger.info("media_stream_started", call_sid=call_sid)

                elif event_type == "stop":
                    logger.info("media_stream_stopped", call_sid=call_sid)
                    break

        except WebSocketDisconnect:
            logger.info("media_stream_disconnected", call_sid=call_sid)
        except Exception as e:
            logger.error("media_stream_error", error=str(e), call_sid=call_sid)
        finally:
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

        websocket = self.active_streams[call_sid]

        try:
            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            # Create media message
            message = {
                "event": "media",
                "streamSid": call_sid,
                "media": {
                    "payload": audio_b64,
                },
            }

            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("audio_send_error", error=str(e), call_sid=call_sid)
            return False

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
            websocket = self.active_streams.pop(call_sid)
            asyncio.create_task(websocket.close())
            logger.info("media_stream_closed", call_sid=call_sid)

