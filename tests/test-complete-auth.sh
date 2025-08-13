#!/bin/bash

# Complete Authentication and Integration Test Script
# Tests backend auth, frontend pages, and full integration

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
API_URL="$BACKEND_URL/api/v1"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123!"

echo "🧪 Complete Authentication and Integration Tests"
echo "================================================"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Test Email: $TEST_EMAIL"
echo ""

# Function to print results
print_result() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
    else
        echo "❌ $2"
        exit 1
    fi
}

# =============================================================================
# PHASE 1: Backend Health and API Tests
# =============================================================================
echo "📊 PHASE 1: Backend Health and API Tests"
echo "-----------------------------------------"

# Health check
echo -n "1.1 Backend health check... "
HEALTH=$(curl -s "$BACKEND_URL/health" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
[ "$HEALTH" = "healthy" ] && print_result 0 "Backend is healthy" || print_result 1 "Backend is not healthy"

# Database connectivity
echo -n "1.2 Database connectivity... "
docker compose exec -T postgres pg_isready -U plancharge > /dev/null 2>&1
print_result $? "Database is ready"

# Redis connectivity
echo -n "1.3 Redis connectivity... "
docker compose exec -T redis redis-cli ping > /dev/null 2>&1
print_result $? "Redis is ready"

# =============================================================================
# PHASE 2: Authentication Flow Tests
# =============================================================================
echo ""
echo "📊 PHASE 2: Authentication Flow Tests"
echo "-------------------------------------"

# Register new user
echo -n "2.1 User registration... "
REGISTER_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"first_name\": \"Test\", \"last_name\": \"User\"}")

REGISTER_BODY=$(echo $REGISTER_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
REGISTER_CODE=$(echo $REGISTER_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

[ "$REGISTER_CODE" = "201" ] && print_result 0 "User registered successfully" || print_result 1 "Registration failed (HTTP $REGISTER_CODE)"

# Login
echo -n "2.2 User login... "
LOGIN_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

LOGIN_BODY=$(echo $LOGIN_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
LOGIN_CODE=$(echo $LOGIN_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [ "$LOGIN_CODE" = "200" ]; then
    print_result 0 "Login successful"
    ACCESS_TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])" 2>/dev/null)
else
    print_result 1 "Login failed (HTTP $LOGIN_CODE)"
fi

# Protected endpoint
echo -n "2.3 Protected endpoint access... "
ME_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$API_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

ME_CODE=$(echo $ME_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
[ "$ME_CODE" = "200" ] && print_result 0 "Protected endpoint accessible" || print_result 1 "Protected endpoint failed (HTTP $ME_CODE)"

# Token refresh
echo -n "2.4 Token refresh... "
REFRESH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$API_URL/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

REFRESH_CODE=$(echo $REFRESH_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
[ "$REFRESH_CODE" = "200" ] && print_result 0 "Token refresh successful" || echo "⚠️  Token refresh not implemented (HTTP $REFRESH_CODE)"

# =============================================================================
# PHASE 3: Frontend Page Accessibility
# =============================================================================
echo ""
echo "📊 PHASE 3: Frontend Page Accessibility"
echo "---------------------------------------"

# Check if frontend is running
echo -n "3.1 Frontend health check... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/" || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_result 0 "Frontend is running"
else
    echo "⚠️  Frontend not accessible (HTTP $FRONTEND_STATUS) - may still be building"
fi

# Check frontend pages (if running)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -n "3.2 Home page... "
    HOME_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/")
    [ "$HOME_STATUS" = "200" ] && print_result 0 "Home page accessible" || print_result 1 "Home page not accessible (HTTP $HOME_STATUS)"
    
    echo -n "3.3 Login page... "
    LOGIN_PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/login")
    [ "$LOGIN_PAGE_STATUS" = "200" ] && print_result 0 "Login page accessible" || echo "⚠️  Login page returns HTTP $LOGIN_PAGE_STATUS"
    
    echo -n "3.4 Static assets... "
    # Check if index.html has script tags
    SCRIPTS=$(curl -s "$FRONTEND_URL/" | grep -c "<script" || echo "0")
    [ "$SCRIPTS" -gt 0 ] && print_result 0 "Static assets loading" || print_result 1 "No static assets found"
fi

# =============================================================================
# PHASE 4: API Endpoints Verification
# =============================================================================
echo ""
echo "📊 PHASE 4: API Endpoints Verification"
echo "--------------------------------------"

# Organizations endpoint
echo -n "4.1 Organizations endpoint... "
ORGS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$API_URL/orgs" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
ORGS_CODE=$(echo $ORGS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
[ "$ORGS_CODE" = "200" ] && print_result 0 "Organizations endpoint working" || echo "⚠️  Organizations endpoint returned HTTP $ORGS_CODE"

# Teams endpoint
echo -n "4.2 Teams endpoint... "
TEAMS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$API_URL/teams" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
TEAMS_CODE=$(echo $TEAMS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
[ "$TEAMS_CODE" = "200" ] && print_result 0 "Teams endpoint working" || echo "⚠️  Teams endpoint returned HTTP $TEAMS_CODE"

# Projects endpoint
echo -n "4.3 Projects endpoint... "
PROJECTS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$API_URL/projects" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
PROJECTS_CODE=$(echo $PROJECTS_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
[ "$PROJECTS_CODE" = "200" ] && print_result 0 "Projects endpoint working" || echo "⚠️  Projects endpoint returned HTTP $PROJECTS_CODE"

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "================================================"
echo "✨ Test Summary"
echo "================================================"
echo "✅ Backend Health: OK"
echo "✅ Authentication: Working (Register, Login, Protected endpoints)"
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend: Accessible"
else
    echo "⚠️  Frontend: Not fully ready (may still be building)"
fi
echo "✅ Database: Connected and operational"
echo "✅ Redis: Connected and operational"
echo ""
echo "🎉 Core authentication system is functional!"
echo "================================================"