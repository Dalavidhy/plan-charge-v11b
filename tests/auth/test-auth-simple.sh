#\!/bin/bash

# Simple Authentication Test Script

BASE_URL="http://localhost:8000/api/v1"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPass123\!"

echo "🧪 Starting Authentication Flow Tests"
echo "================================"
echo "Test Email: $TEST_EMAIL"
echo ""

# Test Registration
echo "1. Testing User Registration..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'"$TEST_EMAIL"'",
        "password": "'"$TEST_PASSWORD"'",
        "first_name": "Test",
        "last_name": "User"
    }')

BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
CODE=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [ "$CODE" = "201" ] || [ "$CODE" = "200" ]; then
    echo "✅ Registration successful (HTTP $CODE)"
    echo "Response: $BODY"
else
    echo "❌ Registration failed (HTTP $CODE)"
    echo "Response: $BODY"
    exit 1
fi

# Test Login
echo ""
echo "2. Testing User Login..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'"$TEST_EMAIL"'",
        "password": "'"$TEST_PASSWORD"'"
    }')

BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
CODE=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [ "$CODE" = "200" ]; then
    echo "✅ Login successful (HTTP $CODE)"
    
    # Extract tokens using python
    ACCESS_TOKEN=$(echo "$BODY" | python3 -c "import sys, json; data = json.loads(sys.stdin.read()); print(data.get('access_token', ''))" 2>/dev/null || echo "")
    REFRESH_TOKEN=$(echo "$BODY" | python3 -c "import sys, json; data = json.loads(sys.stdin.read()); print(data.get('refresh_token', ''))" 2>/dev/null || echo "")
    
    if [ -n "$ACCESS_TOKEN" ]; then
        echo "Access Token received: ${ACCESS_TOKEN:0:20}..."
    fi
else
    echo "❌ Login failed (HTTP $CODE)"
    echo "Response: $BODY"
    exit 1
fi

# Test Protected Endpoint
echo ""
echo "3. Testing Protected Endpoint (Me)..."
RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
CODE=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [ "$CODE" = "200" ]; then
    echo "✅ Protected endpoint access successful (HTTP $CODE)"
    echo "User data: $BODY"
else
    echo "❌ Protected endpoint access failed (HTTP $CODE)"
    echo "Response: $BODY"
fi

echo ""
echo "✨ Authentication Tests Completed\!"
echo "================================"
