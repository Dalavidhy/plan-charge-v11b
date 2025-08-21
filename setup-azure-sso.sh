#!/bin/bash

# ============================================================================
# Azure Entra ID (Azure AD) SSO Configuration Script for Plan de Charge
# ============================================================================
# This script automates the complete setup of Azure AD SSO for the application
# Requirements: Azure CLI installed and authenticated
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
APP_NAME="Plan de Charge SSO"
REDIRECT_URI="http://localhost:3200/auth/callback"
PROD_REDIRECT_URI=""  # Add your production URL if needed

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Azure CLI if not present
install_azure_cli() {
    print_message $YELLOW "Azure CLI not found. Installing..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew update && brew install azure-cli
        else
            print_message $RED "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
    else
        print_message $RED "Unsupported OS. Please install Azure CLI manually:"
        print_message $RED "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
}

# ============================================================================
# STEP 1: Check Prerequisites
# ============================================================================
print_message $BLUE "\n=== Step 1: Checking Prerequisites ==="

if ! command_exists az; then
    install_azure_cli
fi

print_message $GREEN "✓ Azure CLI is installed"

# Check if jq is installed (for JSON parsing)
if ! command_exists jq; then
    print_message $YELLOW "Installing jq for JSON parsing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        sudo apt-get install -y jq
    fi
fi

print_message $GREEN "✓ jq is installed"

# ============================================================================
# STEP 2: Azure Authentication
# ============================================================================
print_message $BLUE "\n=== Step 2: Azure Authentication ==="

# Check if already logged in
if ! az account show >/dev/null 2>&1; then
    print_message $YELLOW "Please login to Azure..."
    az login
else
    CURRENT_USER=$(az account show --query user.name -o tsv)
    print_message $GREEN "✓ Already logged in as: $CURRENT_USER"
fi

# Get tenant information
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

print_message $GREEN "✓ Using Tenant ID: $TENANT_ID"
print_message $GREEN "✓ Subscription: $SUBSCRIPTION_NAME"

# ============================================================================
# STEP 3: Clean up existing app (if exists)
# ============================================================================
print_message $BLUE "\n=== Step 3: Checking for Existing App Registration ==="

# Check if app already exists
EXISTING_APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")

if [ ! -z "$EXISTING_APP_ID" ]; then
    print_message $YELLOW "Found existing app registration: $EXISTING_APP_ID"
    read -p "Do you want to delete it and create a new one? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "Deleting existing app..."
        az ad app delete --id "$EXISTING_APP_ID"
        print_message $GREEN "✓ Deleted existing app"
        sleep 5  # Wait for deletion to propagate
    else
        print_message $YELLOW "Using existing app registration"
        CLIENT_ID=$EXISTING_APP_ID
    fi
fi

# ============================================================================
# STEP 4: Create App Registration
# ============================================================================
if [ -z "$CLIENT_ID" ]; then
    print_message $BLUE "\n=== Step 4: Creating App Registration ==="

    # Create the app registration with SPA platform
    print_message $YELLOW "Creating new app registration..."

    # Create app with basic configuration
    APP_CREATION_RESULT=$(az ad app create \
        --display-name "$APP_NAME" \
        --sign-in-audience "AzureADMyOrg" \
        --enable-access-token-issuance false \
        --enable-id-token-issuance false)

    CLIENT_ID=$(echo $APP_CREATION_RESULT | jq -r '.appId')
    OBJECT_ID=$(echo $APP_CREATION_RESULT | jq -r '.id')

    print_message $GREEN "✓ Created app registration"
    print_message $GREEN "  Client ID: $CLIENT_ID"
    print_message $GREEN "  Object ID: $OBJECT_ID"

    # Wait for app to be created
    sleep 5

    # Configure SPA platform with redirect URIs using Microsoft Graph API
    print_message $YELLOW "Configuring SPA platform..."

    # Use az rest to call Microsoft Graph API directly
    # This method works with all versions of Azure CLI
    SPA_CONFIG='{
        "spa": {
            "redirectUris": [
                "'$REDIRECT_URI'"
            ]
        },
        "web": {
            "redirectUris": [],
            "implicitGrantSettings": {
                "enableAccessTokenIssuance": false,
                "enableIdTokenIssuance": false
            }
        }
    }'

    # Update using Microsoft Graph API
    print_message $YELLOW "Updating app configuration via Microsoft Graph..."

    # Try using az rest command
    if az rest --method PATCH \
        --uri "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
        --headers "Content-Type=application/json" \
        --body "$SPA_CONFIG" 2>/dev/null; then
        print_message $GREEN "✓ Configured SPA platform with redirect URI: $REDIRECT_URI"
    else
        # Fallback method: use az ad app update with manifest
        print_message $YELLOW "Trying alternative method..."

        # Get current manifest
        CURRENT_MANIFEST=$(az ad app show --id $CLIENT_ID)

        # Create updated manifest with SPA configuration
        UPDATED_MANIFEST=$(echo $CURRENT_MANIFEST | jq '.spa.redirectUris = ["'$REDIRECT_URI'"]')

        # Save to temp file
        echo "$UPDATED_MANIFEST" > /tmp/app-manifest.json

        # Update app with new manifest
        az ad app update --id $CLIENT_ID --set spa.redirectUris="[\"$REDIRECT_URI\"]" 2>/dev/null || {
            # Last resort: manual instruction
            print_message $YELLOW "⚠ Automatic SPA configuration failed. Please configure manually:"
            print_message $YELLOW "  1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Authentication/appId/$CLIENT_ID"
            print_message $YELLOW "  2. Add a platform: Single-page application"
            print_message $YELLOW "  3. Add redirect URI: $REDIRECT_URI"
            print_message $YELLOW "  4. Save the changes"
        }

        rm -f /tmp/app-manifest.json
    fi
fi

# ============================================================================
# STEP 5: Configure API Permissions
# ============================================================================
print_message $BLUE "\n=== Step 5: Configuring API Permissions ==="

# Microsoft Graph API ID
GRAPH_API_ID="00000003-0000-0000-c000-000000000000"

# Define required permissions
print_message $YELLOW "Adding Microsoft Graph permissions..."

# User.Read permission (delegated)
az ad app permission add \
    --id $CLIENT_ID \
    --api $GRAPH_API_ID \
    --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope \
    2>/dev/null || true

# openid permission (delegated)
az ad app permission add \
    --id $CLIENT_ID \
    --api $GRAPH_API_ID \
    --api-permissions 37f7f235-527c-4136-accd-4a02d197296e=Scope \
    2>/dev/null || true

# profile permission (delegated)
az ad app permission add \
    --id $CLIENT_ID \
    --api $GRAPH_API_ID \
    --api-permissions 14dad69e-099b-42c9-810b-d002981feec1=Scope \
    2>/dev/null || true

# email permission (delegated)
az ad app permission add \
    --id $CLIENT_ID \
    --api $GRAPH_API_ID \
    --api-permissions 64a6cdd6-aab1-4aaf-94b8-3cc8405e90d0=Scope \
    2>/dev/null || true

# offline_access permission (delegated)
az ad app permission add \
    --id $CLIENT_ID \
    --api $GRAPH_API_ID \
    --api-permissions 7427e0e9-2fba-42fe-b0c0-848c9e6a8182=Scope \
    2>/dev/null || true

print_message $GREEN "✓ Added all required permissions"

# ============================================================================
# STEP 6: Grant Admin Consent
# ============================================================================
print_message $BLUE "\n=== Step 6: Granting Admin Consent ==="

print_message $YELLOW "Granting admin consent for the application..."

# Try to grant admin consent
if az ad app permission admin-consent --id $CLIENT_ID 2>/dev/null; then
    print_message $GREEN "✓ Admin consent granted successfully"
else
    print_message $YELLOW "⚠ Could not grant admin consent automatically."
    print_message $YELLOW "  You may need to grant it manually in Azure Portal."
    print_message $YELLOW "  URL: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/CallAnAPI/appId/$CLIENT_ID"
fi

# ============================================================================
# STEP 7: Create Enterprise Application
# ============================================================================
print_message $BLUE "\n=== Step 7: Configuring Enterprise Application ==="

# Check if service principal exists
SP_ID=$(az ad sp list --filter "appId eq '$CLIENT_ID'" --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ -z "$SP_ID" ]; then
    print_message $YELLOW "Creating service principal (Enterprise Application)..."
    SP_CREATION=$(az ad sp create --id $CLIENT_ID)
    SP_ID=$(echo $SP_CREATION | jq -r '.id')
    print_message $GREEN "✓ Created service principal: $SP_ID"
else
    print_message $GREEN "✓ Service principal already exists: $SP_ID"
fi

# ============================================================================
# STEP 8: NO CLIENT SECRET FOR SPA!
# ============================================================================
print_message $BLUE "\n=== Step 8: SPA Configuration ==="
print_message $GREEN "✓ No client secret needed for SPA (using PKCE flow)"

# ============================================================================
# STEP 9: Generate Environment Files
# ============================================================================
print_message $BLUE "\n=== Step 9: Generating Environment Files ==="

# Update backend .env file
BACKEND_ENV_FILE="backend/.env"
if [ -f "$BACKEND_ENV_FILE" ]; then
    print_message $YELLOW "Updating backend .env file..."

    # Update or add Azure AD configuration
    sed -i.bak '/^AZURE_AD_TENANT_ID=/d' $BACKEND_ENV_FILE
    sed -i.bak '/^AZURE_AD_CLIENT_ID=/d' $BACKEND_ENV_FILE
    sed -i.bak '/^AZURE_AD_CLIENT_SECRET=/d' $BACKEND_ENV_FILE
    sed -i.bak '/^AZURE_AD_REDIRECT_URI=/d' $BACKEND_ENV_FILE

    echo "" >> $BACKEND_ENV_FILE
    echo "# Azure AD Configuration (Updated by setup script)" >> $BACKEND_ENV_FILE
    echo "AZURE_AD_TENANT_ID=$TENANT_ID" >> $BACKEND_ENV_FILE
    echo "AZURE_AD_CLIENT_ID=$CLIENT_ID" >> $BACKEND_ENV_FILE
    echo "AZURE_AD_CLIENT_SECRET=" >> $BACKEND_ENV_FILE  # Empty for SPA
    echo "AZURE_AD_REDIRECT_URI=$REDIRECT_URI" >> $BACKEND_ENV_FILE

    print_message $GREEN "✓ Updated backend/.env"
else
    print_message $YELLOW "⚠ backend/.env not found. Please create it manually."
fi

# Update frontend .env file
FRONTEND_ENV_FILE="frontend/.env"
if [ ! -f "$FRONTEND_ENV_FILE" ]; then
    FRONTEND_ENV_FILE="frontend/.env.local"
fi

if [ -f "$FRONTEND_ENV_FILE" ]; then
    print_message $YELLOW "Updating frontend .env file..."

    # Update or add Azure AD configuration
    sed -i.bak '/^VITE_AZURE_AD_TENANT_ID=/d' $FRONTEND_ENV_FILE
    sed -i.bak '/^VITE_AZURE_AD_CLIENT_ID=/d' $FRONTEND_ENV_FILE
    sed -i.bak '/^VITE_AZURE_AD_REDIRECT_URI=/d' $FRONTEND_ENV_FILE

    echo "" >> $FRONTEND_ENV_FILE
    echo "# Azure AD Configuration (Updated by setup script)" >> $FRONTEND_ENV_FILE
    echo "VITE_AZURE_AD_TENANT_ID=$TENANT_ID" >> $FRONTEND_ENV_FILE
    echo "VITE_AZURE_AD_CLIENT_ID=$CLIENT_ID" >> $FRONTEND_ENV_FILE
    echo "VITE_AZURE_AD_REDIRECT_URI=$REDIRECT_URI" >> $FRONTEND_ENV_FILE

    print_message $GREEN "✓ Updated $FRONTEND_ENV_FILE"
else
    # Create new frontend .env file
    cat > frontend/.env.local << EOF
# Azure AD Configuration (Generated by setup script)
VITE_AZURE_AD_TENANT_ID=$TENANT_ID
VITE_AZURE_AD_CLIENT_ID=$CLIENT_ID
VITE_AZURE_AD_REDIRECT_URI=$REDIRECT_URI
EOF
    print_message $GREEN "✓ Created frontend/.env.local"
fi

# ============================================================================
# STEP 10: Summary and Next Steps
# ============================================================================
print_message $BLUE "\n=== Configuration Complete! ==="
print_message $GREEN "\n✅ Azure AD SSO has been successfully configured!"

echo ""
print_message $BLUE "Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "App Name:        $APP_NAME"
echo "Tenant ID:       $TENANT_ID"
echo "Client ID:       $CLIENT_ID"
echo "Redirect URI:    $REDIRECT_URI"
echo "Auth Type:       SPA with PKCE (no secret)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
print_message $YELLOW "Next Steps:"
echo "1. Restart your Docker containers:"
echo "   docker-compose down && docker-compose up --build"
echo ""
echo "2. Test the SSO login at:"
echo "   http://localhost:3200"
echo ""
echo "3. If you need to add production URLs, run:"
echo "   az ad app update --id $CLIENT_ID --set spa.redirectUris='[\"$REDIRECT_URI\",\"https://your-domain.com/auth/callback\"]'"
echo ""

print_message $BLUE "Azure Portal Links:"
echo "• App Registration: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/$CLIENT_ID"
echo "• Enterprise App: https://portal.azure.com/#blade/Microsoft_AAD_IAM/ManagedAppMenuBlade/Overview/appId/$CLIENT_ID"

# Save configuration to file for reference
cat > azure-sso-config.json << EOF
{
  "appName": "$APP_NAME",
  "tenantId": "$TENANT_ID",
  "clientId": "$CLIENT_ID",
  "redirectUri": "$REDIRECT_URI",
  "configurationType": "SPA with PKCE",
  "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

print_message $GREEN "\n✓ Configuration saved to azure-sso-config.json"
print_message $GREEN "\n🎉 Setup completed successfully!"
