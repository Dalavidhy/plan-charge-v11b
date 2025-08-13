#!/bin/bash

# Script to create admin user account

echo "Creating admin user account..."

# Create admin account
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@plancharge.fr",
    "password": "Admin123!",
    "first_name": "Admin",
    "last_name": "User"
  }')

echo "Response: $RESPONSE"

# Try to login
echo ""
echo "Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@plancharge.fr",
    "password": "Admin123!"
  }')

# Check if login successful
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful!"
    echo ""
    echo "==================================="
    echo "📧 Email: admin@plancharge.fr"
    echo "🔑 Password: Admin123!"
    echo "==================================="
else
    echo "Login response: $LOGIN_RESPONSE"
fi

# Also create a demo user
echo ""
echo "Creating demo user account..."
DEMO_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@plancharge.fr",
    "password": "Demo123!",
    "first_name": "Demo",
    "last_name": "User"
  }')

echo "Demo user response: $DEMO_RESPONSE"

# Test demo login
DEMO_LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@plancharge.fr",
    "password": "Demo123!"
  }')

if echo "$DEMO_LOGIN" | grep -q "access_token"; then
    echo "✅ Demo user login successful!"
    echo ""
    echo "==================================="
    echo "📧 Demo Email: demo@plancharge.fr"
    echo "🔑 Demo Password: Demo123!"
    echo "==================================="
fi

echo ""
echo "🎉 User accounts ready!"
echo ""
echo "Available accounts:"
echo "1. Admin: admin@plancharge.fr / Admin123!"
echo "2. Demo: demo@plancharge.fr / Demo123!"
echo ""
echo "Access the application at: http://localhost:3000"