"""Audio routes: Speech-to-Text (STT) and Text-to-Speech (TTS) via OpenAI."""

from __future__ import annotations

import base64
from typing import Optional, Literal

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.utils.openai_client import create_openai_client, retry_openai_call
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.cost.cost_event_logger import CostEventLogger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    model: str = "tts-1"
    format: Literal["mp3", "wav", "pcm"] = "mp3"


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
):
    """
    Transcribe an audio file using OpenAI STT.
    """
    try:
        client = create_openai_client(timeout=60.0, max_retries=3)

        @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=30.0)
        def _call():
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=file.file,
                response_format="json",
            )

        result = _call()
        # openai-python returns an object with .text for transcriptions in many versions; keep robust.
        text = getattr(result, "text", None) or (result.get("text") if isinstance(result, dict) else None)
        return {"success": True, "text": text or ""}
    except Exception as e:
        logger.error("stt_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"STT failed: {str(e)}")


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest,
    db: Session = Depends(get_db),
):
    """
    Synthesize speech using OpenAI TTS and return audio bytes.
    """
    try:
        client = create_openai_client(timeout=60.0, max_retries=3)

        @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=30.0)
        def _call():
            return client.audio.speech.create(
                model=req.model,
                voice=req.voice,
                input=req.text,
                response_format=req.format,
            )

        resp = _call()
        audio_bytes = getattr(resp, "content", None)
        if audio_bytes is None and isinstance(resp, (bytes, bytearray)):
            audio_bytes = bytes(resp)
        if audio_bytes is None:
            # Some SDK variants return base64 or a dict; last resort handle.
            if isinstance(resp, dict) and "audio" in resp:
                audio_bytes = base64.b64decode(resp["audio"])
        if audio_bytes is None:
            raise ValueError("Unexpected TTS response type")

        # Cost logging for TTS is not token-based; log a 1-unit event for observability.
        try:
            CostEventLogger().log_cost_event(
                db=db,
                provider="openai",
                service="tts",
                metric_type="requests",
                units=1.0,
                metadata={"model": req.model, "voice": req.voice, "format": req.format, "text_len": len(req.text)},
            )
        except Exception as cost_error:
            logger.warning("tts_cost_logging_failed", error=str(cost_error))

        media_type = {"mp3": "audio/mpeg", "wav": "audio/wav", "pcm": "application/octet-stream"}[req.format]
        return Response(content=audio_bytes, media_type=media_type)
    except Exception as e:
        logger.error("tts_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"TTS failed: {str(e)}")


