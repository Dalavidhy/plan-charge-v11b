# Plan Charge - Multi-Team Resource Planning System

A comprehensive resource planning and management system designed for organizations managing multiple teams, projects, and resource allocations.

## 🚀 Features

### Core Functionality
- **Organization Management**: Multi-tenant support with hierarchical organization structure
- **Team Management**: Create and manage teams with role-based members
- **Resource Planning**: Advanced allocation system with conflict detection
- **Project Management**: Comprehensive project and task tracking
- **Calendar Integration**: Holiday management and capacity planning
- **Analytics & Reporting**: Real-time utilization and capacity reports
- **Identity Matching**: Smart deduplication across data sources

### Technical Features
- **Modern Stack**: FastAPI + React with TypeScript
- **Authentication**: JWT-based auth with refresh tokens
- **Role-Based Access**: 5-tier permission system (Owner, Admin, Manager, Member, Viewer)
- **Real-time Updates**: WebSocket support for live data
- **Async Architecture**: High-performance async/await patterns
- **Docker Native**: Complete containerized deployment
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 14 with UUID support
- **ORM**: SQLAlchemy 2.0 with async support
- **Cache**: Redis 7
- **Queue**: Celery with Redis broker
- **Auth**: JWT with access/refresh tokens
- **Testing**: Pytest with async support

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn/ui with Radix UI
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: React Query + Axios
- **Forms**: React Hook Form with Zod validation
- **Charts**: Recharts

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx (production)
- **Database Migrations**: Alembic

## 📋 Prerequisites

- Docker Desktop (latest version)
- Git
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/plan-charge-v11b.git
cd plan-charge-v11b
```

### 2. Setup Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration (optional for development)
# Default values work out of the box
```

### 3. Start the Application
```bash
# Start in development mode (with hot reload)
./start.sh

# OR start in detached mode
./start.sh -d

# OR start in production mode
./start.sh --prod
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: plancharge, password: plancharge123)
- **Redis**: localhost:6379

## 🔧 Development

### Using Make Commands
```bash
# Setup development environment
make dev

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Create new migration
make migration name="add_new_table"

# Apply migrations
make migrate

# Seed database with sample data
make seed

# View logs
make logs

# Stop all services
make down

# Clean everything (including volumes)
make clean
```

### Manual Docker Commands
```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after changes
docker compose up --build

# Access backend shell
docker compose exec backend bash

# Access database
docker compose exec postgres psql -U plancharge -d plancharge

# Run backend tests
docker compose exec backend pytest

# Run frontend tests
docker compose exec frontend npm test
```

### Database Operations
```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback migration
docker compose exec backend alembic downgrade -1

# Seed sample data
docker compose exec backend python -m app.scripts.seed_data
```

## 📁 Project Structure

```
plan-charge-v11b/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── core/           # Core utilities
│   │   └── tests/          # Test suite
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   ├── stores/        # State management
│   │   └── utils/         # Utilities
│   └── package.json       # Node dependencies
│
├── docker/                # Docker configuration
│   ├── backend/          # Backend Dockerfile
│   ├── frontend/         # Frontend Dockerfile
│   ├── nginx/            # Nginx configuration
│   ├── postgres/         # PostgreSQL init scripts
│   └── redis/            # Redis configuration
│
├── docs/                 # Documentation
├── docker-compose.yml    # Development configuration
├── docker-compose.prod.yml # Production configuration
├── Makefile             # Development shortcuts
└── start.sh             # Startup script
```

## 🔐 Authentication

The system uses JWT authentication with:
- **Access Token**: 15 minutes expiry
- **Refresh Token**: 30 days expiry
- **Automatic token refresh** on 401 responses
- **Secure token storage** in localStorage (dev) / httpOnly cookies (prod)

### Default Users (Development)
After seeding, you can login with:
- **Admin**: admin@example.com / password123
- **Manager**: manager@example.com / password123
- **User**: user@example.com / password123

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/test_auth.py

# Run tests in parallel
docker compose exec backend pytest -n auto
```

### Frontend Tests
```bash
# Run tests
docker compose exec frontend npm test

# Run with UI
docker compose exec frontend npm run test:ui

# Run with coverage
docker compose exec frontend npm run test:coverage
```

### E2E Tests
```bash
# Run end-to-end tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication Flow
1. POST `/api/v1/auth/login` with email/password
2. Receive access_token and refresh_token
3. Include `Authorization: Bearer {access_token}` in requests
4. POST `/api/v1/auth/refresh` when token expires
5. POST `/api/v1/auth/logout` to invalidate tokens

### Main Endpoints
- `/api/v1/orgs` - Organization management
- `/api/v1/people` - People management
- `/api/v1/teams` - Team management
- `/api/v1/projects` - Project management
- `/api/v1/tasks` - Task management
- `/api/v1/allocations` - Resource allocations
- `/api/v1/calendars` - Calendar management
- `/api/v1/reports` - Analytics and reports

## 🚢 Production Deployment

### AWS Infrastructure
The application is deployed on AWS using:
- **ECS Fargate** for containerized services
- **Application Load Balancer** for traffic routing
- **CloudFront CDN** for global distribution
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for caching

For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Quick Deployment
```bash
# Build and push Docker images to ECR
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin [ACCOUNT].dkr.ecr.eu-west-3.amazonaws.com
docker build -t plan-charge-backend backend/
docker tag plan-charge-backend:latest [ACCOUNT].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/backend:latest
docker push [ACCOUNT].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/backend:latest

# Update ECS service
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --force-new-deployment

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E3U93II4ZE9MCI --paths "/*"
```

### Environment Variables
Key production variables (stored in AWS Secrets Manager):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Strong random secret
- `CORS_ORIGINS`: https://plan-de-charge.aws.nda-partners.com
- `AZURE_CLIENT_ID`: Azure AD application ID
- `AZURE_TENANT_ID`: Azure AD tenant ID

### Database Backup
```bash
# Backup RDS database
aws rds create-db-snapshot --db-instance-identifier plan-charge-prod-db --db-snapshot-identifier backup-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot --db-instance-identifier plan-charge-prod-db-restored --db-snapshot-identifier backup-20240115
```

## 🔧 Troubleshooting

For production issues and their solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Common Development Issues

**Port Already in Use**
```bash
# Find process using port
lsof -i :3000  # or :8000, :5432, :6379

# Kill process
kill -9 <PID>
```

**Docker Space Issues**
```bash
# Clean Docker system
docker system prune -a --volumes
```

**Database Connection Issues**
```bash
# Check database status
docker compose exec postgres pg_isready

# View database logs
docker compose logs postgres
```

**Frontend Not Loading**
```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose up --build frontend
```

## 📝 License

This project is proprietary and confidential.

## 🤝 Support

For issues or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in `/docs`

## 🚀 Roadmap

- [ ] Multi-language support
- [ ] Advanced reporting dashboard
- [ ] Mobile application
- [ ] Third-party integrations (Jira, Slack, Teams)
- [ ] AI-powered resource optimization
- [ ] Real-time collaboration features

---

Built with ❤️ by the Plan Charge Team
