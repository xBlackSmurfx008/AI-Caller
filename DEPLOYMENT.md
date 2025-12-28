# Deployment Guide

This guide covers deploying the AI Caller system to production.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend)
- Docker and Docker Compose (optional)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Application
APP_NAME=AI Caller
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=<generate-secure-random-key>

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

# JWT
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email (Optional)
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=AI Caller
FRONTEND_URL=https://your-frontend-domain.com

# Vector Database (choose one)
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX_NAME=ai-caller-knowledge

# Or
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Or use Chroma (default)
CHROMA_PERSIST_DIR=./chroma_db
```

## Backend Deployment

### Using Docker Compose (Recommended)

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run:
```bash
docker-compose up -d
```

### Manual Deployment

1. Install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set up database:
```bash
alembic upgrade head
```

3. Run migrations:
```bash
python scripts/run_migrations.py
```

4. Start the application:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Production Server (Gunicorn)

```bash
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Frontend Deployment

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Build for production:
```bash
npm run build
```

3. Serve static files (using nginx example):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Celery Worker

For background tasks, run Celery worker:

```bash
celery -A src.celery_app worker --loglevel=info
```

## Monitoring

- Health check: `GET /health`
- API docs: `GET /docs`
- Flower (Celery monitoring): `http://localhost:5555`

## Security Checklist

- [ ] Change all default secrets
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts
- [ ] Review and restrict API endpoints
- [ ] Enable rate limiting
- [ ] Set up SSL certificates

## Scaling

- Use a load balancer for multiple backend instances
- Configure Redis for session storage
- Use a managed PostgreSQL service
- Set up horizontal scaling for Celery workers
- Use CDN for frontend assets

