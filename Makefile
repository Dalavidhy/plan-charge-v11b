.PHONY: help build up down restart logs shell test clean migrate seed lint format type-check security-check

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_TEST = docker-compose -f docker-compose.test.yml
BACKEND_CONTAINER = plancharge-backend
DB_CONTAINER = plancharge-postgres
REDIS_CONTAINER = plancharge-redis

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "API documentation at http://localhost:8000/docs"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Show backend logs
	$(DOCKER_COMPOSE) logs -f backend

logs-celery: ## Show Celery logs
	$(DOCKER_COMPOSE) logs -f celery celery-beat

shell: ## Open shell in backend container
	$(DOCKER_COMPOSE) exec backend sh

shell-db: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U plancharge -d plancharge

shell-redis: ## Open Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# Database commands
migrate: ## Run database migrations
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

migration-create: ## Create a new migration (usage: make migration-create name="migration_name")
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(name)"

migrate-down: ## Rollback last migration
	$(DOCKER_COMPOSE) exec backend alembic downgrade -1

migrate-history: ## Show migration history
	$(DOCKER_COMPOSE) exec backend alembic history

db-reset: ## Reset database (drop and recreate)
	$(DOCKER_COMPOSE) exec postgres psql -U plancharge -c "DROP DATABASE IF EXISTS plancharge;"
	$(DOCKER_COMPOSE) exec postgres psql -U plancharge -c "CREATE DATABASE plancharge;"
	$(MAKE) migrate
	$(MAKE) seed

seed: ## Seed database with sample data
	$(DOCKER_COMPOSE) exec backend python -m scripts.seed_data

# Testing commands
test: ## Run all tests (build, auth, pages, API)
	@./tests/run-all-tests.sh

test-build: ## Test Docker build process
	@echo "Testing Docker build..."
	@$(DOCKER_COMPOSE) config --quiet
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "✅ Build test passed"

test-auth: ## Test authentication flow with curl
	@echo "Testing authentication..."
	@./tests/auth/test-auth-flow.sh

test-pages: ## Test frontend page accessibility
	@echo "Testing frontend pages..."
	@./tests/frontend/test-pages.sh

test-health: ## Test service health
	@echo "Testing service health..."
	@./tests/docker/wait-for-healthy.sh

test-unit: ## Run unit tests
	$(DOCKER_COMPOSE) exec backend pytest tests/unit -v

test-integration: ## Run integration tests
	$(DOCKER_COMPOSE) exec backend pytest tests/integration -v

test-e2e: ## Run end-to-end tests
	$(DOCKER_COMPOSE) exec backend pytest tests/e2e -v

test-coverage: ## Run tests with coverage report
	$(DOCKER_COMPOSE) exec backend pytest --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	$(DOCKER_COMPOSE) exec backend ptw

test-all: test-health test-auth test-pages ## Run all validation tests
	@echo "✅ All tests passed!"

# Code quality commands
lint: ## Run linting
	$(DOCKER_COMPOSE) exec backend ruff check .

format: ## Format code with black
	$(DOCKER_COMPOSE) exec backend black .
	$(DOCKER_COMPOSE) exec backend isort .

format-check: ## Check code formatting
	$(DOCKER_COMPOSE) exec backend black --check .
	$(DOCKER_COMPOSE) exec backend isort --check-only .

type-check: ## Run type checking with mypy
	$(DOCKER_COMPOSE) exec backend mypy app

security-check: ## Run security checks
	$(DOCKER_COMPOSE) exec backend bandit -r app
	$(DOCKER_COMPOSE) exec backend safety check

quality: lint format-check type-check security-check ## Run all quality checks

# Development utilities
install: ## Install dependencies
	$(DOCKER_COMPOSE) exec backend pip install -r requirements.txt -r requirements-dev.txt

update-deps: ## Update dependencies
	$(DOCKER_COMPOSE) exec backend pip install --upgrade -r requirements.txt -r requirements-dev.txt

freeze: ## Freeze current dependencies
	$(DOCKER_COMPOSE) exec backend pip freeze > requirements.lock

clean: ## Clean up generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache

# Production commands
prod-build: ## Build production images
	docker build -f docker/backend/Dockerfile --target production -t plancharge-backend:latest .

prod-up: ## Start production services
	docker-compose -f docker-compose.prod.yml up -d

prod-deploy: ## Deploy to production (placeholder)
	@echo "Deploy to production - implement based on your infrastructure"

# Monitoring commands
monitor: ## Open monitoring dashboard (if configured)
	@echo "Opening monitoring dashboards..."
	@echo "Flower (Celery): http://localhost:5555"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

# Performance testing
perf-test: ## Run performance tests with Locust
	$(DOCKER_COMPOSE) exec backend locust -f tests/performance/locustfile.py --host http://localhost:8000

# API documentation
api-docs: ## Generate API documentation
	$(DOCKER_COMPOSE) exec backend python -m scripts.generate_openapi

# Backup and restore
backup-db: ## Backup database
	$(DOCKER_COMPOSE) exec postgres pg_dump -U plancharge plancharge > backups/backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database (usage: make restore-db file=backup.sql)
	$(DOCKER_COMPOSE) exec -T postgres psql -U plancharge plancharge < $(file)

# Quick development setup
dev-setup: build up migrate seed ## Complete development setup
	@echo "Development environment ready!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

# Health checks
health: ## Check health of all services
	@echo "Checking service health..."
	@$(DOCKER_COMPOSE) exec backend curl -s http://localhost:8000/health | python -m json.tool
	@$(DOCKER_COMPOSE) exec postgres pg_isready -U plancharge
	@$(DOCKER_COMPOSE) exec redis redis-cli ping
