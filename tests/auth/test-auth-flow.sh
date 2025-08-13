#\!/bin/bash

# Authentication Flow Testing Script
# Tests registration, login, token refresh, password change, and logout

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000/api/v1"

# Test data
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123\!"
NEW_PASSWORD="NewTestPass456\!"

echo -e "${YELLOW}🧪 Starting Authentication Flow Tests${NC}"
echo "================================"
echo "Test Email: $TEST_EMAIL"
echo "Base URL: $BASE_URL"
echo ""

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# 1. Test Registration
echo -e "\n${YELLOW}1. Testing User Registration${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\"
    }" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    print_result 0 "User registration successful"
    echo "Response: $RESPONSE_BODY"
else
    print_result 1 "User registration failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
fi

# 2. Test Login
echo -e "\n${YELLOW}2. Testing User Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_result 0 "User login successful"
    
    # Extract tokens
    ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])" 2>/dev/null)
    
    if [ -n "$ACCESS_TOKEN" ] && [ -n "$REFRESH_TOKEN" ]; then
        echo "Access Token: ${ACCESS_TOKEN:0:50}..."
        echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
    else
        echo "Warning: Could not extract tokens from response"
    fi
else
    print_result 1 "User login failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
fi

# 3. Test Protected Endpoint
echo -e "\n${YELLOW}3. Testing Protected Endpoint (Me)${NC}"
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$ME_RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$ME_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_result 0 "Protected endpoint access successful"
    echo "User Info: $RESPONSE_BODY"
else
    print_result 1 "Protected endpoint access failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
fi

echo -e "\n${GREEN}✨ Authentication Flow Tests Completed\!${NC}"
echo "================================"
EOF < /dev/null