#!/bin/bash
# Automated Lambda deployment script for SSO fix
# This script creates a temporary Lambda function, executes the fix, and cleans up

set -e

echo "🚀 Lambda SSO Fix - Automated Deployment"
echo "========================================"

# Configuration
FUNCTION_NAME="sso-fix-$(date +%Y%m%d-%H%M%S)"
REGION="eu-west-1"
ROLE_NAME="lambda-sso-fix-role"
POLICY_NAME="lambda-sso-fix-policy"
TEMP_DIR="/tmp/lambda-sso-fix"
ZIP_FILE="lambda-sso-fix.zip"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "🧹 Cleaning up..."

    # Delete Lambda function
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &>/dev/null; then
        aws lambda delete-function --function-name "$FUNCTION_NAME" --region "$REGION"
        log_info "Lambda function deleted"
    fi

    # Delete IAM role and policy
    if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
        aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME" 2>/dev/null || true
        aws iam delete-policy --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME" 2>/dev/null || true
        aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true
        log_info "IAM resources deleted"
    fi

    # Remove temp files
    rm -rf "$TEMP_DIR"
    log_info "Temporary files removed"
}

# Set up cleanup on exit
trap cleanup EXIT

# Step 1: Prepare deployment package
log_info "📦 Preparing deployment package..."

mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Create requirements.txt
cat > requirements.txt << EOF
psycopg2-binary==2.9.9
EOF

# Install dependencies
log_info "📥 Installing dependencies..."
pip install -r requirements.txt -t .

# Copy Lambda function
cp "/Users/david/Dev-Workspace/plan-charge-v11b/lambda_fix_sso.py" ./lambda_function.py

# Create deployment package
zip -r "$ZIP_FILE" . -x "*.pyc" "__pycache__/*" "*.DS_Store"

log_info "✅ Deployment package created: $(ls -lh $ZIP_FILE | awk '{print $5}')"

# Step 2: Create IAM role
log_info "🔐 Creating IAM role..."

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
    --region "$REGION"

# Create policy for VPC access
cat > lambda-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface"
            ],
            "Resource": "*"
        }
    ]
}
EOF

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document file://lambda-policy.json

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"

# Wait for role to be ready
log_info "⏳ Waiting for IAM role to be ready..."
sleep 10

# Step 3: Get VPC configuration
log_info "🔍 Finding VPC configuration..."

# Try to find the backend VPC/subnets
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --query 'Vpcs[?Tags[?Key==`Name` && contains(Value, `plan-charge`)]].VpcId | [0]' --output text 2>/dev/null || echo "")

if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    # Fallback to default VPC
    VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
fi

SUBNET_IDS=$(aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text | tr '\t' ',')

SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text)

log_info "📋 VPC Configuration:"
log_info "   VPC ID: $VPC_ID"
log_info "   Subnets: $SUBNET_IDS"
log_info "   Security Group: $SECURITY_GROUP_ID"

# Step 4: Create Lambda function
log_info "🚀 Creating Lambda function..."

aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime python3.9 \
    --role "arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME" \
    --handler lambda_function.lambda_handler \
    --zip-file "fileb://$ZIP_FILE" \
    --timeout 30 \
    --memory-size 128 \
    --vpc-config SubnetIds="$SUBNET_IDS",SecurityGroupIds="$SECURITY_GROUP_ID" \
    --environment Variables='{
        "DB_HOST":"plan-charge-db.cluster-c7sdx2kjcw7j.eu-west-1.rds.amazonaws.com",
        "DB_NAME":"plancharge",
        "DB_USER":"plancharge",
        "DB_PASSWORD":"4Se%3CvRRq5KF9r)ms"
    }' \
    --region "$REGION"

log_info "✅ Lambda function created"

# Wait for function to be ready
log_info "⏳ Waiting for Lambda to be ready..."
sleep 15

# Step 5: Execute the fix
log_info "🔧 Executing SSO fix..."

RESULT=$(aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --log-type Tail \
    --query 'LogResult' \
    --output text \
    response.json | base64 --decode)

echo "📋 Lambda execution logs:"
echo "$RESULT"

# Check the response
if [ -f response.json ]; then
    echo "📄 Lambda response:"
    cat response.json | jq .

    # Check if it was successful
    SUCCESS=$(cat response.json | jq -r '.body | fromjson | .success // false')

    if [ "$SUCCESS" = "true" ]; then
        log_info "🎉 SSO FIX SUCCESSFUL!"
        log_info "✅ Default Organization has been added to the database"
        log_info "✅ SSO authentication should now work without 500 errors"
        log_info "🚀 Test login at: https://plan-de-charge.aws.nda-partners.com"
    else
        log_error "❌ SSO fix failed - check the logs above"
        exit 1
    fi
else
    log_error "❌ No response from Lambda"
    exit 1
fi

log_info "🧪 You can now test SSO authentication!"
log_info "   1. Go to: https://plan-de-charge.aws.nda-partners.com"
log_info "   2. Click login with your @nda-partners.com email"
log_info "   3. Should work without 500 errors!"

# Cleanup happens automatically via trap
