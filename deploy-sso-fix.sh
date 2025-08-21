#!/bin/bash
# Deployment script for SSO organization fix
# This script should be run by someone with AWS ECR and ECS permissions

set -e

echo "🚀 Deploying SSO Organization Fix"
echo "=================================="

# Configuration
ECR_REGISTRY="339713025992.dkr.ecr.eu-west-1.amazonaws.com"
REPOSITORY="plan-charge-backend"
IMAGE_TAG="sso-fix-$(date +%Y%m%d-%H%M%S)"
REGION="eu-west-1"
CLUSTER="plan-charge-cluster"
SERVICE="plan-charge-backend"

echo "📦 Building Docker image..."
docker build -f aws-deployment/docker/backend/Dockerfile.prod -t ${REPOSITORY}:${IMAGE_TAG} .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo "🏷️  Tagging image for ECR..."
docker tag ${REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${REPOSITORY}:${IMAGE_TAG}
docker tag ${REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${REPOSITORY}:latest

echo "📤 Pushing image to ECR..."
docker push ${ECR_REGISTRY}/${REPOSITORY}:${IMAGE_TAG}
docker push ${ECR_REGISTRY}/${REPOSITORY}:latest

echo "🔄 Updating ECS service..."
aws ecs update-service \
  --cluster ${CLUSTER} \
  --service ${SERVICE} \
  --force-new-deployment \
  --region ${REGION}

echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
  --cluster ${CLUSTER} \
  --services ${SERVICE} \
  --region ${REGION}

echo "✅ Deployment completed successfully!"
echo "🔍 New image: ${ECR_REGISTRY}/${REPOSITORY}:${IMAGE_TAG}"
echo ""
echo "📋 What was fixed:"
echo "- Changed organization name from 'Default Organization' to 'NDA Partners'"
echo "- Fixed in azure_sso.py and auth.py"
echo "- This should resolve the 500 error during SSO authentication"
echo ""
echo "🧪 Next steps:"
echo "1. Wait 2-3 minutes for the new service to be fully running"
echo "2. Test SSO authentication at: https://plan-de-charge.aws.nda-partners.com"
echo "3. Clear browser cache/localStorage if needed"
echo "4. Check CloudWatch logs if issues persist"

# Optional: Check service status
echo "📊 Current service status:"
aws ecs describe-services \
  --cluster ${CLUSTER} \
  --services ${SERVICE} \
  --region ${REGION} \
  --query 'services[0].deployments[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount,TaskDefinition:taskDefinition}' \
  --output table
