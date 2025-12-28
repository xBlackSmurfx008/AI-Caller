"""
Vercel serverless function entry point.

IMPORTANT:
- Vercel serverless has strict bundle size limits.
- The full AI Caller backend pulls in heavy optional deps (RAG, Playwright, etc.).
  For Twilio webhook testing, we only need a small subset of routes and deps.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.webhooks.twilio_webhook import router as twilio_webhook_router
from src.utils.config import get_settings
from src.utils.logging import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(
    title="AI Caller Webhooks (Vercel)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(twilio_webhook_router, prefix="/webhooks/twilio", tags=["webhooks"])


@app.get("/")
async def root():
    return {"message": "AI Caller Webhook API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

