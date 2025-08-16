#!/bin/bash
# Script de configuration Route53 pour aws.nda-partners.com
# Région : eu-west-3 (Paris)

set -e

# Variables
DOMAIN="aws.nda-partners.com"
REGION="eu-west-3"
APP_DOMAIN="plan-de-charge.aws.nda-partners.com"

echo "🌐 Configuration Route53 pour $DOMAIN dans la région $REGION"

# Vérifier les credentials AWS
echo "📋 Vérification des credentials AWS..."
aws sts get-caller-identity --region $REGION

# 1. Créer la Hosted Zone
echo "📡 Création de la Hosted Zone pour $DOMAIN..."
ZONE_ID=$(aws route53 create-hosted-zone \
  --name $DOMAIN \
  --caller-reference "$(date +%s)-plan-charge" \
  --hosted-zone-config Comment="Zone déléguée pour les applications AWS NDA" \
  --query 'HostedZone.Id' \
  --output text 2>/dev/null || \
  aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='$DOMAIN.'].Id" \
  --output text)

echo "✅ Hosted Zone créée/trouvée: $ZONE_ID"

# 2. Récupérer les Name Servers
echo "📋 Name Servers à configurer dans OVH :"
echo "==========================================."
aws route53 get-hosted-zone --id $ZONE_ID \
  --query 'DelegationSet.NameServers' \
  --output table

echo ""
echo "⚠️  IMPORTANT: Vérifier que ces NS sont bien configurés dans OVH pour $DOMAIN"
echo ""

# 3. Vérifier la propagation DNS (peut prendre jusqu'à 48h)
echo "🔍 Test de propagation DNS..."
if nslookup -type=NS $DOMAIN 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ DNS propagé avec succès"
else
    echo "⏳ DNS en cours de propagation (peut prendre jusqu'à 48h)"
fi

# 4. Créer les certificats SSL
echo "🔒 Demande de certificats SSL..."

# Certificat pour CloudFront (doit être en us-east-1)
echo "📋 Certificat CloudFront (us-east-1)..."
CLOUDFRONT_CERT_ARN=$(aws acm request-certificate \
  --domain-name "$APP_DOMAIN" \
  --subject-alternative-names "*.aws.nda-partners.com" \
  --validation-method DNS \
  --region us-east-1 \
  --query 'CertificateArn' \
  --output text 2>/dev/null || echo "exists")

echo "📋 Certificat CloudFront: $CLOUDFRONT_CERT_ARN"

# Certificat pour ALB (eu-west-3)
echo "📋 Certificat ALB (eu-west-3)..."
ALB_CERT_ARN=$(aws acm request-certificate \
  --domain-name "$APP_DOMAIN" \
  --subject-alternative-names "api-$APP_DOMAIN" \
  --validation-method DNS \
  --region $REGION \
  --query 'CertificateArn' \
  --output text 2>/dev/null || echo "exists")

echo "📋 Certificat ALB: $ALB_CERT_ARN"

# 5. Sauvegarder les informations importantes
cat > aws-deployment/dns-info.env << EOF
# Configuration DNS et SSL
HOSTED_ZONE_ID=$ZONE_ID
DOMAIN=$DOMAIN
APP_DOMAIN=$APP_DOMAIN
CLOUDFRONT_CERT_ARN=$CLOUDFRONT_CERT_ARN
ALB_CERT_ARN=$ALB_CERT_ARN
AWS_REGION=$REGION
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
EOF

echo "✅ Informations sauvegardées dans dns-info.env"
echo ""
echo "📋 Prochaines étapes :"
echo "1. Attendre la propagation DNS (vérifier avec: dig NS $DOMAIN)"
echo "2. Valider les certificats SSL dans la console AWS ACM"
echo "3. Continuer avec la création des repositories ECR"
echo ""
echo "🎯 Une fois le DNS propagé, lancer: ./02-create-ecr.sh"