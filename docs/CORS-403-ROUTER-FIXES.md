# CORS, Authentication, and React Router Fixes

## Date: 2024-07-24

This document describes the fixes applied to resolve CORS configuration issues, 403 Forbidden errors on Gryzzly API endpoints, and React Router v7 warnings.

## Issues Identified

### 1. CORS Configuration Issues
**Problem**: Frontend (localhost:3000) was unable to access backend (localhost:8000) due to CORS restrictions.

**Root Cause**: 
- CORS origins were not being parsed correctly from the environment variable
- Missing proper logging for debugging CORS configuration

### 2. 403 Forbidden Errors on Gryzzly API Endpoints
**Problem**: All Gryzzly API endpoints were returning 403 Forbidden errors.

**Root Causes**:
- Authentication token not being sent properly from frontend
- Some endpoints require superuser privileges (admin)
- Incorrect HTTP status code (403 instead of 401) for authentication failures

### 3. React Router v7 Warning
**Problem**: Console warning about `startTransition` when using React Router.

**Root Cause**: 
- Using future flags (`v7_relativeSplatPath`) that require React 18's startTransition
- Unnecessary imports from React Router

## Fixes Applied

### 1. Backend CORS Configuration (backend/app/main.py)

```python
# Set up CORS
# Parse CORS origins and ensure they're properly formatted
if isinstance(settings.BACKEND_CORS_ORIGINS, str):
    origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")]
elif isinstance(settings.BACKEND_CORS_ORIGINS, list):
    origins = settings.BACKEND_CORS_ORIGINS
else:
    origins = ["http://localhost:3000"]

# Log CORS configuration for debugging
print(f"CORS Origins configured: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

**Changes**:
- Added proper parsing of CORS origins from environment variable
- Added logging for debugging
- Added `expose_headers` parameter to expose all headers

### 2. Authentication Error Handling (backend/app/api/deps.py)

```python
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Changes**:
- Changed status code from 403 to 401 for authentication failures
- Added proper WWW-Authenticate header
- This ensures proper handling of authentication errors in the frontend

### 3. React Router Configuration (frontend/src/App.js)

```javascript
// Before
import { BrowserRouter as Router, Routes, Route, Navigate, createBrowserRouter, RouterProvider } from 'react-router-dom';
// ...
<Router future={{ v7_relativeSplatPath: true }}>

// After
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
// ...
<Router>
```

**Changes**:
- Removed unused imports (`createBrowserRouter`, `RouterProvider`)
- Removed future flag that was causing the warning
- Simplified router configuration

## Testing

A test script has been created at `scripts/test-api-auth.sh` to verify:
1. Health endpoint accessibility
2. CORS headers configuration
3. Authentication (login)
4. Authorized access to Gryzzly endpoints

Run the test script:
```bash
./scripts/test-api-auth.sh
```

## Required Environment Variables

Ensure these are set in your `.env` file:
```env
# CORS Configuration
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
```

## Important Notes

1. **Authentication Required**: Most Gryzzly endpoints require authentication. Ensure users are logged in before accessing these endpoints.

2. **Admin Privileges**: Some endpoints (sync operations) require superuser privileges. Regular users will get 400 errors on these endpoints.

3. **Token Management**: The frontend correctly stores and sends authentication tokens via the Authorization header.

4. **CORS in Production**: Remember to update BACKEND_CORS_ORIGINS for production domains.

## Verification Steps

1. **Restart Services**:
   ```bash
   docker compose restart backend frontend
   ```

2. **Check Backend Logs**:
   ```bash
   docker compose logs backend | grep "CORS Origins"
   ```
   You should see: `CORS Origins configured: ['http://localhost:3000', 'http://localhost:8080']`

3. **Test Login**:
   - Navigate to http://localhost:3000
   - Login with admin@plancharge.com / admin123
   - Navigate to Gryzzly section
   - All tabs should load without 403 errors

4. **Check Browser Console**:
   - No CORS errors
   - No React Router warnings
   - No 403 Forbidden errors (may see 401 if not logged in)

## Troubleshooting

If issues persist:

1. **Clear Browser Cache**: Force refresh with Ctrl+Shift+R
2. **Check Token**: In browser console, run `localStorage.getItem('auth_token')` to verify token exists
3. **Verify CORS**: Check network tab for Access-Control-Allow-Origin header
4. **Docker Logs**: `docker compose logs -f backend` for real-time logs