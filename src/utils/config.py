"""Configuration management using Pydantic Settings"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Voice Assistant"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = ""  # URL of the frontend (e.g. https://myapp.vercel.app or http://localhost:5173)
    SECRET_KEY: str = "change-me-in-production"

    # OpenAI - Chat Models (for planning, orchestration, text tasks)
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"  # Chat model for task planning
    OPENAI_PLANNING_MODEL: str = ""  # Optional: separate model for complex planning (defaults to OPENAI_MODEL)
    
    # OpenAI - Realtime Voice Models (for voice-to-voice conversations)
    OPENAI_REALTIME_API_URL: str = "wss://api.openai.com/v1/realtime"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview"  # Voice model for real-time calls
    OPENAI_REALTIME_VOICE: str = "alloy"  # Voice: alloy, echo, fable, onyx, nova, shimmer
    
    # OpenAI Advanced Features
    OPENAI_USE_RESPONSES: bool = False  # Use Responses API (beta)
    OPENAI_ENABLE_STREAMING: bool = True  # Stream chat responses
    OPENAI_USE_STRUCTURED_OUTPUTS: bool = True  # Force valid JSON responses
    OPENAI_MAX_TOKENS: int = 4096  # Max tokens for completions

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_WEBHOOK_URL: str = ""
    # Enable Twilio Media Streams (WebSocket) for true voice-to-voice.
    # If false, we fall back to the Gather/Say loop.
    TWILIO_MEDIA_STREAMS_ENABLED: bool = False
    # Optional: explicitly set the public WS base, e.g. wss://xxxxx.ngrok.app
    TWILIO_MEDIA_STREAMS_WS_BASE_URL: str = ""

    # Email (for email tool)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # Godfather identity / allowlist
    # Comma-separated E.164 numbers, e.g. "+15551234567,+15557654321"
    GODFATHER_PHONE_NUMBERS: str = ""
    GODFATHER_EMAIL: str = ""

    # Auto-execute mode: skip confirmation prompts for high-risk actions
    # When True, the AI will execute calls, SMS, emails, and calendar changes immediately
    AUTO_EXECUTE_HIGH_RISK: bool = True

    # Google Calendar (OAuth)
    # Provide either a path to a client secrets JSON, or JSON inline.
    GOOGLE_OAUTH_CLIENT_SECRETS_FILE: str = ""
    GOOGLE_OAUTH_CLIENT_SECRETS_JSON: str = ""
    # Where we store tokens in dev (avoid committing this file).
    # NOTE: `secrets/` is already gitignored in this repo.
    GOOGLE_OAUTH_TOKEN_FILE: str = "secrets/google_token.json"
    # Default calendar (\"primary\" is typical)
    GOOGLE_CALENDAR_ID: str = "primary"

    # Gmail (OAuth)
    # Provide either a path to a client secrets JSON, or JSON inline.
    GMAIL_OAUTH_CLIENT_SECRETS_FILE: str = ""
    GMAIL_OAUTH_CLIENT_SECRETS_JSON: str = ""
    # Where we store Gmail tokens
    GMAIL_OAUTH_TOKEN_FILE: str = "secrets/gmail_token.json"

    # Outlook (Microsoft Graph OAuth)
    # Provide either a path to a client secrets JSON, or JSON inline.
    # JSON should contain: client_id (or appId), client_secret (or password), tenant (optional, defaults to "common")
    OUTLOOK_OAUTH_CLIENT_SECRETS_FILE: str = ""
    OUTLOOK_OAUTH_CLIENT_SECRETS_JSON: str = ""
    # Where we store Outlook tokens
    OUTLOOK_OAUTH_TOKEN_FILE: str = "secrets/outlook_token.json"

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Auth
    # Legacy Godfather token (backwards compatibility)
    # If set, all /api/* endpoints accept this token via:
    # - Header: X-Godfather-Token: <token>
    # - OR Authorization: Bearer <token>
    GODFATHER_API_TOKEN: str = ""
    
    # Supabase Auth (recommended for production)
    # JWT secret from Supabase project settings (Settings > API > JWT Secret)
    SUPABASE_JWT_SECRET: str = ""
    # Supabase project URL (for verification)
    SUPABASE_URL: str = ""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
