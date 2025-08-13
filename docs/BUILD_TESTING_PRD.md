# Product Requirements Document: Build Testing & Validation System

## Executive Summary

This PRD defines the comprehensive build testing and validation system for Plan Charge v11b, ensuring all Docker builds work correctly, authentication functions properly, and all pages are accessible before deployment.

## Problem Statement

Current issues:
- Docker builds fail without proper error detection
- No automated validation of authentication flow
- No systematic verification of page accessibility
- Missing integration tests between frontend and backend
- No continuous validation during development

## Goals & Objectives

### Primary Goals
1. **Zero Build Failures**: Ensure Docker Compose builds succeed 100% of the time
2. **Authentication Validation**: Verify JWT authentication works end-to-end
3. **Page Accessibility**: Confirm all frontend pages load correctly
4. **API Integration**: Validate all API endpoints respond correctly
5. **Automated Testing**: Enable CI/CD with confidence

### Success Metrics
- Build success rate: 100%
- Authentication test coverage: 100%
- Page accessibility: 100%
- API endpoint coverage: 100%
- Test execution time: <5 minutes

## Functional Requirements

### 1. Docker Build Validation

#### 1.1 Pre-Build Checks
```bash
# Verify Docker daemon is running
docker info

# Check Docker Compose version
docker compose version

# Validate docker-compose.yml syntax
docker compose config --quiet

# Check for required environment files
test -f .env || cp .env.example .env
```

#### 1.2 Build Process
```bash
# Clean build with no cache
docker compose build --no-cache

# Verify all images built successfully
docker compose images

# Check container health
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status}'
```

#### 1.3 Post-Build Validation
```bash
# Wait for services to be healthy
./scripts/wait-for-healthy.sh

# Verify network connectivity
docker compose exec backend curl -f http://postgres:5432 || exit 1
docker compose exec backend curl -f http://redis:6379 || exit 1
```

### 2. Authentication Testing

#### 2.1 Basic Authentication Flow
```bash
# Test user registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User",
    "org_name": "Test Organization"
  }'

# Test login and capture tokens
LOGIN_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

# Test authenticated endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Test token refresh
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}"

# Test logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

#### 2.2 Advanced Authentication Tests
```bash
# Test invalid credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "wrong@example.com", "password": "wrong"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Test expired token
sleep 900  # Wait for token expiry
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $EXPIRED_TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

# Test password change
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123!",
    "new_password": "NewPass456!"
  }'
```

### 3. Page Accessibility Testing

#### 3.1 Frontend Health Checks
```bash
# Check frontend is running
curl -f http://localhost:5173 || exit 1

# Check static assets are served
curl -f http://localhost:5173/assets/index.js || exit 1

# Check API proxy is working
curl -f http://localhost:5173/api/v1/health || exit 1
```

#### 3.2 Page Route Testing
```bash
# Test all public pages
for route in "/" "/login" "/register" "/forgot-password" "/reset-password"; do
  echo "Testing route: $route"
  curl -f -o /dev/null -s -w "%{http_code}" http://localhost:5173$route
done

# Test protected pages (should redirect to login)
for route in "/dashboard" "/projects" "/allocations" "/people" "/teams"; do
  echo "Testing protected route: $route"
  RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:5173$route)
  if [[ "$RESPONSE" != *"302"* ]] && [[ "$RESPONSE" != *"login"* ]]; then
    echo "Error: Protected route $route is not redirecting to login"
    exit 1
  fi
done
```

#### 3.3 WebSocket Testing
```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/ws \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -x '{"type": "ping"}' \
  -w 5
```

### 4. API Endpoint Testing

#### 4.1 Health Endpoints
```bash
# Backend health
curl -f http://localhost:8000/health || exit 1

# Database health
curl -f http://localhost:8000/api/v1/health/db || exit 1

# Redis health
curl -f http://localhost:8000/api/v1/health/redis || exit 1
```

#### 4.2 CRUD Operations
```bash
# Create organization
ORG_ID=$(curl -X POST http://localhost:8000/api/v1/orgs \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Org", "slug": "test-org"}' \
  | jq -r '.id')

# Read organization
curl -X GET http://localhost:8000/api/v1/orgs/$ORG_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Update organization
curl -X PATCH http://localhost:8000/api/v1/orgs/$ORG_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Org"}'

# Delete organization
curl -X DELETE http://localhost:8000/api/v1/orgs/$ORG_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 5. Integration Testing

#### 5.1 End-to-End User Flow
```bash
#!/bin/bash
# Complete user journey test

# 1. Register new user
./tests/e2e/01-register.sh

# 2. Login and get token
TOKEN=$(./tests/e2e/02-login.sh)

# 3. Create organization
ORG_ID=$(./tests/e2e/03-create-org.sh $TOKEN)

# 4. Create project
PROJECT_ID=$(./tests/e2e/04-create-project.sh $TOKEN $ORG_ID)

# 5. Create person
PERSON_ID=$(./tests/e2e/05-create-person.sh $TOKEN $ORG_ID)

# 6. Create allocation
ALLOCATION_ID=$(./tests/e2e/06-create-allocation.sh $TOKEN $PROJECT_ID $PERSON_ID)

# 7. Generate report
./tests/e2e/07-generate-report.sh $TOKEN $ORG_ID

# 8. Cleanup
./tests/e2e/99-cleanup.sh $TOKEN
```

#### 5.2 Performance Testing
```bash
# Load test authentication endpoint
ab -n 1000 -c 10 \
  -p login.json \
  -T application/json \
  http://localhost:8000/api/v1/auth/login

# Stress test API
siege -c 20 -t 60s \
  --header="Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/projects
```

## Non-Functional Requirements

### Performance Requirements
- Build time: <3 minutes
- Test execution: <5 minutes
- API response time: <200ms (p95)
- Frontend load time: <2 seconds

### Security Requirements
- All tests use HTTPS in production
- Tokens are never logged
- Test data is isolated
- Sensitive data is masked

### Reliability Requirements
- Tests are idempotent
- Automatic retry on transient failures
- Clear error messages
- Rollback capability

## Implementation Plan

### Phase 1: Infrastructure (Day 1)
- [ ] Create test scripts directory structure
- [ ] Setup test data fixtures
- [ ] Configure test environment variables
- [ ] Create wait-for-healthy script

### Phase 2: Build Validation (Day 2)
- [ ] Implement Docker build checks
- [ ] Create build validation script
- [ ] Setup health check monitoring
- [ ] Add container dependency validation

### Phase 3: Authentication Tests (Day 3)
- [ ] Implement registration tests
- [ ] Create login/logout tests
- [ ] Add token refresh tests
- [ ] Build permission tests

### Phase 4: Integration Tests (Day 4)
- [ ] Create page accessibility tests
- [ ] Implement API endpoint tests
- [ ] Build E2E user flows
- [ ] Add WebSocket tests

### Phase 5: Automation (Day 5)
- [ ] Create Makefile targets
- [ ] Setup GitHub Actions workflow
- [ ] Configure pre-commit hooks
- [ ] Document test procedures

## Test Script Structure

```
tests/
├── docker/
│   ├── build-test.sh
│   ├── health-check.sh
│   └── wait-for-healthy.sh
├── auth/
│   ├── register.sh
│   ├── login.sh
│   ├── refresh.sh
│   └── logout.sh
├── api/
│   ├── organizations.sh
│   ├── projects.sh
│   ├── allocations.sh
│   └── reports.sh
├── frontend/
│   ├── pages.sh
│   ├── assets.sh
│   └── routing.sh
├── e2e/
│   ├── user-journey.sh
│   ├── admin-workflow.sh
│   └── allocation-flow.sh
├── performance/
│   ├── load-test.sh
│   └── stress-test.sh
└── run-all-tests.sh
```

## Makefile Targets

```makefile
# Test targets
test-build:
	@echo "Testing Docker build..."
	@./tests/docker/build-test.sh

test-auth:
	@echo "Testing authentication..."
	@./tests/auth/login.sh

test-pages:
	@echo "Testing page accessibility..."
	@./tests/frontend/pages.sh

test-api:
	@echo "Testing API endpoints..."
	@./tests/api/organizations.sh

test-e2e:
	@echo "Running E2E tests..."
	@./tests/e2e/user-journey.sh

test-all: test-build test-auth test-pages test-api test-e2e
	@echo "All tests passed!"

# Development helpers
dev-test:
	@docker compose up -d
	@./tests/docker/wait-for-healthy.sh
	@make test-all
	@docker compose down

ci-test:
	@docker compose -f docker-compose.ci.yml up -d
	@./tests/docker/wait-for-healthy.sh
	@make test-all
	@docker compose -f docker-compose.ci.yml down -v
```

## GitHub Actions Workflow

```yaml
name: Build and Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Create .env file
      run: cp .env.example .env
    
    - name: Build Docker images
      run: docker compose build
    
    - name: Start services
      run: docker compose up -d
    
    - name: Wait for services
      run: ./tests/docker/wait-for-healthy.sh
      timeout-minutes: 5
    
    - name: Run authentication tests
      run: ./tests/auth/login.sh
    
    - name: Run API tests
      run: ./tests/api/organizations.sh
    
    - name: Run frontend tests
      run: ./tests/frontend/pages.sh
    
    - name: Run E2E tests
      run: ./tests/e2e/user-journey.sh
    
    - name: Collect logs on failure
      if: failure()
      run: docker compose logs
    
    - name: Cleanup
      if: always()
      run: docker compose down -v
```

## Success Criteria

### Acceptance Criteria
- [ ] All Docker builds complete successfully
- [ ] Authentication flow works end-to-end
- [ ] All frontend pages are accessible
- [ ] All API endpoints respond correctly
- [ ] Tests run in under 5 minutes
- [ ] CI/CD pipeline is green

### Definition of Done
- [ ] All test scripts are implemented
- [ ] Documentation is complete
- [ ] Makefile targets work
- [ ] GitHub Actions workflow passes
- [ ] Team is trained on test procedures
- [ ] Monitoring alerts are configured

## Risk Mitigation

### Identified Risks
1. **Docker build failures**: Mitigated by pre-build validation
2. **Network timeouts**: Handled with retry logic
3. **Database migrations**: Validated before tests
4. **Token expiry**: Managed with refresh logic
5. **Resource constraints**: Monitored and limited

### Contingency Plans
- Rollback procedures documented
- Manual test fallbacks available
- Debug mode for troubleshooting
- Comprehensive logging enabled

## Maintenance & Evolution

### Regular Maintenance
- Weekly test suite review
- Monthly performance baseline update
- Quarterly security audit
- Annual test strategy review

### Future Enhancements
- Visual regression testing
- Mutation testing
- Chaos engineering tests
- AI-powered test generation
- Cross-browser testing
- Mobile app testing

## Conclusion

This comprehensive testing system ensures Plan Charge v11b maintains high quality and reliability through automated validation of builds, authentication, and functionality. The combination of unit, integration, and E2E tests provides confidence in deployments and rapid feedback during development.