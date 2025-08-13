# Authentication Testing PRD
## Product Requirements Document for Backend/Frontend Authentication Integration Testing

### Executive Summary
This document outlines the comprehensive testing strategy for validating the authentication system integration between the FastAPI backend and React frontend in the Plan Charge v11b application. The testing will ensure all authentication endpoints work correctly, security measures are in place, and the frontend can successfully integrate with the backend authentication system.

---

## 1. Testing Objectives

### Primary Goals
1. **Validate Backend Authentication Endpoints** - Ensure all auth endpoints work as expected
2. **Test Security Implementation** - Verify JWT tokens, password hashing, and session management
3. **Frontend Integration Testing** - Confirm the frontend can successfully authenticate users
4. **End-to-End Flow Validation** - Test complete user journeys from registration to logout
5. **Error Handling Verification** - Ensure proper error messages and HTTP status codes

### Success Criteria
- ✅ All authentication endpoints return correct HTTP status codes
- ✅ JWT tokens are properly generated and validated
- ✅ Password hashing uses secure algorithms (Argon2)
- ✅ Frontend can register, login, and access protected routes
- ✅ Session management works correctly
- ✅ Rate limiting and security headers are in place

---

## 2. Current Issues to Resolve

### Backend Issues Identified
1. **Registration Endpoint Issue** - JSON parsing error with escape characters
2. **Missing User Model Fields** - User model may be missing required fields
3. **Database Schema** - Tables may not be created via Alembic migrations
4. **CORS Configuration** - Ensure CORS allows frontend requests

### Required Fixes
```python
# 1. Fix User model to ensure all required fields
# 2. Run Alembic migrations to create tables
# 3. Validate password requirements
# 4. Fix JSON parsing in request handling
```

---

## 3. Testing Phases

### Phase 1: Backend API Testing (Current Phase)
**Duration**: 30 minutes
**Status**: IN PROGRESS

#### 1.1 Database Setup
```bash
# Run Alembic migrations
docker compose exec backend alembic upgrade head

# Verify tables exist
docker compose exec postgres psql -U plancharge -c "\dt"
```

#### 1.2 Authentication Endpoints Testing
```bash
# Test each endpoint with curl commands
POST   /api/v1/auth/register     # User registration
POST   /api/v1/auth/login        # User login
GET    /api/v1/auth/me           # Get current user
POST   /api/v1/auth/refresh      # Refresh tokens
POST   /api/v1/auth/logout       # User logout
POST   /api/v1/auth/change-password  # Change password
POST   /api/v1/auth/forgot-password  # Password reset request
POST   /api/v1/auth/reset-password   # Password reset confirm
```

#### 1.3 Test Scenarios
- **Happy Path**: Valid registration → login → access protected endpoint → logout
- **Error Cases**: 
  - Duplicate email registration
  - Invalid credentials
  - Expired tokens
  - Missing required fields
  - Invalid password format

### Phase 2: Frontend Page Accessibility
**Duration**: 20 minutes
**Status**: PENDING

#### 2.1 Static Page Testing
```bash
# Test frontend build
curl http://localhost:3000/            # Home page
curl http://localhost:3000/login       # Login page
curl http://localhost:3000/register    # Register page
curl http://localhost:3000/dashboard   # Dashboard (protected)
```

#### 2.2 Asset Loading
- Verify CSS/JS bundles load correctly
- Check for 404 errors on static assets
- Validate API endpoint configuration

### Phase 3: Integration Testing
**Duration**: 45 minutes
**Status**: PENDING

#### 3.1 Frontend-Backend Communication
- Test API calls from React to FastAPI
- Verify token storage in localStorage/cookies
- Test protected route navigation
- Validate error handling in UI

#### 3.2 User Flows
1. **Registration Flow**
   - Fill registration form
   - Submit to backend
   - Handle success/error responses
   - Auto-redirect to login

2. **Login Flow**
   - Enter credentials
   - Submit login request
   - Store tokens
   - Redirect to dashboard

3. **Protected Routes**
   - Access without token → redirect to login
   - Access with valid token → show content
   - Token expiry handling

---

## 4. Test Implementation Plan

### Step 1: Fix Backend Issues (10 minutes)
```python
# Tasks to complete:
1. Run Alembic migrations to create database tables
2. Fix User model if needed
3. Ensure password validation works
4. Test with simple curl commands first
```

### Step 2: Create Test Scripts (15 minutes)
```bash
# Create comprehensive test scripts:
1. tests/auth/test-backend-auth.sh     # Backend API tests
2. tests/auth/test-frontend-pages.sh   # Frontend accessibility
3. tests/auth/test-integration.sh      # Full integration tests
```

### Step 3: Execute Tests (20 minutes)
```bash
# Run tests in sequence:
1. Backend health check
2. Database connectivity
3. Authentication endpoints
4. Frontend pages
5. Integration flows
```

### Step 4: Document Results (10 minutes)
- Create test report with pass/fail status
- Document any remaining issues
- Provide recommendations for fixes

---

## 5. Expected Test Outputs

### Successful Backend Test
```json
{
  "registration": {
    "status": 201,
    "response": {
      "id": "uuid",
      "email": "test@example.com",
      "message": "User registered successfully"
    }
  },
  "login": {
    "status": 200,
    "response": {
      "access_token": "jwt_token",
      "refresh_token": "refresh_token",
      "token_type": "bearer",
      "user": {
        "id": "uuid",
        "email": "test@example.com",
        "full_name": "Test User"
      }
    }
  },
  "protected_endpoint": {
    "status": 200,
    "response": {
      "user_data": "..."
    }
  }
}
```

### Successful Frontend Test
```
✅ Home page loads (200 OK)
✅ Login page accessible (200 OK)
✅ Register page accessible (200 OK)
✅ Static assets load correctly
✅ API endpoint configured properly
```

---

## 6. Tools and Scripts Required

### Backend Testing Tools
- **curl** - Direct API testing
- **jq** - JSON parsing
- **PostgreSQL client** - Database verification
- **Python** - Script automation

### Frontend Testing Tools
- **curl/wget** - Page accessibility
- **Chrome DevTools** - Manual testing
- **Playwright** (optional) - E2E automation

### Test Scripts to Create
1. `test-auth-backend.sh` - Complete backend auth testing
2. `test-frontend-pages.sh` - Frontend accessibility checks
3. `test-integration.sh` - Full stack integration tests
4. `test-performance.sh` - Load and performance testing

---

## 7. Risk Mitigation

### Potential Issues and Solutions

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database tables not created | HIGH | Run Alembic migrations first |
| CORS blocking requests | HIGH | Verify CORS configuration |
| Password validation failing | MEDIUM | Check password requirements |
| Token expiry too short | MEDIUM | Adjust JWT settings |
| Frontend env vars wrong | HIGH | Verify VITE_API_URL |

---

## 8. Acceptance Criteria

### Backend
- [ ] All auth endpoints return correct status codes
- [ ] Registration creates user in database
- [ ] Login returns valid JWT tokens
- [ ] Protected endpoints require valid token
- [ ] Token refresh works correctly
- [ ] Logout invalidates tokens

### Frontend
- [ ] All pages load without errors
- [ ] Login form submits correctly
- [ ] Registration form validates input
- [ ] Protected routes redirect when unauthorized
- [ ] Tokens stored securely
- [ ] Logout clears session

### Integration
- [ ] User can complete full registration flow
- [ ] Login persists across page refreshes
- [ ] Token expiry handled gracefully
- [ ] Error messages display correctly
- [ ] Loading states work properly

---

## 9. Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Backend Testing | 30 min | IN PROGRESS |
| Frontend Testing | 20 min | PENDING |
| Integration Testing | 45 min | PENDING |
| Documentation | 10 min | PENDING |
| **Total** | **1h 45min** | - |

---

## 10. Next Steps

1. **Immediate Actions** (Now)
   - Run Alembic migrations
   - Fix any model issues
   - Create test scripts

2. **Testing Execution** (Next 30 min)
   - Run backend tests
   - Verify all endpoints
   - Document results

3. **Frontend Integration** (Following 45 min)
   - Test page accessibility
   - Verify API integration
   - Complete E2E flows

4. **Completion** (Final 30 min)
   - Create test report
   - Document any issues
   - Prepare CI/CD workflow

---

## Appendix: Test Commands

### Quick Backend Test
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

### Quick Frontend Test
```bash
# Check if frontend is running
curl -I http://localhost:3000/

# Check API configuration
curl http://localhost:3000/ | grep -o "VITE_API_URL"
```

---

**Document Version**: 1.0
**Created**: August 2024
**Status**: ACTIVE
**Owner**: Development Team