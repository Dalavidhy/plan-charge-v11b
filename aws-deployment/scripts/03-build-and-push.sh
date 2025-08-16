#!/bin/bash
# Script de build et push des images Docker vers ECR
# Région : eu-west-3 (Paris)

set -e

# Charger les variables d'environnement
source aws-deployment/dns-info.env

echo "🏗️  Building et push des images Docker vers ECR"
echo "📋 Registry: $ECR_URL"

# Login ECR
echo "📋 Login ECR..."
aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $ECR_URL

# Variables pour le tagging
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

echo "📋 Build timestamp: $TIMESTAMP"
echo "📋 Git SHA: $GIT_SHA"

# Build et push Backend
echo ""
echo "🔧 Building Backend image..."
docker build \
    -f aws-deployment/docker/backend/Dockerfile.prod \
    -t $ECR_BACKEND_URL:$GIT_SHA \
    -t $ECR_BACKEND_URL:$TIMESTAMP \
    -t $ECR_BACKEND_URL:latest \
    .

echo "📤 Pushing Backend image..."
docker push $ECR_BACKEND_URL:$GIT_SHA
docker push $ECR_BACKEND_URL:$TIMESTAMP
docker push $ECR_BACKEND_URL:latest

echo "✅ Backend image pushed"

# Build et push Frontend
echo ""
echo "🎨 Building Frontend image..."
docker build \
    -f aws-deployment/docker/frontend/Dockerfile.prod \
    -t $ECR_FRONTEND_URL:$GIT_SHA \
    -t $ECR_FRONTEND_URL:$TIMESTAMP \
    -t $ECR_FRONTEND_URL:latest \
    .

echo "📤 Pushing Frontend image..."
docker push $ECR_FRONTEND_URL:$GIT_SHA
docker push $ECR_FRONTEND_URL:$TIMESTAMP
docker push $ECR_FRONTEND_URL:latest

echo "✅ Frontend image pushed"

# Build et push Celery (même image que backend mais différents tags)
echo ""
echo "⚙️  Building Celery image..."
docker build \
    -f aws-deployment/docker/backend/Dockerfile.prod \
    -t $ECR_CELERY_URL:$GIT_SHA \
    -t $ECR_CELERY_URL:$TIMESTAMP \
    -t $ECR_CELERY_URL:latest \
    .

echo "📤 Pushing Celery image..."
docker push $ECR_CELERY_URL:$GIT_SHA
docker push $ECR_CELERY_URL:$TIMESTAMP
docker push $ECR_CELERY_URL:latest

echo "✅ Celery image pushed"

# Sauvegarder les informations de build
cat >> aws-deployment/dns-info.env << EOF

# Build Information
LAST_BUILD_TIMESTAMP=$TIMESTAMP
LAST_GIT_SHA=$GIT_SHA
BACKEND_IMAGE=$ECR_BACKEND_URL:$GIT_SHA
FRONTEND_IMAGE=$ECR_FRONTEND_URL:$GIT_SHA
CELERY_IMAGE=$ECR_CELERY_URL:$GIT_SHA
EOF

echo ""
echo "✅ Toutes les images sont pushées vers ECR!"
echo "📋 Images disponibles :"
echo "  Backend:  $ECR_BACKEND_URL:$GIT_SHA"
echo "  Frontend: $ECR_FRONTEND_URL:$GIT_SHA"
echo "  Celery:   $ECR_CELERY_URL:$GIT_SHA"
echo ""

# Vérifier les images dans ECR
echo "📋 Vérification des images dans ECR..."
echo "Backend repositories:"
aws ecr list-images --repository-name plan-charge-backend --region $AWS_REGION --query 'imageIds[?imageTag!=`null`].[imageTag]' --output table

echo "Frontend repositories:"
aws ecr list-images --repository-name plan-charge-frontend --region $AWS_REGION --query 'imageIds[?imageTag!=`null`].[imageTag]' --output table

echo ""
echo "🎯 Prochaine étape: Créer l'infrastructure Terraform"
echo "   Lancer: ./04-deploy-infrastructure.sh"