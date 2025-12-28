# Enterprise AI Caller System

An enterprise-grade AI-powered call center system built with OpenAI Voice API (GPT-4o) and Twilio, featuring RAG knowledge base integration, quality assurance, and seamless human escalation.

## Features

- **Dual Telephony Support**: OpenAI Voice API + Twilio integration
- **Template-Based Architecture**: Easily customizable for different business types
- **RAG Knowledge Base**: Vector database integration for intelligent information retrieval
- **Quality Assurance**: Real-time monitoring, sentiment analysis, and compliance checking
- **Human Escalation**: Seamless Level 2 handoff with context preservation
- **Enterprise-Grade**: Scalable, secure, and production-ready

## Architecture

The system uses a hybrid architecture combining:
- **OpenAI Realtime API** (GPT-4o) for low-latency speech-to-speech processing
- **Twilio Voice API** for telephony infrastructure (inbound/outbound calls)
- **RAG (Retrieval-Augmented Generation)** for knowledge base integration
- **Modular template system** for business-specific customization

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend)
- OpenAI API key
- Twilio account

### Installation

#### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-caller
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
# See Environment Variables section below for details
```

5. Set up PostgreSQL database:
```bash
# Create database
createdb ai_caller

# Or using PostgreSQL client:
psql -U postgres
CREATE DATABASE ai_caller;
```

6. Run database migrations:
```bash
# Initialize Alembic (if not already done)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

7. Start Redis (if not using Docker):
```bash
redis-server
```

8. Run the backend application:
```bash
# Development mode
uvicorn src.main:app --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
# Create .env file in frontend directory
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env
```

4. Run the frontend development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

#### Required Variables

- `DATABASE_URL` - PostgreSQL connection string (e.g., `postgresql://user:password@localhost:5432/ai_caller`)
- `OPENAI_API_KEY` - Your OpenAI API key
- `TWILIO_ACCOUNT_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `JWT_SECRET_KEY` - Secret key for JWT tokens (generate a secure random string)
- `SECRET_KEY` - Application secret key

#### Optional Variables

- `REDIS_URL` - Redis connection string (default: `redis://localhost:6379/0`)
- `EMAIL_ENABLED` - Enable email functionality (default: `false`)
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - SMTP settings
- `FRONTEND_URL` - Frontend URL for password reset links
- `CORS_ORIGINS` - Allowed CORS origins (JSON array)

See `.env.example` for complete list of all available environment variables.

### Database Migrations

The project uses Alembic for database migrations.

#### Creating a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

#### Applying migrations:
```bash
alembic upgrade head
```

#### Rolling back migrations:
```bash
alembic downgrade -1  # Roll back one migration
alembic downgrade base  # Roll back all migrations
```

#### Checking migration status:
```bash
alembic current
alembic history
```

## Configuration

The system uses YAML-based templates for business-specific configurations. See `config/` directory for examples.

## API Documentation

Once running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
ai-caller/
├── src/
│   ├── telephony/          # Twilio integration
│   ├── ai/                  # OpenAI integration
│   ├── knowledge/           # RAG system
│   ├── templates/           # Business templates
│   ├── qa/                  # Quality assurance
│   ├── escalation/          # Human handoff
│   ├── api/                 # REST API
│   ├── database/            # Data models
│   └── utils/               # Shared utilities
├── config/                  # Configuration files
├── tests/                   # Test suite
├── docs/                    # Documentation
└── scripts/                 # Deployment scripts
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_qa.py

# Run with verbose output
pytest -v
```

### Code Formatting

```bash
# Format Python code
black src/
isort src/

# Check formatting without making changes
black --check src/
isort --check src/
```

### Development Workflow

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest`
4. Format code: `black src/ && isort src/`
5. Create a pull request

### Health Checks

The application includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

This returns the status of the application, database connectivity, and Redis connectivity.

## Deployment

### Docker Deployment

The project includes Docker configuration for easy deployment.

#### Development (using docker-compose):

```bash
# Start all services (PostgreSQL, Redis, API, Celery, Flower)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### Production Deployment:

1. Build the Docker image:
```bash
docker build -t ai-caller:latest .
```

2. Run with production environment:
```bash
docker run -d \
  --name ai-caller \
  -p 8000:8000 \
  --env-file .env.production \
  ai-caller:latest
```

### Production Checklist

Before deploying to production:

- [ ] Set `APP_ENV=production` in environment variables
- [ ] Set `APP_DEBUG=false`
- [ ] Generate secure `JWT_SECRET_KEY` and `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` to your frontend domain(s)
- [ ] Set up SSL/TLS certificates (HTTPS)
- [ ] Configure production database with connection pooling
- [ ] Set up Redis with persistence
- [ ] Configure email service (SMTP)
- [ ] Set up monitoring and logging
- [ ] Review security settings in `config/environments/production.yaml`
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Test health endpoint: `curl https://yourdomain.com/health`

### Environment-Specific Configuration

The project supports environment-specific configuration files:

- `config/default.yaml` - Default configuration
- `config/environments/production.yaml` - Production overrides

Set `APP_ENV` environment variable to load the appropriate configuration.

## License

[Your License Here]

## Support

[Your Support Information Here]

