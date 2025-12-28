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
    APP_NAME: str = "AI Caller"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "change-me-in-production"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-realtime-preview"  # Best for voice assistants/agents
    OPENAI_REALTIME_API_URL: str = "wss://api.openai.com/v1/realtime"

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_WEBHOOK_URL: str = ""

    # Database
    # NOTE: In serverless environments (e.g., Vercel), missing env vars should not crash boot.
    # Production should override this with a real Postgres URL (e.g., Neon).
    DATABASE_URL: str = "sqlite:////tmp/ai_caller.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector Database - Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "ai-caller-knowledge"

    # Vector Database - Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = ""

    # Vector Database - Chroma
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Monitoring
    PROMETHEUS_PORT: int = 9090

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Quality Assurance
    QA_ENABLED: bool = True
    SENTIMENT_ANALYSIS_ENABLED: bool = True
    COMPLIANCE_CHECK_ENABLED: bool = True

    # Escalation
    ESCALATION_ENABLED: bool = True
    HUMAN_AGENT_QUEUE_URL: str = "redis://localhost:6379/3"

    # Knowledge Base
    KB_CHUNKING_STRATEGY: str = "adaptive"  # semantic, hierarchical, sliding_window, adaptive
    KB_CHUNK_SIZE: int = 1000
    KB_CHUNK_OVERLAP: int = 200
    KB_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Email Configuration
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "AI Caller"
    FRONTEND_URL: str = "http://localhost:3000"
    KB_USE_CACHE: bool = True
    KB_CACHE_TTL: int = 3600
    KB_HYBRID_SEARCH_ENABLED: bool = True
    KB_SEMANTIC_WEIGHT: float = 0.7
    KB_KEYWORD_WEIGHT: float = 0.3
    KB_RERANKING_ENABLED: bool = True
    KB_USE_CROSS_ENCODER: bool = True
    KB_TOP_K: int = 5
    KB_SIMILARITY_THRESHOLD: float = 0.7
    KB_VOICE_OPTIMIZATION: bool = True
    KB_MAX_CONTEXT_LENGTH: int = 2000
    KB_VOICE_MAX_LENGTH: int = 500
    KB_FEEDBACK_ENABLED: bool = True
    KB_ANALYTICS_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database Connection Pooling
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

