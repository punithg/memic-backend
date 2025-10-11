# Memic Backend

A FastAPI backend application built with Python 3.14 using MVC (Model-View-Controller) architecture pattern.

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

## Features

- **FastAPI** with automatic API documentation
- **PostgreSQL** database with SQLAlchemy ORM
- **MVC Architecture** for clean code separation
- **Health Check** endpoint for monitoring
- **Environment Configuration** with pydantic-settings
- **CORS Support** for frontend integration

## Environment Setup

This application supports multiple environments (dev, uat, prod) with secure configuration management.

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd memic-backend
   ```

2. **Set up Python environment**
   ```bash
   # Using pyenv (recommended)
   pyenv install 3.14.0
   pyenv local 3.14.0
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure development environment**
   ```bash
   # Copy environment template
   cp .env.example .env.dev
   
   # Set environment
   export APP_ENV=dev
   
   # Edit .env.dev with your actual values
   # See docs/ENVIRONMENT_SETUP.md for detailed instructions
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Environment Configuration

The application uses environment-specific configuration files:

- **Development**: `.env.dev` (local development)
- **UAT**: `.env.uat` (user acceptance testing)  
- **Production**: `.env.prod` (production deployment)

**Important Security Notes:**
- Never commit actual environment files with real secrets
- Use `.env.example` as a template
- Production secrets should be stored in Azure Key Vault
- Set spending limits on development API keys

For detailed setup instructions, see [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md).

### Prerequisites

- **Python 3.14+** (installed via pyenv)
- **PostgreSQL** (local installation for development)
- **API Keys** (OpenAI, Stripe, SendGrid - see setup guide)

### API Endpoints

- **Root**: `GET /` - Welcome message
- **Health Check**: `GET /api/v1/health` - Application health status
- **API Documentation**: `GET /docs` - Interactive API docs (Swagger UI)
- **ReDoc**: `GET /redoc` - Alternative API documentation

### Development

The application uses the following architecture flow:

1. **Routes** (`app/routes/`) define API endpoints
2. **Controllers** (`app/controllers/`) handle HTTP requests/responses
3. **Services** (`app/services/`) contain business logic
4. **Models** (`app/models/`) define database schemas
5. **DTOs** (`app/dtos/`) define request/response schemas

### Adding New Features

To add a new feature (e.g., user management):

1. Create model in `app/models/user_model.py`
2. Create DTOs in `app/dtos/user_dto.py`
3. Create service in `app/services/user_service.py`
4. Create controller in `app/controllers/user_controller.py`
5. Add routes in `app/routes/api.py`

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `APP_ENV` | Yes | Environment (dev/uat/prod) | `dev` |
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `OPENAI_API_KEY` | Yes | OpenAI API key | `sk-...` |
| `JWT_SECRET_KEY` | Yes | JWT signing key | `random-string` |
| `ENCRYPTION_KEY` | Yes | Data encryption key | `random-string` |
| `STRIPE_SECRET_KEY` | No | Stripe API key | `sk_test_...` |
| `SENDGRID_API_KEY` | No | SendGrid API key | `SG.xxx` |
| `DEBUG` | No | Debug mode | `true`/`false` |
| `CORS_ORIGINS` | No | Allowed CORS origins | `*` or `https://domain.com` |

For complete environment variable reference, see [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md).
