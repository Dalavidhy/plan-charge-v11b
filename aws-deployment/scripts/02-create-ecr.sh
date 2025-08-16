#!/bin/bash
# Script de création des repositories ECR
# Région : eu-west-3 (Paris)

set -e

# Charger les variables d'environnement
source aws-deployment/dns-info.env

echo "📦 Création des repositories ECR dans la région $AWS_REGION"

# Repositories à créer
REPOSITORIES=(
    "plan-charge-backend"
    "plan-charge-frontend"
    "plan-charge-celery"
)

# Créer les repositories ECR
for REPO in "${REPOSITORIES[@]}"; do
    echo "📋 Création du repository: $REPO"
    
    # Créer le repository (ignore si existe déjà)
    aws ecr create-repository \
        --repository-name $REPO \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 2>/dev/null || \
    echo "⚠️  Repository $REPO existe déjà"
    
    # Configurer la politique de lifecycle
    aws ecr put-lifecycle-policy \
        --repository-name $REPO \
        --region $AWS_REGION \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep last 10 images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }' >/dev/null
        
    echo "✅ Repository $REPO configuré"
done

# Obtenir l'URL de login ECR
ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "📋 Login ECR..."
aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $ECR_URL

echo "✅ Connecté à ECR: $ECR_URL"

# Sauvegarder les URLs ECR
cat >> aws-deployment/dns-info.env << EOF

# URLs ECR
ECR_URL=$ECR_URL
ECR_BACKEND_URL=$ECR_URL/plan-charge-backend
ECR_FRONTEND_URL=$ECR_URL/plan-charge-frontend
ECR_CELERY_URL=$ECR_URL/plan-charge-celery
EOF

echo "✅ URLs ECR sauvegardées dans dns-info.env"
echo ""
echo "📋 Repositories ECR créés :"
for REPO in "${REPOSITORIES[@]}"; do
    echo "  - $ECR_URL/$REPO"
done
echo ""
echo "🎯 Prochaine étape: Créer les Dockerfiles de production"
echo "   Lancer: ./03-create-dockerfiles.sh"