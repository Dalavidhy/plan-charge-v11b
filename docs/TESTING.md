# Testing Guide for Plan Charge V8

This guide provides comprehensive instructions for running tests in the Plan Charge V8 project.

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Running Tests](#running-tests)
3. [Test Coverage](#test-coverage)
4. [Writing Tests](#writing-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

## Test Environment Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis (optional, for caching tests)

### Initial Setup

1. **Check test environment:**
   ```bash
   ./scripts/check_test_setup.sh
   ```

2. **Backend setup:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   ```

4. **Database setup:**
   ```bash
   # Create test database
   createdb -U plancharge plan_charge_v8_test
   
   # Run migrations
   cd backend
   DATABASE_URL="postgresql://plancharge:plancharge123@localhost:5432/plan_charge_v8_test" alembic upgrade head
   ```

## Running Tests

### Quick Test (Development)

For rapid feedback during development:

```bash
# Run all quick tests
./scripts/quick_test.sh

# Run only backend tests
./scripts/quick_test.sh --backend

# Run only frontend tests
./scripts/quick_test.sh --frontend

# Run tests matching a pattern
./scripts/quick_test.sh --pattern auth
```

### Comprehensive Test Suite

For full test coverage:

```bash
# Run all tests
./scripts/run_all_tests.sh

# Run with parallel execution (faster)
./scripts/run_all_tests.sh --parallel

# Include E2E tests
./scripts/run_all_tests.sh --e2e

# View help
./scripts/run_all_tests.sh --help
```

### Backend Tests Only

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run tests matching pattern
pytest -k "restaurant"

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run with verbose output
pytest -v
```

### Frontend Tests Only

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run tests matching pattern
npm test -- --testNamePattern="auth"

# Run in watch mode (development)
npm test -- --watch

# Run specific test file
npm test -- RestaurantTicketsPreview.test.js
```

## Test Coverage

### Backend Coverage

Coverage reports are automatically generated when running tests with coverage:

```bash
cd backend
pytest --cov=app

# View coverage report in terminal
pytest --cov=app --cov-report=term-missing

# Generate HTML report
pytest --cov=app --cov-report=html

# Open HTML report
open htmlcov/index.html  # On macOS
# xdg-open htmlcov/index.html  # On Linux
```

Coverage thresholds are configured in `.coveragerc`.

### Frontend Coverage

```bash
cd frontend
npm test -- --coverage

# View coverage report
open coverage/lcov-report/index.html  # On macOS
# xdg-open coverage/lcov-report/index.html  # On Linux
```

Coverage thresholds are configured in `jest.config.js`.

## Writing Tests

### Backend Test Structure

```python
# tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestExample:
    """Test suite for example functionality"""
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """Fixture for authenticated requests"""
        response = client.post("/api/v1/auth/login", data={
            "username": test_user.email,
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_example_endpoint(self, auth_headers):
        """Test example endpoint"""
        response = client.get("/api/v1/example", headers=auth_headers)
        assert response.status_code == 200
        assert "data" in response.json()
    
    @pytest.mark.integration
    def test_integration_example(self, db_session):
        """Integration test example"""
        # Test with real database
        pass
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Test marked as slow"""
        # Long-running test
        pass
```

### Frontend Test Structure

```javascript
// src/components/Example.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../../store';
import Example from './Example';

describe('Example Component', () => {
  const renderWithProviders = (component) => {
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    );
  };

  test('renders example component', () => {
    renderWithProviders(<Example />);
    expect(screen.getByText('Example')).toBeInTheDocument();
  });

  test('handles user interaction', async () => {
    renderWithProviders(<Example />);
    
    const button = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
    });
  });
});
```

## CI/CD Integration

Tests are automatically run on GitHub Actions for:

- Every push to `main` and `develop` branches
- Every pull request

The CI pipeline includes:

1. **Backend Tests:**
   - Linting (flake8)
   - Type checking (mypy)
   - Security scanning (bandit)
   - Unit and integration tests
   - Coverage reporting

2. **Frontend Tests:**
   - Linting (ESLint)
   - Unit tests
   - Coverage reporting
   - Build verification

3. **Integration Tests:**
   - Full stack integration tests
   - API endpoint testing

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   ```bash
   # Check PostgreSQL is running
   pg_isready
   
   # Check test database exists
   psql -U plancharge -l | grep plan_charge_v8_test
   ```

2. **Virtual environment issues:**
   ```bash
   # Recreate virtual environment
   cd backend
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Node modules issues:**
   ```bash
   # Clean install dependencies
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Permission errors:**
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   ```

### Test Debugging

1. **Backend test debugging:**
   ```bash
   # Run with debugging output
   pytest -vv -s
   
   # Run with pdb on failure
   pytest --pdb
   
   # Run specific test with full traceback
   pytest tests/test_auth.py::TestAuth::test_login -vv --tb=long
   ```

2. **Frontend test debugging:**
   ```bash
   # Run in debug mode
   npm test -- --detectOpenHandles --forceExit
   
   # Run with Node debugging
   node --inspect-brk node_modules/.bin/jest --runInBand
   ```

### Performance Tips

1. **Parallel test execution:**
   ```bash
   # Backend
   pip install pytest-xdist
   pytest -n auto
   
   # Use the script
   ./scripts/run_all_tests.sh --parallel
   ```

2. **Run only changed tests:**
   ```bash
   # Backend
   pip install pytest-testmon
   pytest --testmon
   
   # Frontend (Jest does this by default in watch mode)
   npm test -- --watch
   ```

3. **Skip slow tests during development:**
   ```bash
   pytest -m "not slow"
   ```

## Test Reports

Test reports are saved in the `test-reports` directory with timestamps:

- `backend_test_YYYYMMDD_HHMMSS.log`
- `frontend_test_YYYYMMDD_HHMMSS.log`
- `test_summary_YYYYMMDD_HHMMSS.log`

Coverage reports:
- Backend: `backend/htmlcov/index.html`
- Frontend: `frontend/coverage/lcov-report/index.html`