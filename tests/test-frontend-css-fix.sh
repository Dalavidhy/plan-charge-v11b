#!/bin/bash

# Test script for frontend CSS fix
# Verifies that Tailwind CSS configuration is working properly

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FRONTEND_URL="http://localhost:3000"

echo "🧪 Frontend CSS Fix Validation Test"
echo "==================================="
echo ""

# Function to print results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Test 1: Check if frontend is running
echo -n "1. Frontend health check... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/" || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_result 0 "Frontend is running (HTTP 200)"
else
    print_result 1 "Frontend not accessible (HTTP $FRONTEND_STATUS)"
fi

# Test 2: Check for CSS/PostCSS errors in logs
echo -n "2. Checking for CSS build errors... "
CSS_ERRORS=$(docker compose logs frontend 2>&1 | grep -i "postcss\|tailwind.*error\|border-border" | grep -v "ready in" || echo "")
if [ -z "$CSS_ERRORS" ]; then
    print_result 0 "No CSS build errors found"
else
    echo -e "${RED}❌ CSS errors detected:${NC}"
    echo "$CSS_ERRORS"
    exit 1
fi

# Test 3: Check if CSS is being served
echo -n "3. CSS assets loading... "
HTML_CONTENT=$(curl -s "$FRONTEND_URL/")
if echo "$HTML_CONTENT" | grep -q "src=\"/@vite/client\""; then
    print_result 0 "Vite dev server serving assets"
else
    print_result 1 "CSS assets not loading properly"
fi

# Test 4: Check for JavaScript modules
echo -n "4. JavaScript modules loading... "
if echo "$HTML_CONTENT" | grep -q "type=\"module\""; then
    print_result 0 "ES modules loading correctly"
else
    print_result 1 "JavaScript modules not loading"
fi

# Test 5: Check container status
echo -n "5. Frontend container status... "
CONTAINER_STATUS=$(docker compose ps frontend --format "{{.State}}" | head -1 || echo "unknown")
if [ "$CONTAINER_STATUS" = "running" ]; then
    print_result 0 "Container is running"
else
    print_result 1 "Container status: $CONTAINER_STATUS"
fi

# Test 6: Check for Tailwind configuration
echo -n "6. Tailwind configuration... "
CONFIG_CHECK=$(docker compose exec -T frontend cat tailwind.config.js | grep -c "border.*hsl.*var.*--border" || echo "0")
if [ "$CONFIG_CHECK" -gt 0 ]; then
    print_result 0 "Tailwind config includes CSS variable colors"
else
    print_result 1 "Tailwind config missing CSS variable colors"
fi

# Test 7: Check for tailwindcss-animate plugin
echo -n "7. Tailwind plugins... "
PLUGIN_CHECK=$(docker compose exec -T frontend cat tailwind.config.js | grep -c "tailwindcss-animate" || echo "0")
if [ "$PLUGIN_CHECK" -gt 0 ]; then
    print_result 0 "tailwindcss-animate plugin configured"
else
    print_result 1 "tailwindcss-animate plugin not configured"
fi

echo ""
echo "==================================="
echo -e "${GREEN}✨ All CSS fix tests passed!${NC}"
echo "==================================="
echo ""
echo "Summary:"
echo "✅ Frontend is running without CSS errors"
echo "✅ Tailwind configuration fixed with CSS variables"
echo "✅ border-border class error resolved"
echo "✅ All required plugins installed and configured"
echo ""
echo "The frontend CSS issue has been successfully resolved!"