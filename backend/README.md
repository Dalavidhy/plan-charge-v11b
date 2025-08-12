# Plan Charge v9 - Backend

## Overview

Plan Charge v9 is a multi-team resource planning and capacity management system built with FastAPI, PostgreSQL, and Redis.

## Features

- 🔐 **JWT Authentication** with access/refresh tokens
- 👥 **Multi-organization** support with RBAC (Role-Based Access Control)
- 📅 **Resource Planning** with allocation and capacity management
- 🔍 **Conflict Detection** for over-allocation and scheduling conflicts
- 📊 **Advanced Reporting** with utilization and capacity analytics
- 🔄 **External Integrations** (Payfit, Gryzzly) with identity matching
- 🎯 **RESTful API** with OpenAPI documentation
- 🐳 **Docker-ready** with development and production configurations
- ⚡ **High Performance** with Redis caching and async operations
- 🧪 **Comprehensive Testing** with pytest and coverage reporting

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0
- **Cache/Queue**: Redis 7+
- **Task Queue**: Celery
- **Authentication**: JWT with python-jose
- **Testing**: pytest, pytest-asyncio
- **Containerization**: Docker & Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Make (optional, for convenience commands)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd plan-charge-v11b
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker**
   ```bash
   make dev-setup  # Builds, starts services, runs migrations, and seeds data
   # OR manually:
   docker-compose up -d
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python -m scripts.seed_data
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/health

### Available Make Commands

```bash
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make logs           # Show logs
make shell          # Open shell in backend container
make test           # Run all tests
make migrate        # Run database migrations
make seed           # Seed database with sample data
make format         # Format code with black
make lint           # Run linting
make clean          # Clean up generated files
```

## API Documentation

### Authentication

The API uses JWT for authentication. To get started:

1. **Login** to get access and refresh tokens:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@demo.com", "password": "demo123"}'
   ```

2. **Use the access token** in subsequent requests:
   ```bash
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <access_token>"
   ```

### Default Credentials (Development)

After running the seed script, you can login with:
- Admin: `admin@demo.com` / `demo123`
- Manager: `john@demo.com` / `demo123`
- Member: `jane@demo.com` / `demo123`

### Key Endpoints

- **Auth**: `/api/v1/auth/*`
- **Organizations**: `/api/v1/orgs/*`
- **People**: `/api/v1/people/*`
- **Teams**: `/api/v1/teams/*`
- **Projects**: `/api/v1/projects/*`
- **Tasks**: `/api/v1/tasks/*`
- **Allocations**: `/api/v1/allocations/*`
- **Reports**: `/api/v1/reports/*`
- **Integrations**: `/api/v1/integrations/*`

Full API documentation is available at `/api/v1/docs` when running in development mode.

## Database Schema

The database follows the schema defined in the PRD with the following key entities:
- Organizations, People, Users, Teams
- Projects, Tasks, Epics
- Allocations, Capacities, Calendars
- External Integrations and Identity Matching
- Benefits and Audit Logs

## Testing

### Run All Tests
```bash
make test
# OR
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Run Specific Tests
```bash
# Unit tests
docker-compose exec backend pytest tests/unit -v

# Integration tests
docker-compose exec backend pytest tests/integration -v

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html
```

### Test Coverage
Coverage reports are generated in `htmlcov/` directory.

## Development

### Project Structure
```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── middleware/    # Custom middleware
│   └── utils/         # Utility functions
├── migrations/        # Alembic migrations
├── tests/            # Test suite
└── scripts/          # Utility scripts
```

### Code Quality

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing

Run quality checks:
```bash
make quality  # Runs all quality checks
make format   # Format code
make lint     # Check linting
make type-check  # Type checking
```

### Adding New Features

1. Create/update models in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add API endpoints in `app/api/v1/`
5. Create tests in `tests/`
6. Generate migration: `make migration-create name="feature_name"`
7. Run migration: `make migrate`

## Production Deployment

### Using Docker Compose

1. **Set production environment variables**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Build and start production services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables

Key environment variables for production:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT (use strong random string)
- `ENVIRONMENT`: Set to "production"
- `CORS_ORIGINS`: Allowed CORS origins

### Security Considerations

- Always use HTTPS in production
- Set strong JWT secret keys
- Configure proper CORS origins
- Enable rate limiting
- Use environment-specific configurations
- Regularly update dependencies
- Monitor logs and metrics

## Monitoring

The application provides:
- Health check endpoint: `/health`
- Readiness endpoint: `/ready`
- Prometheus metrics: `/metrics` (when enabled)
- Structured JSON logging

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Stop conflicting service or change port in docker-compose.yml
   ```

2. **Database connection issues**
   ```bash
   # Check database is running
   docker-compose ps
   # Check logs
   docker-compose logs postgres
   ```

3. **Migration issues**
   ```bash
   # Reset database (development only!)
   make db-reset
   ```

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Run code quality checks
6. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.