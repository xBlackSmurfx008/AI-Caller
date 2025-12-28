"""OpenAI Realtime API client"""

import asyncio
import base64
import json
from typing import Optional, Dict, Any, Callable, List

import websockets
from openai import OpenAI

from src.utils.config import get_settings
from src.utils.errors import OpenAIError
from src.utils.logging import get_logger
from src.ai.tool_handlers import ToolHandlers

logger = get_logger(__name__)
settings = get_settings()


class OpenAIRealtimeClient:
    """Client for OpenAI Realtime API"""

    def __init__(self, business_id: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            business_id: Optional business ID for tool handlers
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.api_url = settings.OPENAI_REALTIME_API_URL
        self.model = settings.OPENAI_MODEL
        self.active_sessions: Dict[str, Any] = {}
        self.tool_handlers = ToolHandlers(business_id=business_id)
        self.pending_function_calls: Dict[str, Dict[str, Any]] = {}

    async def create_session(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        voice: str = "alloy",
        temperature: float = 0.8,
        max_response_output_tokens: int = 4096,
        on_audio: Optional[Callable] = None,
        on_transcript: Optional[Callable] = None,
        on_event: Optional[Callable] = None,
    ) -> None:
        """
        Create a new Realtime API session
        
        Args:
            session_id: Unique session identifier
            system_prompt: System prompt for the assistant
            instructions: Additional instructions
            tools: List of tools/functions available
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            temperature: Temperature for response generation
            max_response_output_tokens: Maximum tokens in response
            on_audio: Callback for audio events
            on_transcript: Callback for transcript events
            on_event: Callback for all events
        """
        try:
            # Create session configuration
            session_config = {
                "model": self.model,
                "voice": voice,
                "temperature": temperature,
                "max_response_output_tokens": max_response_output_tokens,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "modalities": ["audio", "text"],
            }

            if system_prompt:
                session_config["instructions"] = system_prompt

            if instructions:
                if "instructions" in session_config:
                    session_config["instructions"] += f"\n\n{instructions}"
                else:
                    session_config["instructions"] = instructions

            if tools:
                session_config["tools"] = tools

            # Create WebSocket connection
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1",
            }

            # Connect to Realtime API
            uri = f"{self.api_url}?model={self.model}"
            websocket = await websockets.connect(
                uri,
                extra_headers=headers,
            )

            # Send session update with configuration
            await self._send_event(websocket, {
                "type": "session.update",
                "session": session_config,
            })

            # Store session
            self.active_sessions[session_id] = {
                "websocket": websocket,
                "config": session_config,
                "on_audio": on_audio,
                "on_transcript": on_transcript,
                "on_event": on_event,
            }

            # Start listening for events
            asyncio.create_task(self._listen_events(session_id, websocket))

            logger.info("openai_session_created", session_id=session_id)

        except Exception as e:
            logger.error("openai_session_creation_failed", error=str(e), session_id=session_id)
            raise OpenAIError(f"Failed to create OpenAI session: {str(e)}") from e

    async def _listen_events(self, session_id: str, websocket: Any) -> None:
        """Listen for events from OpenAI Realtime API"""
        try:
            async for message in websocket:
                try:
                    event = json.loads(message)
                    await self._handle_event(session_id, event)
                except json.JSONDecodeError as e:
                    logger.error("json_decode_error", error=str(e), session_id=session_id)
                except Exception as e:
                    logger.error("event_handling_error", error=str(e), session_id=session_id)
        except websockets.exceptions.ConnectionClosed:
            logger.info("openai_connection_closed", session_id=session_id)
        except Exception as e:
            logger.error("openai_listen_error", error=str(e), session_id=session_id)
        finally:
            self.active_sessions.pop(session_id, None)

    async def _handle_event(self, session_id: str, event: Dict[str, Any]) -> None:
        """Handle incoming event from OpenAI"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        event_type = event.get("type")

        # Handle audio events
        if event_type == "response.audio.delta":
            audio_data = event.get("delta")
            if audio_data and session["on_audio"]:
                # Decode base64 audio
                try:
                    decoded_audio = base64.b64decode(audio_data)
                    await session["on_audio"](session_id, decoded_audio)
                except Exception as e:
                    logger.error("audio_decode_error", error=str(e), session_id=session_id)

        # Handle transcript events
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript")
            if transcript and session["on_transcript"]:
                await session["on_transcript"](session_id, transcript, "user")

        elif event_type == "response.audio_transcript.delta":
            transcript_delta = event.get("delta")
            if transcript_delta and session["on_transcript"]:
                await session["on_transcript"](session_id, transcript_delta, "assistant", is_delta=True)

        # Handle function call events (AgentKit abilities)
        elif event_type == "response.function_call_arguments.delta":
            # Accumulate function call arguments
            function_call_id = event.get("function_call_id")
            delta = event.get("delta", "")
            
            if function_call_id not in self.pending_function_calls:
                self.pending_function_calls[function_call_id] = {
                    "id": function_call_id,
                    "name": "",
                    "arguments": "",
                }
            
            self.pending_function_calls[function_call_id]["arguments"] += delta

        elif event_type == "response.function_call.done":
            # Function call is complete, execute it
            function_call = event.get("function_call", {})
            function_call_id = function_call.get("id")
            function_name = function_call.get("name")
            
            # Get accumulated arguments
            if function_call_id in self.pending_function_calls:
                arguments_str = self.pending_function_calls[function_call_id].get("arguments", "{}")
                self.pending_function_calls.pop(function_call_id, None)
            else:
                arguments_str = function_call.get("arguments", "{}")
            
            try:
                # Parse arguments
                arguments = json.loads(arguments_str) if arguments_str else {}
                
                # Execute tool
                logger.info(
                    "executing_tool",
                    session_id=session_id,
                    tool_name=function_name,
                    arguments=arguments,
                )
                
                result = await self.tool_handlers.handle_tool_call(
                    tool_name=function_name,
                    arguments=arguments,
                    call_id=session_id,
                )
                
                # Send tool result back to OpenAI
                await self._send_event(session["websocket"], {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "function_call_id": function_call_id,
                        "output": json.dumps(result),
                    },
                })
                
                logger.info(
                    "tool_execution_complete",
                    session_id=session_id,
                    tool_name=function_name,
                )
                
            except Exception as e:
                logger.error(
                    "tool_execution_error",
                    session_id=session_id,
                    tool_name=function_name,
                    error=str(e),
                )
                # Send error result
                await self._send_event(session["websocket"], {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "function_call_id": function_call_id,
                        "output": json.dumps({"error": str(e)}),
                    },
                })

        # Handle general events
        if session["on_event"]:
            await session["on_event"](session_id, event)

    async def _send_event(self, websocket: Any, event: Dict[str, Any]) -> None:
        """Send event to OpenAI Realtime API"""
        try:
            await websocket.send(json.dumps(event))
        except Exception as e:
            logger.error("event_send_error", error=str(e), event_type=event.get("type"))
            raise

    async def send_audio(
        self,
        session_id: str,
        audio_data: bytes,
    ) -> None:
        """
        Send audio data to OpenAI Realtime API
        
        Args:
            session_id: Session identifier
            audio_data: PCM16 audio data
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise OpenAIError(f"Session {session_id} not found")

        try:
            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            # Send input audio event
            await self._send_event(session["websocket"], {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            })

            # Commit audio buffer
            await self._send_event(session["websocket"], {
                "type": "input_audio_buffer.commit",
            })

        except Exception as e:
            logger.error("audio_send_error", error=str(e), session_id=session_id)
            raise OpenAIError(f"Failed to send audio: {str(e)}") from e

    async def send_text(
        self,
        session_id: str,
        text: str,
    ) -> None:
        """
        Send text input to OpenAI Realtime API
        
        Args:
            session_id: Session identifier
            text: Text to send
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise OpenAIError(f"Session {session_id} not found")

        try:
            await self._send_event(session["websocket"], {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": text,
                },
            })

        except Exception as e:
            logger.error("text_send_error", error=str(e), session_id=session_id)
            raise OpenAIError(f"Failed to send text: {str(e)}") from e

    async def interrupt(self, session_id: str) -> None:
        """
        Interrupt the current response
        
        Args:
            session_id: Session identifier
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise OpenAIError(f"Session {session_id} not found")

        try:
            await self._send_event(session["websocket"], {
                "type": "response.interrupt",
            })
        except Exception as e:
            logger.error("interrupt_error", error=str(e), session_id=session_id)
            raise OpenAIError(f"Failed to interrupt: {str(e)}") from e

    async def close_session(self, session_id: str) -> None:
        """
        Close a session
        
        Args:
            session_id: Session identifier
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return

        try:
            await session["websocket"].close()
            self.active_sessions.pop(session_id, None)
            logger.info("openai_session_closed", session_id=session_id)
        except Exception as e:
            logger.error("session_close_error", error=str(e), session_id=session_id)

    def is_session_active(self, session_id: str) -> bool:
        """
        Check if session is active
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is active
        """
        return session_id in self.active_sessions

