"""Twilio Media Streams <-> OpenAI Realtime bridge (voice-to-voice)."""

from __future__ import annotations

import asyncio
import base64
import json
import struct
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Awaitable, Callable, List
from datetime import datetime
import uuid

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.security.policy import Actor, decide_confirmation, PlannedToolCall, tool_risk, Risk, is_godfather
from src.agent.assistant import VoiceAssistant
from src.agent.tools import TOOLS as CHAT_TOOLS, TOOL_HANDLERS
from src.database.database import SessionLocal
from src.database.models import Task as TaskModel

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class _SessionState:
    ws: Any
    call_sid: str
    actor: Actor
    twilio_audio_sender: Optional[Callable[[bytes], Awaitable[None]]] = None
    last_user_transcript: str = ""
    last_confirmed: bool = False
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    reconnect_attempts: int = 0
    max_reconnect_attempts: int = 3
    is_connected: bool = True


class RealtimeCallBridge:
    """
    Manages an OpenAI Realtime WebSocket session for a Twilio call.

    Audio:
    - Twilio: 8kHz PCM16 (after µ-law decode) from `MediaStreamHandler`
    - OpenAI: 24kHz PCM16 (typical for realtime when using pcm16)
    """

    def __init__(self):
        self._sessions: Dict[str, _SessionState] = {}
        self._assistant = VoiceAssistant()
    
    def _realtime_tools(self) -> List[Dict[str, Any]]:
        """Convert chat tool schema to Realtime tool schema."""
        out: List[Dict[str, Any]] = []
        for t in CHAT_TOOLS:
            fn = (t or {}).get("function") or {}
            out.append(
                {
                    "type": "function",
                    "name": fn.get("name"),
                    "description": fn.get("description"),
                    "parameters": fn.get("parameters") or {"type": "object", "properties": {}},
                }
            )
        return out

    async def start(
        self,
        call_sid: str,
        actor: Actor,
        twilio_audio_sender: Optional[Callable[[bytes], Awaitable[None]]] = None,
    ) -> None:
        if call_sid in self._sessions:
            return

        await self._connect_websocket(call_sid, actor)
        st = self._sessions.get(call_sid)
        if not st:
            logger.error("realtime_session_missing_after_connect", call_sid=call_sid)
            return
        st.twilio_audio_sender = twilio_audio_sender
        # Poller to bridge UI approval -> tool output submission (dual confirmation).
        asyncio.create_task(self._poll_pending_loop(call_sid))

        # Provide session instructions: execute actions directly without asking for confirmation.
        instructions = (
            "You are Godfather's voice assistant. Speak naturally and concisely.\n"
            "You may perform actions like calling, texting, emailing, scheduling, and web research.\n"
            "Execute actions directly when instructed - do not ask for confirmation, just do it.\n"
            "If the caller is not Godfather, take a message and proceed with the request."
        )

        await self._send(
            st.ws,
            {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": instructions,
                    "voice": getattr(settings, "OPENAI_REALTIME_VOICE", None) or "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                    },
                    "input_audio_transcription": {"model": "whisper-1"},
                    "tools": self._realtime_tools(),
                },
            },
        )

        asyncio.create_task(self._listen(call_sid))
        logger.info("realtime_session_started", call_sid=call_sid)

    def _create_pending_task(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Create an awaiting_confirmation Task row for UI approval."""
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        db = SessionLocal()
        try:
            rec = TaskModel(
                task_id=task_id,
                status="awaiting_confirmation",
                task=f"[Realtime call] {tool_name}",
                requires_confirmation=True,
                planned_tool_calls=[{"name": tool_name, "arguments": tool_args}],
                policy_reasons=[f"requested via realtime call: {tool_name}"],
                created_at=now,
                updated_at=now,
            )
            db.add(rec)
            db.commit()
            return task_id
        finally:
            db.close()

    def _get_task_status(self, task_id: str) -> Optional[TaskModel]:
        db = SessionLocal()
        try:
            return db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
        finally:
            db.close()

    async def _poll_pending_loop(self, call_sid: str) -> None:
        """Poll DB for UI-approved tasks and submit tool outputs once voice-confirmed."""
        while True:
            st = self._sessions.get(call_sid)
            if not st:
                return
            if not st.pending_actions:
                await asyncio.sleep(1.0)
                continue

            # Only poll aggressively if at least one is voice-confirmed.
            any_voice_confirmed = any(p.get("voice_confirmed") for p in st.pending_actions)
            await asyncio.sleep(1.0 if any_voice_confirmed else 2.0)

            # Iterate over a copy to allow removal.
            for pending in list(st.pending_actions):
                task_id = pending.get("task_id")
                if not task_id or not pending.get("voice_confirmed"):
                    continue

                task = self._get_task_status(task_id)
                if not task:
                    continue

                status = task.status
                if status not in {"completed", "failed", "rejected"}:
                    continue

                item_id = pending.get("item_id")
                tool_call_id = pending.get("tool_call_id")
                if not item_id or not tool_call_id:
                    st.pending_actions.remove(pending)
                    continue

                if status == "completed":
                    # Confirm endpoint stores tool results in task.result.
                    result = task.result or {}
                    tool_results = (result.get("tool_results") or []) if isinstance(result, dict) else []
                    output_payload: Dict[str, Any] = {"success": True, "task_id": task_id}
                    if tool_results and isinstance(tool_results, list):
                        # Take first tool result for this pending action.
                        tr0 = tool_results[0] or {}
                        output_payload["tool_result"] = tr0.get("result", tr0)
                    await self._submit_tool_outputs(
                        st,
                        item_id=item_id,
                        tool_outputs=[{"tool_call_id": tool_call_id, "output": json.dumps(output_payload)}],
                    )
                else:
                    await self._submit_tool_outputs(
                        st,
                        item_id=item_id,
                        tool_outputs=[{"tool_call_id": tool_call_id, "output": json.dumps({"error": status, "task_id": task_id})}],
                    )

                st.pending_actions.remove(pending)
    
    async def _connect_websocket(self, call_sid: str, actor: Actor) -> None:
        """Connect to OpenAI Realtime API with error handling."""
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        }
        model = getattr(settings, "OPENAI_REALTIME_MODEL", None) or "gpt-4o-realtime-preview"
        uri = f"{settings.OPENAI_REALTIME_API_URL}?model={model}"

        try:
            ws = await websockets.connect(
                uri,
                extra_headers=headers,
                ping_interval=20,  # Keep connection alive
                ping_timeout=10,
                close_timeout=10,
            )
            self._sessions[call_sid] = _SessionState(ws=ws, call_sid=call_sid, actor=actor)
            await self._configure_session(call_sid)
        except Exception as e:
            logger.error("realtime_connection_failed", call_sid=call_sid, error=str(e))
            raise
    
    async def _configure_session(self, call_sid: str) -> None:
        """Configure the Realtime API session."""
        st = self._sessions.get(call_sid)
        if not st:
            return

    async def stop(self, call_sid: str) -> None:
        st = self._sessions.pop(call_sid, None)
        if not st:
            return
        try:
            await st.ws.close()
        except Exception:
            pass
        logger.info("realtime_session_stopped", call_sid=call_sid)

    async def handle_twilio_audio(self, call_sid: str, pcm16_8k: bytes) -> None:
        st = self._sessions.get(call_sid)
        if not st or not st.is_connected:
            return
        try:
            pcm16_24k = _pcm16_resample_x3(pcm16_8k)
            audio_b64 = base64.b64encode(pcm16_24k).decode("utf-8")
            await self._send(st.ws, {"type": "input_audio_buffer.append", "audio": audio_b64})
            await self._send(st.ws, {"type": "input_audio_buffer.commit"})
        except (ConnectionClosed, WebSocketException) as e:
            logger.warning("realtime_audio_send_failed", call_sid=call_sid, error=str(e))
            st.is_connected = False
        except Exception as e:
            logger.error("realtime_audio_error", call_sid=call_sid, error=str(e))

    async def pop_openai_audio_8k(self, call_sid: str, event: Dict[str, Any]) -> Optional[bytes]:
        """
        Convert OpenAI `response.audio.delta` (base64 PCM16 @ 24k) to PCM16 @ 8k for Twilio.
        """
        delta = event.get("delta")
        if not delta:
            return None
        try:
            pcm16_24k = base64.b64decode(delta)
            return _pcm16_resample_div3(pcm16_24k)
        except Exception as e:
            logger.error("openai_audio_decode_error", call_sid=call_sid, error=str(e))
            return None

    async def _submit_tool_outputs(self, st: _SessionState, item_id: str, tool_outputs: List[Dict[str, Any]]) -> None:
        await self._send(
            st.ws,
            {
                "type": "conversation.item.required_action.submit_tool_outputs",
                "item_id": item_id,
                "tool_outputs": tool_outputs,
            },
        )

    async def _handle_requires_action(self, st: _SessionState, event: Dict[str, Any]) -> None:
        item = event.get("item") or {}
        item_id = item.get("id")
        required_action = item.get("required_action") or {}
        submit = required_action.get("submit_tool_outputs") or {}
        tool_calls = submit.get("tool_calls") or []
        if not item_id or not isinstance(tool_calls, list):
            return

        tool_outputs: List[Dict[str, Any]] = []

        for tc in tool_calls:
            tool_call_id = tc.get("id")
            tool_name = tc.get("name")
            tool_args = tc.get("parameters") or {}
            if not tool_call_id or not tool_name:
                continue

            risk, _ = tool_risk(tool_name)
            # Check if auto-execute is enabled
            auto_execute = getattr(settings, "AUTO_EXECUTE_HIGH_RISK", True)
            
            if risk == Risk.LOW or auto_execute:
                # Execute immediately (LOW-risk tools, or HIGH-risk with auto-execute enabled)
                handler = TOOL_HANDLERS.get(tool_name)
                if not handler:
                    tool_outputs.append(
                        {"tool_call_id": tool_call_id, "output": json.dumps({"error": f"Unknown tool: {tool_name}"})}
                    )
                    continue
                try:
                    result = await handler(**tool_args)
                    tool_outputs.append({"tool_call_id": tool_call_id, "output": json.dumps(result)})
                except Exception as e:
                    tool_outputs.append({"tool_call_id": tool_call_id, "output": json.dumps({"error": str(e)})})
            else:
                # HIGH-risk with confirmation required (auto-execute disabled)
                task_id = self._create_pending_task(tool_name=tool_name, tool_args=tool_args)
                st.pending_actions.append(
                    {
                        "item_id": item_id,
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "voice_confirmed": False,
                        "task_id": task_id,
                    }
                )
                # Ask for voice confirmation
                await self._send(
                    st.ws,
                    {
                        "type": "response.create",
                        "response": {
                            "modalities": ["audio", "text"],
                            "instructions": (
                                f"I can do that, but it requires approval. "
                                f"Please say 'confirm' to approve by voice, then approve task {task_id} in the app."
                            ),
                        },
                    },
                )

        if tool_outputs:
            await self._submit_tool_outputs(st, item_id=item_id, tool_outputs=tool_outputs)

    async def _listen(self, call_sid: str) -> None:
        st = self._sessions.get(call_sid)
        if not st:
            return
        ws = st.ws
        
        while st.is_connected:
            try:
                async for msg in ws:
                    event = json.loads(msg)
                    et = event.get("type")

                    if et == "conversation.item.input_audio_transcription.completed":
                        st.last_user_transcript = (event.get("transcript") or "").strip()
                        if st.last_user_transcript.lower() in {"confirm", "approve", "yes"}:
                            st.last_confirmed = True
                            # Apply voice confirmation to the most recent pending action (if any).
                            if st.pending_actions:
                                st.pending_actions[-1]["voice_confirmed"] = True
                    
                    if et == "response.audio.delta":
                        pcm16_8k = await self.pop_openai_audio_8k(call_sid=call_sid, event=event)
                        if pcm16_8k and st.twilio_audio_sender:
                            try:
                                await st.twilio_audio_sender(pcm16_8k)
                            except Exception as e:
                                logger.error("twilio_audio_send_failed", call_sid=call_sid, error=str(e))

                    if et == "conversation.item.requires_action":
                        await self._handle_requires_action(st, event)
                    
                    # Handle error events
                    if et == "error":
                        error_info = event.get("error", {})
                        logger.error(
                            "realtime_api_error",
                            call_sid=call_sid,
                            error_type=error_info.get("type"),
                            error_message=error_info.get("message"),
                            error_code=error_info.get("code")
                        )
                        # Don't reconnect on client errors (4xx)
                        error_code = error_info.get("code")
                        if error_code and error_code.startswith("4"):
                            st.is_connected = False
                            break

                    # Tool handling is finalized in tools-suite; keep minimal placeholder now.
                    
                # If the async iterator ends without raising ConnectionClosed, treat as disconnected.
                st.is_connected = False
                break
            except ConnectionClosed as e:
                logger.warning("realtime_connection_closed", call_sid=call_sid, code=e.code, reason=e.reason)
                # Attempt reconnection if not exceeded max attempts
                if st.reconnect_attempts < st.max_reconnect_attempts:
                    st.reconnect_attempts += 1
                    logger.info("realtime_reconnecting", call_sid=call_sid, attempt=st.reconnect_attempts)
                    try:
                        await asyncio.sleep(2 ** st.reconnect_attempts)  # Exponential backoff
                        await self._connect_websocket(call_sid, st.actor)
                        st = self._sessions.get(call_sid)
                        if st:
                            ws = st.ws
                            continue
                    except Exception as reconnect_error:
                        logger.error("realtime_reconnect_failed", call_sid=call_sid, error=str(reconnect_error))
                else:
                    logger.error("realtime_reconnect_exhausted", call_sid=call_sid)
                    st.is_connected = False
                    break
                    
            except WebSocketException as e:
                logger.error("realtime_websocket_error", call_sid=call_sid, error=str(e))
                st.is_connected = False
                break
                
            except Exception as e:
                logger.error("realtime_listen_error", call_sid=call_sid, error=str(e), error_type=type(e).__name__)
                st.is_connected = False
                break
        
        # Cleanup
        await self.stop(call_sid)

    async def _send(self, ws: Any, payload: Dict[str, Any]) -> None:
        """Send message to WebSocket with error handling."""
        try:
            await ws.send(json.dumps(payload))
        except (ConnectionClosed, WebSocketException) as e:
            logger.warning("realtime_send_failed", error=str(e))
            raise
        except Exception as e:
            logger.error("realtime_send_error", error=str(e), error_type=type(e).__name__)
            raise


# --- PCM16 resampling helpers (8k <-> 24k exact factor 3) ---

def _pcm16_unpack_mono(pcm16: bytes) -> list[int]:
    if not pcm16:
        return []
    if len(pcm16) % 2 != 0:
        pcm16 = pcm16[:-1]
    return list(struct.unpack(f"<{len(pcm16)//2}h", pcm16))


def _pcm16_pack_mono(samples: list[int]) -> bytes:
    if not samples:
        return b""
    clamped = [max(-32768, min(32767, int(s))) for s in samples]
    return struct.pack(f"<{len(clamped)}h", *clamped)


def _pcm16_resample_x3(pcm16_8k: bytes) -> bytes:
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
    src = _pcm16_unpack_mono(pcm16_24k)
    if not src:
        return b""
    return _pcm16_pack_mono(src[::3])


_bridge_singleton: Optional[RealtimeCallBridge] = None


def get_realtime_bridge() -> RealtimeCallBridge:
    global _bridge_singleton
    if _bridge_singleton is None:
        _bridge_singleton = RealtimeCallBridge()
    return _bridge_singleton


