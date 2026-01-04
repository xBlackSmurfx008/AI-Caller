"""Twilio webhook handlers (Gather/Say fallback + optional Media Streams + Messaging)."""

from fastapi import APIRouter, Request, Response, HTTPException, status, WebSocket, Depends
from fastapi.responses import JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
from sqlalchemy.orm import Session

from typing import Tuple

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.agent.assistant import VoiceAssistant
from src.telephony.media_stream import MediaStreamHandler
from src.security.policy import Actor, decide_confirmation, PlannedToolCall, is_godfather
from src.utils.autonomy import get_auto_execute_high_risk
from src.voice.realtime_bridge import get_realtime_bridge
from src.messaging.messaging_service import MessagingService
from src.database.database import get_db

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()
assistant = VoiceAssistant()
media_stream_handler = MediaStreamHandler()
realtime_bridge = get_realtime_bridge()
messaging_service = MessagingService()


def _validate_twilio_request(request: Request, form_data: dict) -> Tuple[bool, str]:
    """Validate Twilio webhook request signature.

    Returns:
        (is_valid, reason)
        reason ∈ {"ok","missing_token","invalid_signature","validation_error"}
    """
    try:
        if not settings.TWILIO_AUTH_TOKEN:
            logger.warning("twilio_auth_token_not_configured")
            return False, "missing_token"
        
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        signature = request.headers.get('X-Twilio-Signature', '')
        url = str(request.url)
        
        is_valid = validator.validate(url, form_data, signature)
        
        if not is_valid:
            logger.warning("twilio_signature_validation_failed", url=url)
            return False, "invalid_signature"
        
        return True, "ok"
    except Exception as e:
        logger.error("twilio_signature_validation_error", error=str(e))
        return False, "validation_error"


def _normalize_validation_result(result: object) -> Tuple[bool, str]:
    """
    Backward-compatible normalization for tests/mocks that return bool.
    """
    if isinstance(result, tuple) and len(result) == 2:
        valid, reason = result
        return bool(valid), str(reason)
    valid = bool(result)
    return valid, ("ok" if valid else "invalid_signature")


@router.post("/status")
async def twilio_status_callback(request: Request):
    """Handle Twilio status callbacks"""
    try:
        data = await request.form()
        valid, reason = _normalize_validation_result(_validate_twilio_request(request, dict(data)))
        if not valid:
            if reason == "missing_token":
                return JSONResponse(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    content={"detail": "TWILIO_AUTH_TOKEN not configured; set it to validate webhooks."}
                )
            logger.error("twilio_status_invalid_signature", reason=reason)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Twilio signature"
            )
        
        call_sid = data.get("CallSid")
        call_status = data.get("CallStatus")
        
        logger.info("twilio_status_received", call_sid=call_sid, status=call_status)
        return {"status": "received"}
        
    except Exception as e:
        logger.error("twilio_status_error", error=str(e))
        return {"status": "received"}


@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """Handle Twilio voice webhooks"""
    try:
        data = await request.form()
        form_dict = dict(data)
        
        valid, reason = _normalize_validation_result(_validate_twilio_request(request, form_dict))
        if not valid:
            if reason == "missing_token":
                return JSONResponse(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    content={"detail": "TWILIO_AUTH_TOKEN not configured; set it to validate webhooks."}
                )
            logger.error("twilio_voice_invalid_signature", reason=reason)
            error_twiml = "<Response><Say>I'm sorry, there was an authentication error.</Say></Response>"
            # Keep 200 for voice TwiML errors so Twilio can play the message; auth exemption tests rely on this.
            return Response(content=error_twiml, media_type="application/xml", status_code=status.HTTP_200_OK)
        
        call_sid = data.get("CallSid")
        from_number = data.get("From")
        to_number = data.get("To")
        speech_result = (data.get("SpeechResult") or "").strip()
        
        logger.info(
            "twilio_voice_webhook",
            call_sid=call_sid,
            from_number=from_number,
            speech_result=speech_result[:100] if speech_result else None
        )
        
        # If Media Streams enabled, start bidirectional stream for true voice-to-voice.
        if getattr(settings, "TWILIO_MEDIA_STREAMS_ENABLED", False):
            base_ws = (getattr(settings, "TWILIO_MEDIA_STREAMS_WS_BASE_URL", "") or "").strip().rstrip("/")
            if not base_ws:
                base_http = settings.TWILIO_WEBHOOK_URL.rstrip("/") if settings.TWILIO_WEBHOOK_URL else str(request.base_url).rstrip("/")
                if base_http.startswith("https://"):
                    base_ws = "wss://" + base_http[len("https://") :]
                elif base_http.startswith("http://"):
                    base_ws = "ws://" + base_http[len("http://") :]
                else:
                    base_ws = "wss://" + base_http.lstrip("/")

            websocket_url = f"{base_ws}/webhooks/twilio/media"
            # Pass caller metadata as custom parameters so the WS `start` event can classify actor.
            params = {
                "from": from_number or "",
                "to": to_number or "",
            }
            twiml = media_stream_handler.generate_twiml(websocket_url, parameters=params)
            return Response(content=twiml, media_type="application/xml")

        # Build TwiML response (Gather/Say fallback)
        resp = VoiceResponse()
        
        if not speech_result:
            # First turn: greet the caller
            resp.say("Hello! I'm your AI assistant. What would you like me to help you with today?")
        else:
            # Process the user's speech
            try:
                actor = Actor(
                    kind="godfather" if is_godfather(Actor(kind="external", phone_number=from_number)) else "external",
                    phone_number=from_number,
                )

                plan = assistant.plan_task(speech_result, context={})
                planned_calls = [
                    PlannedToolCall(name=c["name"], arguments=c.get("arguments") or {})
                    for c in (plan.get("planned_tool_calls") or [])
                ]

                # Use DB autonomy override if available (fallback to env)
                from src.database.database import SessionLocal
                _db = SessionLocal()
                try:
                    auto_execute = get_auto_execute_high_risk(_db)
                finally:
                    _db.close()

                policy = decide_confirmation(actor=actor, planned_calls=planned_calls, auto_execute_high_risk=auto_execute)

                if policy.requires_confirmation:
                    response_text = plan.get("response") or "I understand your request, but I need approval before taking action."
                    resp.say(response_text)
                    resp.say("I've noted this and will wait for approval before proceeding.")
                else:
                    if planned_calls:
                        await assistant.execute_planned_tools([{"name": c.name, "arguments": c.arguments} for c in planned_calls])
                    response_text = plan.get("response") or "I've completed your request."
                    resp.say(response_text)
            except Exception as e:
                logger.error("voice_task_error", error=str(e))
                resp.say("I'm sorry, I encountered an error. Please try again.")
        
        # Continue conversation
        action_url = f"{settings.TWILIO_WEBHOOK_URL.rstrip('/')}/webhooks/twilio/voice" if settings.TWILIO_WEBHOOK_URL else str(request.base_url).rstrip('/') + "/webhooks/twilio/voice"
        
        gather = Gather(
            input="speech",
            action=action_url,
            method="POST",
            language="en-US",
            timeout=5,
            speech_timeout="auto",
        )
        gather.say("How else can I help you?")
        resp.append(gather)
        resp.redirect(action_url, method="POST")
        
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error("twilio_voice_error", error=str(e))
        error_twiml = "<Response><Say>I'm sorry, I'm having trouble right now. Please try again later.</Say></Response>"
        return Response(content=error_twiml, media_type="application/xml")


@router.websocket("/media")
async def twilio_media_stream(websocket: WebSocket):
    """
    Twilio Media Streams WebSocket endpoint.
    Twilio sends callSid/streamSid in initial `start` event payload.
    """

    async def _on_start(call_sid: str, stream_sid: str, start_event: dict):
        start = (start_event.get("start") or {}) if isinstance(start_event, dict) else {}
        custom = start.get("customParameters") or {}
        from_number = custom.get("from")

        actor = Actor(
            kind="godfather" if from_number else "external",
            phone_number=from_number,
        )
        await realtime_bridge.start(
            call_sid=call_sid,
            actor=actor,
            twilio_audio_sender=lambda pcm16_8k: media_stream_handler.send_audio(call_sid, pcm16_8k),
        )

    async def _on_stop(call_sid: str, stream_sid: str, stop_event: dict):
        await realtime_bridge.stop(call_sid)

    async def _audio_handler(call_sid: str, audio_data: bytes, meta: dict):
        await realtime_bridge.handle_twilio_audio(call_sid=call_sid, pcm16_8k=audio_data)

    # The MediaStreamHandler handles Twilio JSON messages + µ-law decode.
    await media_stream_handler.handle_media_stream(
        websocket=websocket,
        audio_handler=_audio_handler,
        on_start=_on_start,
        on_stop=_on_stop,
    )


@router.post("/inbound-message")
async def twilio_inbound_message(request: Request, db: Session = Depends(get_db)):
    """Handle inbound Twilio SMS/MMS/WhatsApp messages"""
    try:
        data = await request.form()
        form_dict = dict(data)
        
        # Validate signature
        valid, reason = _normalize_validation_result(_validate_twilio_request(request, form_dict))
        if not valid:
            if reason == "missing_token":
                return JSONResponse(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    content={"detail": "TWILIO_AUTH_TOKEN not configured; set it to validate webhooks."}
                )
            logger.error("twilio_inbound_message_invalid_signature", reason=reason)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Twilio signature"
            )
        
        # Normalize payload
        normalized = messaging_service.normalize_twilio_payload(form_dict)
        
        logger.info(
            "inbound_message_received",
            from_address=normalized["from_address"],
            channel=normalized["channel"],
            message_sid=normalized.get("twilio_message_sid")
        )
        
        # Store message
        message = messaging_service.store_inbound_message(
            db=db,
            normalized_data=normalized
        )
        
        # Note: Conversation summarization is handled by background task
        # No need to process inline - background task will pick it up
        
        # Return TwiML response (empty for SMS/MMS/WhatsApp)
        return Response(content="", status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("twilio_inbound_message_error", error=str(e))
        # Still return 200 to Twilio to avoid retries
        return Response(content="", status_code=200)


@router.post("/message-status")
async def twilio_message_status(request: Request, db: Session = Depends(get_db)):
    """Handle Twilio message status callbacks"""
    try:
        data = await request.form()
        form_dict = dict(data)
        
        # Validate signature
        valid, reason = _normalize_validation_result(_validate_twilio_request(request, form_dict))
        if not valid:
            if reason == "missing_token":
                return JSONResponse(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    content={"detail": "TWILIO_AUTH_TOKEN not configured; set it to validate webhooks."}
                )
            logger.error("twilio_message_status_invalid_signature", reason=reason)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Twilio signature"
            )
        
        message_sid = form_dict.get("MessageSid")
        message_status = form_dict.get("MessageStatus")
        error_code = form_dict.get("ErrorCode")
        
        logger.info(
            "message_status_received",
            message_sid=message_sid,
            status=message_status,
            error_code=error_code
        )
        
        # Update message status in database
        if message_sid:
            from src.database.models import Message
            message = db.query(Message).filter(
                Message.twilio_message_sid == message_sid
            ).first()
            
            if message:
                message.status = message_status
                if error_code:
                    message.error_code = error_code
                db.commit()
                
                # Update approval status if outbound
                if message.direction == "outbound":
                    from src.database.models import OutboundApproval
                    approval = db.query(OutboundApproval).filter(
                        OutboundApproval.message_id == message.id
                    ).first()
                    if approval:
                        if message_status in ["delivered", "sent"]:
                            approval.status = "sent"
                        elif message_status == "failed":
                            approval.status = "failed"
                        db.commit()
        
        return Response(content="", status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("twilio_message_status_error", error=str(e))
        return Response(content="", status_code=200)
