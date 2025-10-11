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

## Setup Instructions

### Prerequisites

- Python 3.14
- PostgreSQL database

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd memic-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python3.14 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Set up PostgreSQL database**
   - Create a database named `memic_db`
   - Update `DATABASE_URL` in `.env` file

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

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

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/memic_db` |
| `APP_NAME` | Application name | `Memic Backend` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
