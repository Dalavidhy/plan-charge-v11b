#!/bin/bash

set -e

echo "🚀 Déploiement Plan de Charge Production"

# Variables
ECR_REPOSITORY="557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend"
ECS_CLUSTER="plan-charge-prod-cluster"
ECS_SERVICE="plan-charge-prod-backend"
TASK_DEFINITION="plan-charge-prod-backend"
AWS_REGION="eu-west-3"

# Build et push de l'image Docker
echo "📦 Build et push de l'image Docker..."
docker build --platform linux/amd64 -t $ECR_REPOSITORY:latest backend/
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY
docker push $ECR_REPOSITORY:latest

# Mise à jour de la task definition
echo "📋 Mise à jour de la task definition..."
aws ecs register-task-definition \
  --cli-input-json file://aws-deployment/task-definitions/production-task-definition.json \
  --region $AWS_REGION

# Mise à jour du service
echo "🔄 Mise à jour du service ECS..."
aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service $ECS_SERVICE \
  --task-definition $TASK_DEFINITION \
  --region $AWS_REGION

# Attendre la stabilité du service
echo "⏳ Attente de la stabilité du service..."
aws ecs wait services-stable \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --region $AWS_REGION

echo "✅ Déploiement terminé avec succès !"
