"""Twilio webhook handlers"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/status")
async def twilio_status_callback(request: Request):
    """Handle Twilio status callbacks"""
    # TODO: Implement status callback handling
    data = await request.form()
    return {"status": "received"}


@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """Handle Twilio voice webhooks"""
    # TODO: Implement voice webhook handling
    data = await request.form()
    return {"message": "Voice webhook received"}

