#!/bin/bash

# ============================================================================
# Azure AD SSO Cleanup Script for Plan de Charge
# ============================================================================
# This script removes Azure AD app registration and cleans up local config
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# ============================================================================
# STEP 1: Check Azure CLI
# ============================================================================
print_message $BLUE "\n=== Azure AD SSO Cleanup Script ==="

if ! command -v az >/dev/null 2>&1; then
    print_message $RED "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in
if ! az account show >/dev/null 2>&1; then
    print_message $YELLOW "Please login to Azure..."
    az login
fi

CURRENT_USER=$(az account show --query user.name -o tsv)
print_message $GREEN "✓ Logged in as: $CURRENT_USER"

# ============================================================================
# STEP 2: Find and Delete App Registration
# ============================================================================
print_message $BLUE "\n=== Step 1: Finding App Registrations ==="

# Try to load from config file first
if [ -f "azure-sso-config.json" ]; then
    CLIENT_ID=$(jq -r '.clientId' azure-sso-config.json 2>/dev/null || echo "")
    APP_NAME=$(jq -r '.appName' azure-sso-config.json 2>/dev/null || echo "Plan de Charge SSO")
else
    APP_NAME="Plan de Charge SSO"
fi

# Find all matching apps
APPS=$(az ad app list --display-name "$APP_NAME" --query "[].{name:displayName, id:appId}" -o json)
APP_COUNT=$(echo $APPS | jq '. | length')

if [ "$APP_COUNT" -eq "0" ]; then
    print_message $YELLOW "No app registrations found with name: $APP_NAME"
else
    print_message $YELLOW "Found $APP_COUNT app registration(s):"
    echo $APPS | jq -r '.[] | "  • \(.name) (ID: \(.id))"'
    
    echo ""
    read -p "Do you want to delete ALL these app registrations? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo $APPS | jq -r '.[].id' | while read APP_ID; do
            print_message $YELLOW "Deleting app: $APP_ID"
            az ad app delete --id "$APP_ID"
            print_message $GREEN "✓ Deleted app: $APP_ID"
            
            # Also try to delete service principal if exists
            SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv 2>/dev/null || echo "")
            if [ ! -z "$SP_ID" ]; then
                print_message $YELLOW "Deleting service principal: $SP_ID"
                az ad sp delete --id "$SP_ID" 2>/dev/null || true
                print_message $GREEN "✓ Deleted service principal"
            fi
        done
    else
        print_message $YELLOW "Skipping app deletion"
    fi
fi

# ============================================================================
# STEP 3: Clean Local Configuration
# ============================================================================
print_message $BLUE "\n=== Step 2: Cleaning Local Configuration ==="

echo ""
read -p "Do you want to remove Azure AD configuration from .env files? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Clean backend .env
    if [ -f "backend/.env" ]; then
        print_message $YELLOW "Cleaning backend/.env..."
        sed -i.bak '/^AZURE_AD_/d' backend/.env
        sed -i.bak '/^# Azure AD Configuration/d' backend/.env
        print_message $GREEN "✓ Cleaned backend/.env"
    fi
    
    # Clean frontend .env files
    for ENV_FILE in frontend/.env frontend/.env.local; do
        if [ -f "$ENV_FILE" ]; then
            print_message $YELLOW "Cleaning $ENV_FILE..."
            sed -i.bak '/^VITE_AZURE_AD_/d' $ENV_FILE
            sed -i.bak '/^# Azure AD Configuration/d' $ENV_FILE
            print_message $GREEN "✓ Cleaned $ENV_FILE"
        fi
    done
    
    # Remove config file
    if [ -f "azure-sso-config.json" ]; then
        rm azure-sso-config.json
        print_message $GREEN "✓ Removed azure-sso-config.json"
    fi
fi

# ============================================================================
# STEP 4: Database Cleanup
# ============================================================================
print_message $BLUE "\n=== Step 3: Database Cleanup (Optional) ==="

echo ""
echo "To clean up database (remove SSO users and tokens), run these commands:"
echo ""
print_message $YELLOW "1. Connect to your database:"
echo "   docker-compose exec db psql -U postgres -d plancharge"
echo ""
print_message $YELLOW "2. Delete SSO-created users (keep local users):"
echo "   DELETE FROM users WHERE azure_id IS NOT NULL AND password_hash IS NULL;"
echo ""
print_message $YELLOW "3. Delete all refresh tokens:"
echo "   DELETE FROM refresh_tokens;"
echo ""
print_message $YELLOW "4. Exit psql:"
echo "   \\q"

# ============================================================================
# STEP 5: Summary
# ============================================================================
print_message $BLUE "\n=== Cleanup Complete ==="
print_message $GREEN "\n✅ Azure AD SSO configuration has been cleaned up!"

echo ""
print_message $YELLOW "Next Steps:"
echo "1. If you want to reconfigure SSO, run: ./setup-azure-sso.sh"
echo "2. Restart your application: docker-compose restart"
echo "3. Users can now use local authentication (if enabled)"

print_message $GREEN "\n✓ Cleanup completed successfully!"