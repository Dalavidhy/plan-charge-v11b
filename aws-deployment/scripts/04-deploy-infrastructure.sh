#!/bin/bash
# Script de déploiement complet de l'infrastructure Plan de Charge
# Région : eu-west-3 (Paris)

set -e

# Charger les variables d'environnement
source aws-deployment/dns-info.env

echo "🚀 Déploiement de l'infrastructure Plan de Charge"
echo "📋 Région: $AWS_REGION"
echo "📋 Domaine: $APP_DOMAIN"
echo "📋 Account ID: $AWS_ACCOUNT_ID"
echo ""

# Vérifier les prérequis
echo "📋 Vérification des prérequis..."

# Vérifier Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform n'est pas installé"
    echo "   Installer avec: brew install terraform"
    exit 1
fi

# Vérifier AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI n'est pas installé"
    exit 1
fi

# Vérifier les credentials AWS
aws sts get-caller-identity --region $AWS_REGION > /dev/null || {
    echo "❌ Credentials AWS non configurés"
    exit 1
}

# Vérifier que les images sont dans ECR
echo "📋 Vérification des images ECR..."
for repo in plan-charge-backend plan-charge-frontend plan-charge-celery; do
    aws ecr describe-images --repository-name $repo --region $AWS_REGION > /dev/null || {
        echo "❌ Image $repo manquante dans ECR"
        echo "   Lancer: ./03-build-and-push.sh"
        exit 1
    }
done
echo "✅ Toutes les images sont présentes dans ECR"

# Naviguer vers le dossier Terraform
cd aws-deployment/terraform

# Initialiser Terraform
echo "📋 Initialisation de Terraform..."
terraform init

# Valider la configuration
echo "📋 Validation de la configuration Terraform..."
terraform validate

# Planifier le déploiement
echo "📋 Planification du déploiement..."
terraform plan \
    -var="aws_region=$AWS_REGION" \
    -var="domain_name=$APP_DOMAIN" \
    -var="hosted_zone_id=$HOSTED_ZONE_ID" \
    -var="backend_image_url=$ECR_BACKEND_URL:latest" \
    -var="frontend_image_url=$ECR_FRONTEND_URL:latest" \
    -var="celery_image_url=$ECR_CELERY_URL:latest" \
    -out=plan.tfplan

echo ""
echo "⚠️  ATTENTION: Vous allez déployer l'infrastructure complète"
echo "📋 Coût estimé: ~155€/mois"
echo "📋 Services: VPC, RDS, Redis, ECS, ALB, CloudFront"
echo ""

# Demander confirmation
read -p "Continuer avec le déploiement ? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Déploiement annulé"
    exit 1
fi

# Appliquer la configuration
echo "🚀 Déploiement en cours..."
terraform apply plan.tfplan

# Récupérer les outputs
echo ""
echo "📋 Récupération des informations de déploiement..."
APP_URL=$(terraform output -raw application_url)
ALB_URL=$(terraform output -raw alb_url)
API_URL=$(terraform output -raw api_url)
DOCS_URL=$(terraform output -raw docs_url)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)

# Sauvegarder les informations de déploiement
cd ../..
cat >> aws-deployment/dns-info.env << EOF

# Deployment Information
APP_URL=$APP_URL
ALB_URL=$ALB_URL
API_URL=$API_URL
DOCS_URL=$DOCS_URL
CLOUDFRONT_DISTRIBUTION_ID=$CLOUDFRONT_ID
DEPLOYMENT_DATE=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF

echo ""
echo "🎉 Déploiement terminé avec succès!"
echo ""
echo "📋 URLs d'accès:"
echo "   🌐 Application: $APP_URL"
echo "   🔧 API Direct:  $ALB_URL"
echo "   📖 API Docs:    $DOCS_URL"
echo ""
echo "📋 Services déployés:"
echo "   ✅ VPC avec 2 AZ (eu-west-3a, eu-west-3b)"
echo "   ✅ RDS PostgreSQL (db.t3.micro)"
echo "   ✅ ElastiCache Redis (cache.t3.micro)"
echo "   ✅ ECS Fargate (backend: 2 tâches, frontend: 2 tâches, celery: 1 tâche)"
echo "   ✅ Application Load Balancer avec SSL"
echo "   ✅ CloudFront CDN global"
echo "   ✅ Route53 DNS (en attente de propagation)"
echo ""
echo "⚠️  Important:"
echo "   • La propagation DNS peut prendre 24-48h"
echo "   • En attendant, utiliser: $ALB_URL"
echo "   • Configurer Azure AD avec l'URL: $APP_URL"
echo ""
echo "🔧 Prochaines étapes:"
echo "   1. Attendre la propagation DNS"
echo "   2. Configurer Azure AD (redirect URI)"
echo "   3. Tester l'application complète"
echo "   4. Configurer la surveillance CloudWatch"
echo ""
echo "💰 Coût mensuel estimé: ~155€"
echo "💡 Optimisation possible: ~105€ (sans NAT Gateway)"
