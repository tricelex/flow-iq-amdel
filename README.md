# FastAPI Application

A clean FastAPI application template ready for your implementation.

## Project Details

- **Author:** Emmanuel Okoye (<emmanuel@genta.dev>)
- **Version:** 0.1.0
- **License:** MIT
- **Python Version:** >=3.13
- **Keywords:** fastapi, sqlalchemy, alembic, fullstack, api, asgi

## Features

- **FastAPI Backend:** Async API with automatic OpenAPI documentation
- **Advanced Alchemy:** Database management with UUIDAuditBase models
- **PostgreSQL:** Robust database storage with asyncpg
- **Structured Logging:** Structlog for development and production
- **Observability:** Prometheus metrics and Logfire integration (optional)
- **Taskiq Integration:** Background task processing with taskiq (ready for your tasks)
- **Health Checks:** Built-in health and database connectivity endpoints
- **Clean Architecture:** Ready-to-use structure for your domain implementation

## Architecture

The project follows a clean architecture pattern with clear separation of concerns:

```text
src/app/
├── core/          # Configuration, logging, exceptions, taskiq setup
├── domain/        # Business entities, enums, validators (ready for your implementation)
├── db/            # Database models, repositories, migrations (ready for your models)
├── infra/         # External integrations (ready for your infrastructure)
├── services/      # Business logic orchestration (ready for your services)
└── api/           # FastAPI routes and dependencies
```

## Installation

### Using Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Manual Installation

```bash
# Install uv (package manager)
pip install uv

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit with your credentials
nano .env

# Run database migrations
alembic upgrade head
```

## Configuration

Configure the following environment variables in `.env`:

**Application:**

- `PROJECT_NAME`: Application name (default: "FastAPI Application")
- `VERSION`: Application version (default: "0.1.0")
- `DEBUG`: Enable debug mode (default: true)
- `ENVIRONMENT`: Environment name (default: "development")
- `HOST`: API server host (default: "0.0.0.0")
- `PORT`: API server port (default: 8000)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

**Database:**

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql+asyncpg://user:password@host:port/dbname`
  - Default: `postgresql+asyncpg://postgres:postgres@localhost:5432/app`

**Logging:**

- `LOG_LEVEL`: Logging level (default: "INFO")

**Observability:**

- `PROMETHEUS__ENABLED`: Enable Prometheus metrics (default: true)
- `LOGFIRE__ENABLED`: Enable Logfire integration (default: false)
- `LOGFIRE__WRITE_TOKEN`: Logfire write token (required if Logfire enabled)

## Usage

### Running the API Server

```bash
# Using Docker (API only)
docker-compose up api

# Or start all services
docker-compose up

# Manual
python -m app
```

API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

**Note:** Background tasks are handled via taskiq. Configure taskiq in `src/app/core/taskiq/` and create your task definitions there. The `docker-compose.yml` includes a worker service that references the old worker structure - you may want to update it to use taskiq workers instead.

### API Endpoints

**Health Checks:**

- `GET /api/v1/health` - Service health status
- `GET /api/v1/health/db` - Database connectivity check

## Getting Started

This is a clean FastAPI template ready for your implementation. Here's where to start:

1. **Define your domain models** in `src/app/db/models.py`
2. **Create database migrations** with `alembic revision --autogenerate -m "your description"`
3. **Add your API routes** in `src/app/api/routes/`
4. **Implement business logic** in `src/app/services/`
5. **Add external integrations** in `src/app/infra/` if needed
6. **Configure taskiq** in `src/app/core/taskiq/` for background tasks

The application structure is set up following clean architecture principles with clear separation between domain, database, services, and API layers.

## Development

### Install Development Dependencies

```bash
uv sync --dev
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

Run linting and formatting:

```bash
# Format code
ruff format src/

# Check linting
ruff check src/

# Type checking
mypy src/
```

### Testing

Run tests with coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/app --cov-report=html
```

## Troubleshooting

### Database Connection Errors

- Verify PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/dbname`
- Run migrations: `alembic upgrade head`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
