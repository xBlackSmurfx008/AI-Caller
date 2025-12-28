"""Twilio webhook handlers with full implementation"""

import asyncio
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse, Gather

router = APIRouter()

# Initialize components with error handling
logger = None
settings = None
call_handler = None
openai_client = None

try:
    from src.utils.config import get_settings
    from src.utils.logging import get_logger
    logger = get_logger(__name__)
    settings = get_settings()
except Exception as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to load settings: {e}")

try:
    if settings and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    logger.warning(f"Failed to initialize OpenAI client: {e}") if logger else None

try:
    if settings:
        from src.telephony.call_handler import CallHandler
        call_handler = CallHandler()
except Exception as e:
    logger.warning(f"Failed to initialize CallHandler: {e}") if logger else None


def _get_chat_model() -> str:
    """
    Choose a chat-capable model for Twilio Gather/Say.

    Notes:
    - `OPENAI_MODEL` may be set to a Realtime-only model (e.g. gpt-4o-realtime-preview).
    - For this Twilio flow we need a standard chat model.
    """
    model = (getattr(settings, "OPENAI_MODEL", "") or "").strip()
    if not model:
        return "gpt-4o"
    if "realtime" in model:
        return "gpt-4o"
    return model


def _generate_agent_reply(user_text: str) -> str:
    """Generate a concise, speakable response for a phone call."""
    if not openai_client:
        return "I'm sorry, the AI service is currently unavailable. Please try again later."
    
    system_prompt = (
        "You are a concise, helpful phone agent. "
        "Speak naturally. Keep responses short (1-2 sentences). "
        "Ask one clarifying question if needed."
    )
    try:
        model = _get_chat_model()
        resp = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        content = (resp.choices[0].message.content or "").strip()
        return content or "Sorry—could you repeat that?"
    except Exception as e:
        if logger:
            logger.error("openai_twilio_reply_failed", error=str(e))
        return "Sorry, I'm having trouble right now. Could you try again?"


@router.post("/status")
async def twilio_status_callback(request: Request):
    """Handle Twilio status callbacks"""
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        call_status = data.get("CallStatus")

        # Best-effort DB updates (may be unavailable in serverless / webhook-only mode)
        try:
            from src.database.models import CallStatus as CallStatusEnum

            status_map = {
                "initiated": CallStatusEnum.INITIATED,
                "ringing": CallStatusEnum.RINGING,
                "in-progress": CallStatusEnum.IN_PROGRESS,
                "completed": CallStatusEnum.COMPLETED,
                "failed": CallStatusEnum.FAILED,
            }

            status = status_map.get(call_status)
            if status and call_sid:
                call_handler.update_call_status(call_sid, status)

                # Stop bridge when call ends (only relevant for Media Streams mode)
                if status in (CallStatusEnum.COMPLETED, CallStatusEnum.FAILED):
                    call_manager = get_call_manager()
                    await call_manager.stop_call_bridge(call_sid)
        except Exception as e:
            logger.warning(
                "twilio_status_db_update_skipped",
                error=str(e),
                call_sid=call_sid,
                call_status=call_status,
            )

        logger.info("twilio_status_received", call_sid=call_sid, status=call_status)
        return {"status": "received"}

    except Exception as e:
        logger.error("twilio_status_error", error=str(e))
        return {"status": "error"}


@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """Handle Twilio voice webhooks and return TwiML (Vercel-friendly Gather/Say loop)."""
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        from_number = data.get("From")
        to_number = data.get("To")
        speech_result = (data.get("SpeechResult") or "").strip()

        # Try to ensure we have a call record (but avoid duplicating on subsequent Gather turns)
        if call_handler and call_sid:
            try:
                existing = call_handler.get_call_by_sid(call_sid)
                if not existing:
                    call_handler.handle_inbound_call(
                        call_sid=call_sid,
                        from_number=from_number,
                        to_number=to_number,
                    )
            except Exception as db_error:
                # Database operation failed, but continue with webhook response
                if logger:
                    logger.warning(f"Failed to create/check call record: {db_error}")

        # Build a Twilio Gather/Say loop so this works on Vercel serverless
        resp = VoiceResponse()

        if not speech_result:
            # First turn (or no speech detected): prompt the caller
            resp.say("Hi. How can I help you today?")
        else:
            # Respond to what caller said
            agent_reply = await asyncio.to_thread(_generate_agent_reply, speech_result)
            resp.say(agent_reply)

        # Get webhook URL from settings or use request URL
        if settings and hasattr(settings, 'TWILIO_WEBHOOK_URL') and settings.TWILIO_WEBHOOK_URL:
            action_url = f"{settings.TWILIO_WEBHOOK_URL.rstrip('/')}/webhooks/twilio/voice"
        else:
            # Fallback: construct from request
            base_url = str(request.base_url).rstrip('/')
            action_url = f"{base_url}/webhooks/twilio/voice"

        gather = Gather(
            input="speech",
            action=action_url,
            method="POST",
            language="en-US",
            timeout=5,
            speech_timeout="auto",
        )
        gather.say("Go ahead.")
        resp.append(gather)
        resp.redirect(action_url, method="POST")

        twiml = str(resp)

        # Return TwiML XML with correct content type
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        if logger:
            logger.error("twilio_voice_error", error=str(e))
        # Always return valid TwiML, even on error
        error_twiml = "<Response><Say>I'm sorry, I'm having trouble right now. Please try again later.</Say></Response>"
        return Response(content=error_twiml, media_type="application/xml")


@router.websocket("/media/{call_sid}")
async def twilio_media_stream(websocket: WebSocket, call_sid: str):
    """Handle Twilio Media Stream WebSocket connection"""
    await websocket.accept()
    logger.info("media_stream_connected", call_sid=call_sid)

    call_manager = get_call_manager()
    
    # Get call record to find call_id
    from src.database.database import get_db
    from src.database.models import Call
    db = next(get_db())
    call = db.query(Call).filter(Call.twilio_call_sid == call_sid).first()
    
    # Start OpenAI voice agent bridge when media stream connects
    if call and not call_manager.is_call_active(call_sid):
        try:
            await call_manager.start_call_bridge(
                call_id=call.id,
                call_sid=call_sid,
                db=db,
            )
        except Exception as e:
            logger.error(
                "bridge_start_error",
                error=str(e),
                call_id=call.id if call else None,
                call_sid=call_sid,
            )
    
    try:
        import json
        import base64

        while True:
            # Receive message from Twilio
            message = await websocket.receive_text()
            data = json.loads(message)

            event_type = data.get("event")

            if event_type == "media":
                # Handle audio data
                payload = data.get("payload", {})
                audio_b64 = payload.get("payload")
                
                if audio_b64:
                    try:
                        # Decode base64 audio
                        audio_data = base64.b64decode(audio_b64)
                        
                        # Route to OpenAI via call manager
                        await call_manager.handle_media_stream_audio(
                            call_sid=call_sid,
                            audio_data=audio_data,
                            metadata=data,
                        )
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
                # Stop the bridge when stream stops
                await call_manager.stop_call_bridge(call_sid)
                break

    except WebSocketDisconnect:
        logger.info("media_stream_disconnected", call_sid=call_sid)
        await call_manager.stop_call_bridge(call_sid)
    except Exception as e:
        logger.error("media_stream_error", error=str(e), call_sid=call_sid)
        await call_manager.stop_call_bridge(call_sid)
    finally:
        try:
            await websocket.close()
        except:
            pass


# Note: WebSocket routes need to be added directly to the FastAPI app
# This will be handled in the main application file

