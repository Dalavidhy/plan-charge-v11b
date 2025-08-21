#!/bin/bash
# Simple Lambda SSO fix without VPC configuration
# This assumes RDS is publicly accessible

set -e

echo "🚀 Simple Lambda SSO Fix"
echo "========================"

# Configuration
FUNCTION_NAME="sso-fix-$(date +%Y%m%d-%H%M%S)"
REGION="eu-west-1"
ROLE_NAME="lambda-sso-fix-role-simple"
TEMP_DIR="/tmp/lambda-sso-fix-simple"
ZIP_FILE="lambda-sso-fix.zip"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."

    # Delete Lambda function
    aws lambda delete-function --function-name "$FUNCTION_NAME" --region "$REGION" 2>/dev/null || true

    # Delete IAM role
    aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>/dev/null || true
    aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true

    # Remove temp files
    rm -rf "$TEMP_DIR"
    echo "✅ Cleanup completed"
}

trap cleanup EXIT

# Step 1: Prepare deployment package
echo "📦 Preparing package..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Create simple requirements
echo "psycopg2-binary==2.9.9" > requirements.txt

# Install dependencies
pip install -r requirements.txt -t . --quiet

# Copy Lambda function
cp "/Users/david/Dev-Workspace/plan-charge-v11b/lambda_fix_sso.py" ./lambda_function.py

# Create deployment package
zip -r "$ZIP_FILE" . -q
echo "✅ Package created: $(ls -lh $ZIP_FILE | awk '{print $5}')"

# Step 2: Create IAM role
echo "🔐 Creating IAM role..."

cat > trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file://trust-policy.json \
    --region "$REGION" > /dev/null

# Attach basic execution role
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "⏳ Waiting for role..."
sleep 10

# Step 3: Create Lambda function (no VPC)
echo "🚀 Creating Lambda function..."

aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime python3.9 \
    --role "arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME" \
    --handler lambda_function.lambda_handler \
    --zip-file "fileb://$ZIP_FILE" \
    --timeout 30 \
    --memory-size 128 \
    --environment Variables='{
        "DB_HOST":"plan-charge-db.cluster-c7sdx2kjcw7j.eu-west-1.rds.amazonaws.com",
        "DB_NAME":"plancharge",
        "DB_USER":"plancharge",
        "DB_PASSWORD":"4Se%3CvRRq5KF9r)ms"
    }' \
    --region "$REGION" > /dev/null

echo "✅ Lambda created"

# Wait for function to be ready
echo "⏳ Waiting for Lambda..."
sleep 10

# Step 4: Execute the fix
echo "🔧 Executing SSO fix..."

aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    response.json > /dev/null

if [ -f response.json ]; then
    echo "📄 Response:"
    cat response.json | jq .

    SUCCESS=$(cat response.json | jq -r '.body | fromjson | .success // false' 2>/dev/null || echo "false")

    if [ "$SUCCESS" = "true" ]; then
        echo "🎉 SSO FIX SUCCESSFUL!"
        echo "✅ Default Organization added to database"
        echo "🚀 Test at: https://plan-de-charge.aws.nda-partners.com"
    else
        echo "❌ Fix may have failed - check response above"
    fi
else
    echo "❌ No response from Lambda"
fi
