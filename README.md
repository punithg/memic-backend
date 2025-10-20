# Memic Backend

FastAPI backend for AI agent memory management and high-performance RAG. Built with Python 3.14 using clean MVC architecture.

## What is Memic?

A platform for AI agent memory and RAG (Retrieval-Augmented Generation):
- **Agent Memory**: Store and retrieve agent memories with smart recall
- **High-Performance RAG**: Ingest and query documents, audio, and video
- **Multi-Tenant**: Organization and project-based isolation
- **Production-Ready**: MVC architecture, database migrations, JWT auth

## Architecture

This project follows a clean MVC architecture with the following structure:

```
app/
├── controllers/     # HTTP request/response handlers
├── services/        # Business logic layer
├── models/          # Database entities (SQLAlchemy models)
├── dtos/            # Data Transfer Objects (request/response schemas)
├── routes/          # API route definitions
├── config.py        # Application configuration
├── database.py      # Database connection setup
└── main.py          # Application entry point
```

## Quick Start

**Prerequisites:** Python 3.14+, PostgreSQL

```bash
# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (copy .env.example to .env.dev and edit)
export APP_ENV=dev
cp .env.example .env.dev

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Environment Configuration

Environment files: `.env.dev` (dev), `.env.uat` (uat), `.env.prod` (prod)

**Required Variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `JWT_SECRET_KEY` - JWT signing secret
- `ENCRYPTION_KEY` - Data encryption key

See `.env.example` and [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) for details.

## API Endpoints

- `GET /` - Welcome message
- `GET /api/v1/health` - Health status
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## Development

**Request Flow:** Routes → Controllers → Services → Repositories → Models

**Adding a New Feature:**
1. Create model in `app/models/`
2. Generate Alembic migration: `alembic revision --autogenerate -m "description"`
3. Create DTOs in `app/dtos/`
4. Create service in `app/services/`
5. Create controller in `app/controllers/`
6. Add routes in `app/routes/api.py`
7. Update Postman collection

**Key Rules:**
- Always use Alembic for database changes (never manual SQL)
- Keep controllers thin (HTTP handling only)
- Put business logic in services
- No emojis in code
- Follow PEP 8 style guidelines

See [.cursorrules](.cursorrules) for complete development guidelines.
