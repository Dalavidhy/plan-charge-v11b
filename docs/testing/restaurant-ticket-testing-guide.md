# Restaurant Ticket Testing Guide

## Overview

This guide provides comprehensive documentation for testing the Restaurant Ticket feature, including test setup, execution, and quality assurance processes.

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Quality Metrics](#quality-metrics)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Troubleshooting](#troubleshooting)

## Test Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up test database
createdb plan_charge_test
alembic upgrade head

# Install additional test dependencies
pip install pytest-cov pytest-mock locust bandit safety
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest-junit
```

### Environment Variables

Create a `.env.test` file:

```env
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/plan_charge_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key
TESTING=true
PAYFIT_API_KEY=test-key
GRYZZLY_API_KEY=test-key
```

## Test Structure

```
tests/
├── conftest.py                    # Global test configuration and fixtures
├── test_config.py                 # Test environment settings
├── services/
│   └── restaurant_ticket/
│       ├── test_matricule_mapping.py
│       ├── test_working_days_calculator.py
│       └── test_csv_generator.py
├── api/
│   └── test_restaurant_ticket_endpoints.py
├── integration/
│   └── test_restaurant_ticket_integration.py
├── security/
│   └── test_restaurant_ticket_security.py
├── performance/
│   └── locustfile.py
└── e2e/
    └── test_restaurant_ticket_e2e.py
```

## Running Tests

### All Tests

```bash
# Run comprehensive test suite
cd backend
python run_all_tests.py

# This will:
# - Run all test categories
# - Generate coverage reports
# - Check quality gates
# - Create HTML and JSON reports
```

### Unit Tests

```bash
# Backend unit tests with coverage
pytest tests/services/restaurant_ticket/ -v --cov=app.services.restaurant_ticket --cov-report=html

# Frontend unit tests
cd frontend
npm test -- --coverage --testPathPattern=restaurant-tickets
```

### Integration Tests

```bash
# Backend integration tests
pytest tests/integration/test_restaurant_ticket_integration.py -v

# API endpoint tests
pytest tests/api/test_restaurant_ticket_endpoints.py -v
```

### Security Tests

```bash
# Security test suite
pytest tests/security/test_restaurant_ticket_security.py -v

# Static security analysis
bandit -r app/services/restaurant_ticket/

# Dependency vulnerability check
safety check
```

### Performance Tests

```bash
# Run locust performance tests
locust -f tests/performance/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 300s \
  --host http://localhost:8000 \
  --html performance_report.html
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Coverage Areas**:
- Matricule mapping service
- Working days calculator
- CSV generator
- Data validation
- Business logic

**Key Test Cases**:
- CRUD operations for matricule mappings
- Working days calculation with various absence types
- CSV generation with edge cases
- Input validation boundaries

### 2. Integration Tests

**Purpose**: Test component interactions and workflows

**Coverage Areas**:
- End-to-end generation workflow
- Database transactions
- External service integration
- Data consistency

**Key Test Cases**:
- Complete generation process
- PayFit data synchronization
- Concurrent operations handling
- Error recovery scenarios

### 3. API Tests

**Purpose**: Test REST API endpoints

**Coverage Areas**:
- Endpoint functionality
- Request/response validation
- Authentication/authorization
- Error handling

**Key Test Cases**:
- CRUD operations via API
- Bulk operations
- File upload/download
- Permission checks

### 4. Security Tests

**Purpose**: Identify and prevent security vulnerabilities

**Coverage Areas**:
- SQL injection prevention
- XSS protection
- Path traversal prevention
- CSV injection prevention
- Authentication bypass attempts
- Rate limiting

**Key Test Cases**:
- Malicious input handling
- Authorization levels
- Sensitive data exposure
- File upload security

### 5. Performance Tests

**Purpose**: Ensure system meets performance requirements

**Scenarios**:
- Light load: 10 users, 1 spawn/s, 60s
- Medium load: 50 users, 5 spawn/s, 300s
- Heavy load: 200 users, 10 spawn/s, 600s
- Stress test: 500 users, 20 spawn/s, 300s

**Metrics**:
- Response time (avg, min, max, p95, p99)
- Requests per second
- Error rate
- Resource utilization

### 6. Frontend Tests

**Purpose**: Test React components and user interactions

**Coverage Areas**:
- Component rendering
- User interactions
- State management
- API integration
- Error states

**Key Test Cases**:
- Form validation
- Preview functionality
- Error handling
- Loading states
- Accessibility

## Quality Metrics

### Code Coverage Requirements

- **Overall**: ≥90%
- **Critical paths**: 100%
- **New code**: ≥95%

### Performance Thresholds

- **API Response Time**: <500ms (avg), <1000ms (p95)
- **CSV Generation**: <2s for 1000 employees
- **Frontend Load**: <3s initial, <1s subsequent
- **Error Rate**: <1%

### Security Standards

- **OWASP Top 10**: Full compliance
- **Dependency vulnerabilities**: Zero high/critical
- **Static analysis**: No high-severity findings

## CI/CD Pipeline

### Pipeline Stages

1. **Code Quality**
   - Linting (ESLint, Flake8)
   - Type checking (mypy, TypeScript)
   - Code formatting (Black, Prettier)

2. **Testing**
   - Unit tests
   - Integration tests
   - Security scans
   - Performance tests (on main branch)

3. **Quality Gates**
   - Coverage threshold: 90%
   - Performance threshold: <500ms
   - Security score: >95%
   - All tests passing

4. **Deployment**
   - Staging (develop branch)
   - Production (main branch)
   - Smoke tests
   - Rollback procedures

### GitHub Actions Workflow

The CI/CD pipeline is configured in `.github/workflows/restaurant-ticket-tests.yml`

**Triggers**:
- Push to main, develop, feature/restaurant-tickets
- Pull requests to main, develop
- Manual workflow dispatch

**Jobs**:
- Backend tests (unit, integration, API, security)
- Frontend tests
- Performance tests (main branch only)
- Quality gate check
- Deployment (staging/production)

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL is running
pg_isready

# Verify connection string
psql $DATABASE_URL

# Reset test database
dropdb plan_charge_test
createdb plan_charge_test
alembic upgrade head
```

#### 2. Redis Connection Errors

```bash
# Check Redis is running
redis-cli ping

# Clear Redis cache
redis-cli FLUSHDB
```

#### 3. Test Failures

```bash
# Run specific test with verbose output
pytest path/to/test.py::TestClass::test_method -vvs

# Debug with pdb
pytest path/to/test.py --pdb

# Check test logs
tail -f backend.log
```

#### 4. Coverage Issues

```bash
# Generate detailed coverage report
pytest --cov=app.services.restaurant_ticket --cov-report=html --cov-report=term-missing

# View uncovered lines
open htmlcov/index.html
```

#### 5. Performance Test Issues

```bash
# Run with lower load
locust -f tests/performance/locustfile.py --users 10 --spawn-rate 1

# Monitor system resources
htop
iostat -x 1
```

### Best Practices

1. **Test Data Management**
   - Use factories for consistent test data
   - Clean up after each test
   - Avoid hardcoded values

2. **Test Isolation**
   - Each test should be independent
   - Use transactions and rollback
   - Mock external services

3. **Assertion Quality**
   - Test behavior, not implementation
   - Use descriptive assertion messages
   - Cover edge cases

4. **Performance Testing**
   - Use realistic data volumes
   - Test with production-like infrastructure
   - Monitor resource usage

5. **Security Testing**
   - Keep security test payloads updated
   - Test with different user roles
   - Verify error messages don't leak info

## Test Reporting

### Generated Reports

- `test_reports/test_summary.json` - Overall test summary
- `test_reports/test_report.html` - HTML dashboard
- `htmlcov/index.html` - Coverage report
- `performance_report.html` - Locust performance report
- `security-report.json` - Bandit security findings

### Metrics Dashboard

Access the test metrics dashboard at:
- Coverage: `htmlcov/index.html`
- Performance: `performance_report.html`
- CI/CD: GitHub Actions tab

## Continuous Improvement

1. **Weekly Reviews**
   - Review test failures
   - Update test cases
   - Improve coverage

2. **Monthly Audits**
   - Performance baseline updates
   - Security payload updates
   - Dependency updates

3. **Quarterly Planning**
   - Test strategy review
   - Tool evaluation
   - Training needs

## Support

For test-related issues:
1. Check this guide
2. Review test logs
3. Contact QA team
4. Create GitHub issue with test label