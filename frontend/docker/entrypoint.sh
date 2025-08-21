#!/bin/sh

# Entrypoint script for Plan Charge frontend
# Replaces environment variables placeholders in built JavaScript files

set -e

echo "🚀 Starting Plan Charge Frontend with environment injection..."

# Function to replace placeholders in JavaScript files
inject_env_vars() {
    echo "🔧 Injecting environment variables into JavaScript files..."

    # Find all JavaScript files in the build output
    find /usr/share/nginx/html/assets -name "*.js" -type f | while read -r file; do
        echo "📝 Processing: $file"

        # Replace placeholders with actual environment variables
        sed -i "s|__VITE_AZURE_AD_CLIENT_ID__|${VITE_AZURE_AD_CLIENT_ID:-}|g" "$file"
        sed -i "s|__VITE_AZURE_AD_TENANT_ID__|${VITE_AZURE_AD_TENANT_ID:-}|g" "$file"
        sed -i "s|__VITE_AZURE_AD_REDIRECT_URI__|${VITE_AZURE_AD_REDIRECT_URI:-}|g" "$file"
        sed -i "s|__VITE_API_URL__|${VITE_API_URL:-/api/v1}|g" "$file"
    done

    echo "✅ Environment variables injected successfully"
}

# Generate runtime config file
generate_config() {
    echo "📋 Generating runtime configuration..."

    cat > /usr/share/nginx/html/config.js << EOF
// Runtime configuration injected by entrypoint
window.ENV_CONFIG = {
  VITE_AZURE_AD_CLIENT_ID: "${VITE_AZURE_AD_CLIENT_ID:-}",
  VITE_AZURE_AD_TENANT_ID: "${VITE_AZURE_AD_TENANT_ID:-}",
  VITE_AZURE_AD_REDIRECT_URI: "${VITE_AZURE_AD_REDIRECT_URI:-}",
  VITE_API_URL: "${VITE_API_URL:-/api/v1}",
  VITE_GRYZZLY_USE_MOCK: "${VITE_GRYZZLY_USE_MOCK:-false}"
};
EOF

    echo "✅ Runtime config generated at /usr/share/nginx/html/config.js"
}

# Validate required environment variables
validate_env() {
    echo "🔍 Validating environment variables..."

    missing_vars=""

    if [ -z "$VITE_AZURE_AD_CLIENT_ID" ]; then
        missing_vars="$missing_vars VITE_AZURE_AD_CLIENT_ID"
    fi

    if [ -z "$VITE_AZURE_AD_TENANT_ID" ]; then
        missing_vars="$missing_vars VITE_AZURE_AD_TENANT_ID"
    fi

    if [ -z "$VITE_AZURE_AD_REDIRECT_URI" ]; then
        missing_vars="$missing_vars VITE_AZURE_AD_REDIRECT_URI"
    fi

    if [ -n "$missing_vars" ]; then
        echo "❌ ERROR: Missing required environment variables:$missing_vars"
        echo "Please configure Azure AD environment variables in ECS task definition"
        exit 1
    fi

    echo "✅ All required environment variables are present"
    echo "   - Client ID: ${VITE_AZURE_AD_CLIENT_ID}"
    echo "   - Tenant ID: ${VITE_AZURE_AD_TENANT_ID}"
    echo "   - Redirect URI: ${VITE_AZURE_AD_REDIRECT_URI}"
    echo "   - API URL: ${VITE_API_URL:-/api/v1}"
}

# Main execution
main() {
    echo "=================================="
    echo "Plan Charge Frontend - Environment: ${ENVIRONMENT:-development}"
    echo "=================================="

    # Validate environment variables
    validate_env

    # Generate runtime config (preferred method)
    generate_config

    # Also inject into JS files as fallback
    inject_env_vars

    echo "🎯 Starting nginx..."
    echo "=================================="

    # Start nginx in foreground
    exec nginx -g "daemon off;"
}

# Run main function
main "$@"
