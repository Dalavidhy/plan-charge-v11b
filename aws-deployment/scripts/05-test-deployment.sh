#!/bin/bash
# Script de test du déploiement Plan de Charge

set -e

# Charger les variables d'environnement
source aws-deployment/dns-info.env

echo "🧪 Tests du déploiement Plan de Charge"
echo "📋 Domaine: $APP_DOMAIN"
echo ""

# Test 1: DNS Resolution
echo "🔍 Test 1: Résolution DNS"
if nslookup $APP_DOMAIN > /dev/null 2>&1; then
    echo "✅ DNS résolu avec succès"
    nslookup $APP_DOMAIN | grep -A2 "Non-authoritative answer:"
else
    echo "⚠️  DNS en cours de propagation"
    echo "   Utiliser l'URL ALB en attendant: $ALB_URL"
fi
echo ""

# Test 2: SSL Certificate
echo "🔒 Test 2: Certificat SSL"
if timeout 10 openssl s_client -connect ${APP_DOMAIN}:443 -servername $APP_DOMAIN < /dev/null > /dev/null 2>&1; then
    echo "✅ Certificat SSL valide"
    echo "📋 Détails du certificat:"
    echo | openssl s_client -connect ${APP_DOMAIN}:443 -servername $APP_DOMAIN 2>/dev/null | openssl x509 -noout -subject -dates
else
    echo "⚠️  Certificat SSL en cours de configuration"
fi
echo ""

# Test 3: Frontend (via CloudFront)
echo "🎨 Test 3: Frontend via CloudFront"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_DOMAIN/ || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend accessible"
    echo "📋 Temps de réponse:"
    curl -w "   Connect: %{time_connect}s, Total: %{time_total}s\n" -o /dev/null -s https://$APP_DOMAIN/
else
    echo "❌ Frontend inaccessible (Status: $FRONTEND_STATUS)"
fi
echo ""

# Test 4: API Health Check
echo "🔧 Test 4: API Health Check"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_DOMAIN/api/v1/health || echo "000")
if [ "$API_STATUS" = "200" ]; then
    echo "✅ API accessible"
    echo "📋 Réponse API:"
    curl -s https://$APP_DOMAIN/api/v1/health | jq . 2>/dev/null || curl -s https://$APP_DOMAIN/api/v1/health
else
    echo "❌ API inaccessible (Status: $API_STATUS)"
fi
echo ""

# Test 5: Documentation API
echo "📖 Test 5: Documentation API"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_DOMAIN/docs || echo "000")
if [ "$DOCS_STATUS" = "200" ]; then
    echo "✅ Documentation accessible"
    echo "📋 URL: https://$APP_DOMAIN/docs"
else
    echo "❌ Documentation inaccessible (Status: $DOCS_STATUS)"
fi
echo ""

# Test 6: CloudFront Performance
echo "⚡ Test 6: Performance CloudFront"
echo "📋 Test de performance sur différents endpoints:"

endpoints=(
    "/"
    "/assets/index-DFpBAb1x.css"
    "/api/v1/health"
    "/docs"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "   $endpoint: "
    curl -w "Total: %{time_total}s, CDN: %{time_starttransfer}s\n" -o /dev/null -s "https://$APP_DOMAIN$endpoint" || echo "Failed"
done
echo ""

# Test 7: Auto Scaling (si applicable)
echo "📊 Test 7: État des services ECS"
if [ ! -z "$AWS_REGION" ]; then
    echo "📋 Services ECS actifs:"
    aws ecs list-services --cluster plan-charge-prod-cluster --region $AWS_REGION --output table --query 'serviceArns' 2>/dev/null || echo "   Erreur d'accès ECS"
    
    echo "📋 Tasks en cours d'exécution:"
    aws ecs list-tasks --cluster plan-charge-prod-cluster --region $AWS_REGION --desired-status RUNNING --output table --query 'taskArns' 2>/dev/null || echo "   Erreur d'accès ECS"
fi
echo ""

# Test 8: Logs CloudWatch
echo "📝 Test 8: Logs CloudWatch"
if [ ! -z "$AWS_REGION" ]; then
    echo "📋 Groupes de logs disponibles:"
    aws logs describe-log-groups --log-group-name-prefix "/ecs/plan-charge" --region $AWS_REGION --output table --query 'logGroups[].logGroupName' 2>/dev/null || echo "   Erreur d'accès CloudWatch"
fi
echo ""

# Résumé
echo "📊 RÉSUMÉ DES TESTS"
echo "=================="
echo "🌐 Application URL: $APP_URL"
echo "🔧 API directe:     $ALB_URL"
echo "📖 Documentation:   $DOCS_URL"
echo ""

if [ "$FRONTEND_STATUS" = "200" ] && [ "$API_STATUS" = "200" ]; then
    echo "🎉 DÉPLOIEMENT RÉUSSI!"
    echo "✅ L'application est opérationnelle"
    echo ""
    echo "📋 Prochaines étapes:"
    echo "   1. Configurer Azure AD avec l'URL: $APP_URL"
    echo "   2. Tester le flux d'authentification complet"
    echo "   3. Configurer la surveillance et les alertes"
    echo "   4. Effectuer des tests de charge"
else
    echo "⚠️  DÉPLOIEMENT PARTIEL"
    echo "❌ Certains services ne sont pas encore accessibles"
    echo ""
    echo "🔧 Actions à effectuer:"
    echo "   1. Vérifier les logs ECS: aws logs tail /ecs/plan-charge-prod --follow"
    echo "   2. Vérifier l'état des services: aws ecs describe-services --cluster plan-charge-prod-cluster"
    echo "   3. Attendre la propagation DNS complète (24-48h)"
fi

echo ""
echo "💰 Coût estimé: ~155€/mois"
echo "📊 Monitoring: CloudWatch Dashboard disponible dans la console AWS"