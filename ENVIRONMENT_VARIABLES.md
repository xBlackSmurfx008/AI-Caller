# Environment Variables Reference

Complete list of environment variables used by the AI Caller system.

## Required Variables

### Application
- `APP_NAME`: Application name (default: "AI Caller")
- `APP_ENV`: Environment (`development`, `production`)
- `APP_DEBUG`: Enable debug mode (default: `true`)
- `APP_HOST`: Host to bind to (default: `0.0.0.0`)
- `APP_PORT`: Port to listen on (default: `8000`)
- `SECRET_KEY`: Secret key for application (change in production!)

### Database
- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`

### Redis
- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)

### OpenAI
- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: `gpt-4o`)
- `OPENAI_REALTIME_API_URL`: Realtime API URL (default: `wss://api.openai.com/v1/realtime`)

### Twilio
- `TWILIO_ACCOUNT_SID`: Twilio Account SID (required)
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token (required)
- `TWILIO_PHONE_NUMBER`: Twilio phone number (required)
- `TWILIO_WEBHOOK_URL`: Base URL for webhooks (optional)

### Security
- `JWT_SECRET_KEY`: Secret key for JWT tokens (change in production!)
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_EXPIRATION_HOURS`: Token expiration in hours (default: `24`)

## Optional Variables

### Email Service
- `EMAIL_ENABLED`: Enable email service (default: `false`)
- `SMTP_SERVER`: SMTP server hostname (default: `smtp.gmail.com`)
- `SMTP_PORT`: SMTP port (default: `587`)
- `SMTP_USERNAME`: SMTP username
- `SMTP_PASSWORD`: SMTP password
- `SMTP_FROM_EMAIL`: From email address
- `SMTP_FROM_NAME`: From name (default: `AI Caller`)
- `FRONTEND_URL`: Frontend URL for email links (default: `http://localhost:3000`)

### Vector Database - Pinecone
- `PINECONE_API_KEY`: Pinecone API key
- `PINECONE_ENVIRONMENT`: Pinecone environment
- `PINECONE_INDEX_NAME`: Index name (default: `ai-caller-knowledge`)

### Vector Database - Weaviate
- `WEAVIATE_URL`: Weaviate URL (default: `http://localhost:8080`)
- `WEAVIATE_API_KEY`: Weaviate API key

### Vector Database - Chroma
- `CHROMA_PERSIST_DIR`: Chroma persistence directory (default: `./chroma_db`)

### Celery
- `CELERY_BROKER_URL`: Celery broker URL (default: `redis://localhost:6379/1`)
- `CELERY_RESULT_BACKEND`: Celery result backend (default: `redis://localhost:6379/2`)

### Monitoring
- `PROMETHEUS_PORT`: Prometheus metrics port (default: `9090`)

### Quality Assurance
- `QA_ENABLED`: Enable QA monitoring (default: `true`)
- `SENTIMENT_ANALYSIS_ENABLED`: Enable sentiment analysis (default: `true`)
- `COMPLIANCE_CHECK_ENABLED`: Enable compliance checking (default: `true`)

### Escalation
- `ESCALATION_ENABLED`: Enable escalation (default: `true`)
- `HUMAN_AGENT_QUEUE_URL`: Agent queue URL (default: `redis://localhost:6379/3`)

### Knowledge Base
- `KB_CHUNKING_STRATEGY`: Chunking strategy (default: `adaptive`)
- `KB_CHUNK_SIZE`: Chunk size (default: `1000`)
- `KB_CHUNK_OVERLAP`: Chunk overlap (default: `200`)
- `KB_EMBEDDING_MODEL`: Embedding model (default: `text-embedding-3-small`)

### CORS
- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: `*`)

## Example .env File

```bash
# Application
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_caller

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/webhooks

# Security
JWT_SECRET_KEY=your-jwt-secret-key-here

# Email
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=https://your-frontend-domain.com
```

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use strong, random secrets** for `SECRET_KEY` and `JWT_SECRET_KEY`
3. **Use environment-specific values** for production
4. **Rotate secrets regularly** in production
5. **Use secrets management** services (AWS Secrets Manager, HashiCorp Vault, etc.) for production

