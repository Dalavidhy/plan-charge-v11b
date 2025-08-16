#!/bin/bash
# Create temporary EC2 bastion host to fix SSO database issue
# This creates an instance, executes the fix, and terminates

set -e

echo "🚀 EC2 Bastion SSO Fix - EU-West-3"
echo "=================================="

# Configuration
REGION="eu-west-3"
KEY_NAME="temp-sso-fix-key"
INSTANCE_NAME="temp-sso-fix-$(date +%Y%m%d-%H%M%S)"
INSTANCE_TYPE="t2.micro"

# Get default VPC and subnet
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNET_ID=$(aws ec2 describe-subnets --region "$REGION" --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0].SubnetId' --output text)

if [ "$VPC_ID" = "None" ] || [ "$SUBNET_ID" = "None" ]; then
    echo "❌ No default VPC found in $REGION"
    echo "💡 Please create this manually or use existing VPC"
    exit 1
fi

echo "📋 Using VPC: $VPC_ID, Subnet: $SUBNET_ID"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    if [ ! -z "$INSTANCE_ID" ]; then
        aws ec2 terminate-instances --region "$REGION" --instance-ids "$INSTANCE_ID" &>/dev/null || true
        echo "✅ Instance terminated"
    fi
    if aws ec2 describe-key-pairs --region "$REGION" --key-names "$KEY_NAME" &>/dev/null; then
        aws ec2 delete-key-pair --region "$REGION" --key-name "$KEY_NAME" &>/dev/null || true
        rm -f "/tmp/${KEY_NAME}.pem" &>/dev/null || true
        echo "✅ Key pair deleted"
    fi
    if [ ! -z "$SG_ID" ]; then
        aws ec2 delete-security-group --region "$REGION" --group-id "$SG_ID" &>/dev/null || true
        echo "✅ Security group deleted"
    fi
}

trap cleanup EXIT

# Step 1: Create temporary key pair
echo "🔑 Creating temporary key pair..."
aws ec2 create-key-pair \
    --region "$REGION" \
    --key-name "$KEY_NAME" \
    --query 'KeyMaterial' \
    --output text > "/tmp/${KEY_NAME}.pem"

chmod 600 "/tmp/${KEY_NAME}.pem"
echo "✅ Key pair created"

# Step 2: Create security group for PostgreSQL access
echo "🛡️ Creating security group..."
SG_NAME="temp-sso-fix-sg-$(date +%Y%m%d-%H%M%S)"
SG_ID=$(aws ec2 create-security-group \
    --region "$REGION" \
    --group-name "$SG_NAME" \
    --description "Temporary SG for SSO fix" \
    --vpc-id "$VPC_ID" \
    --query 'GroupId' \
    --output text)

# Allow SSH access
aws ec2 authorize-security-group-ingress \
    --region "$REGION" \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

echo "✅ Security group created: $SG_ID"

# Step 3: Launch EC2 instance
echo "🚀 Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region "$REGION" \
    --image-id ami-028255970c7184d8b \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --subnet-id "$SUBNET_ID" \
    --security-group-ids "$SG_ID" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data '#!/bin/bash
yum update -y
amazon-linux-extras install postgresql12 -y' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# Step 4: Wait for instance to be ready
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region "$REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance ready: $PUBLIC_IP"

# Step 5: Wait for SSH to be ready
echo "⏳ Waiting for SSH access..."
for i in {1..30}; do
    if ssh -i "/tmp/${KEY_NAME}.pem" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ec2-user@$PUBLIC_IP "echo 'SSH ready'" &>/dev/null; then
        echo "✅ SSH access ready"
        break
    fi
    sleep 10
    if [ $i -eq 30 ]; then
        echo "❌ SSH access timeout"
        exit 1
    fi
done

# Step 6: Execute the SQL fix
echo "🔧 Executing SSO fix..."
ssh -i "/tmp/${KEY_NAME}.pem" -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP << 'EOF'
echo "🔧 Installing PostgreSQL client..."
sudo yum install -y postgresql

echo "🔗 Connecting to database..."
PGPASSWORD="4Se%3CvRRq5KF9r)ms" psql \
    -h "plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com" \
    -U plancharge \
    -d plancharge \
    -c "INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW(), NULL) ON CONFLICT (id) DO NOTHING;"

if [ $? -eq 0 ]; then
    echo "✅ SQL executed successfully!"
    
    # Verify the fix
    echo "🔍 Verifying organizations..."
    PGPASSWORD="4Se%3CvRRq5KF9r)ms" psql \
        -h "plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com" \
        -U plancharge \
        -d plancharge \
        -c "SELECT id, name FROM organizations ORDER BY name;"
    
    echo "🎉 SSO FIX COMPLETED!"
    echo "✅ Default Organization added to database"
    echo "🚀 Test login at: https://plan-de-charge.aws.nda-partners.com"
else
    echo "❌ SQL execution failed"
    exit 1
fi
EOF

if [ $? -eq 0 ]; then
    echo "🎉 SUCCESS! SSO fix executed successfully!"
    echo "✅ Default Organization added to database"
    echo "🚀 Test login at: https://plan-de-charge.aws.nda-partners.com"
else
    echo "❌ Fix execution failed"
    exit 1
fi

# Cleanup happens automatically via trap