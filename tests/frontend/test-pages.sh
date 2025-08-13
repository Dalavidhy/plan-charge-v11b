#!/bin/bash

# Test frontend page accessibility
# Usage: ./test-pages.sh

set -e

# Configuration
FRONTEND_URL=${FRONTEND_URL:-http://localhost:5173}
API_URL=${API_URL:-http://localhost:8000/api/v1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🌐 Testing Frontend Pages${NC}"
echo "================================"

# Function to test page
test_page() {
    local path=$1
    local expected_status=$2
    local description=$3
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo "URL: $FRONTEND_URL$path"
    
    # Get response with headers
    RESPONSE=$(curl -s -I -X GET "$FRONTEND_URL$path" 2>/dev/null | head -n 1)
    
    # Extract status code
    STATUS=$(echo "$RESPONSE" | grep -oE '[0-9]{3}' | head -n 1)
    
    if [ -z "$STATUS" ]; then
        # Try alternative method
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL$path")
    fi
    
    if [ "$STATUS" = "$expected_status" ]; then
        echo -e "✅ ${GREEN}$description: HTTP $STATUS${NC}"
        
        # Check page content for key elements
        CONTENT=$(curl -s "$FRONTEND_URL$path")
        
        # Check if it's an HTML page
        if echo "$CONTENT" | grep -q "<html"; then
            echo -e "   ✓ HTML content detected"
        fi
        
        # Check for React root
        if echo "$CONTENT" | grep -q "id=\"root\""; then
            echo -e "   ✓ React root element found"
        fi
        
        # Check for app scripts
        if echo "$CONTENT" | grep -q "src=\"/assets"; then
            echo -e "   ✓ Application scripts loaded"
        fi
        
        return 0
    else
        echo -e "❌ ${RED}$description: Expected HTTP $expected_status, got $STATUS${NC}"
        return 1
    fi
}

# Function to test static assets
test_asset() {
    local path=$1
    local description=$2
    
    echo -e "\n${YELLOW}Testing asset: $description${NC}"
    
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL$path")
    
    if [ "$STATUS" = "200" ] || [ "$STATUS" = "304" ]; then
        echo -e "✅ ${GREEN}$description: HTTP $STATUS${NC}"
        return 0
    else
        echo -e "⚠️  ${YELLOW}$description: HTTP $STATUS (might not be built yet)${NC}"
        return 0  # Don't fail on missing assets in dev mode
    fi
}

# Function to test API proxy
test_api_proxy() {
    echo -e "\n${YELLOW}Testing API proxy through frontend...${NC}"
    
    # Test health endpoint through proxy
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/api/v1/health")
    
    if [ "$STATUS" = "200" ]; then
        echo -e "✅ ${GREEN}API proxy is working: HTTP $STATUS${NC}"
        
        # Get actual response
        RESPONSE=$(curl -s "$FRONTEND_URL/api/v1/health")
        echo "API Response: $RESPONSE"
        return 0
    else
        echo -e "❌ ${RED}API proxy failed: HTTP $STATUS${NC}"
        echo "Direct API test:"
        curl -s "$API_URL/health"
        return 1
    fi
}

# 1. Test frontend is running
echo -e "\n${BLUE}1. Testing Frontend Server${NC}"
echo "================================"

# Check if frontend is responding
if curl -f -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "✅ ${GREEN}Frontend server is running${NC}"
else
    echo -e "❌ ${RED}Frontend server is not responding${NC}"
    echo "Checking Docker container..."
    docker compose ps frontend
    echo -e "\nContainer logs:"
    docker compose logs --tail=20 frontend
    exit 1
fi

# 2. Test public pages
echo -e "\n${BLUE}2. Testing Public Pages${NC}"
echo "================================"

test_page "/" "200" "Home page"
test_page "/login" "200" "Login page"
test_page "/register" "200" "Register page"
test_page "/forgot-password" "200" "Forgot password page"

# 3. Test protected pages (should redirect or show login)
echo -e "\n${BLUE}3. Testing Protected Pages${NC}"
echo "================================"

# These should either return 200 (if SPA handles routing) or redirect
test_page "/dashboard" "200" "Dashboard (protected)"
test_page "/projects" "200" "Projects (protected)"
test_page "/allocations" "200" "Allocations (protected)"
test_page "/people" "200" "People (protected)"
test_page "/teams" "200" "Teams (protected)"
test_page "/calendar" "200" "Calendar (protected)"
test_page "/reports" "200" "Reports (protected)"
test_page "/settings" "200" "Settings (protected)"

# 4. Test static assets
echo -e "\n${BLUE}4. Testing Static Assets${NC}"
echo "================================"

# Note: In dev mode, these might be served differently
test_asset "/favicon.ico" "Favicon"

# 5. Test API proxy
echo -e "\n${BLUE}5. Testing API Proxy${NC}"
echo "================================"

test_api_proxy

# 6. Test 404 handling
echo -e "\n${BLUE}6. Testing 404 Handling${NC}"
echo "================================"

test_page "/this-page-does-not-exist" "200" "404 page (SPA handles routing)"

# 7. Performance check
echo -e "\n${BLUE}7. Performance Check${NC}"
echo "================================"

echo -e "${YELLOW}Testing page load time...${NC}"
TIME=$(curl -o /dev/null -s -w '%{time_total}' "$FRONTEND_URL")
echo -e "Page load time: ${TIME}s"

if (( $(echo "$TIME < 2" | bc -l) )); then
    echo -e "✅ ${GREEN}Page loads within acceptable time (<2s)${NC}"
else
    echo -e "⚠️  ${YELLOW}Page load time is slow (>2s)${NC}"
fi

# 8. Check for common issues
echo -e "\n${BLUE}8. Checking for Common Issues${NC}"
echo "================================"

# Check for console errors (would need Playwright for real testing)
echo -e "${YELLOW}Checking page structure...${NC}"

HOMEPAGE=$(curl -s "$FRONTEND_URL")

# Check for common error indicators
if echo "$HOMEPAGE" | grep -q "Cannot GET"; then
    echo -e "⚠️  ${YELLOW}Possible routing issue detected${NC}"
fi

if echo "$HOMEPAGE" | grep -q "ECONNREFUSED"; then
    echo -e "❌ ${RED}Connection refused error detected${NC}"
fi

if echo "$HOMEPAGE" | grep -q "Error"; then
    echo -e "⚠️  ${YELLOW}Error text found in page (might be normal)${NC}"
fi

# Check meta tags
if echo "$HOMEPAGE" | grep -q "<title>"; then
    TITLE=$(echo "$HOMEPAGE" | grep -oP '(?<=<title>)[^<]+')
    echo -e "✅ Page title: $TITLE"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "================================"
echo -e "✅ ${GREEN}Frontend pages are accessible!${NC}"
echo -e "Frontend URL: $FRONTEND_URL"
echo -e "API Proxy: $FRONTEND_URL/api"

exit 0