#!/bin/bash

set -e

echo "🧪 Tests de production Plan de Charge"

API_URL="https://api.plan-de-charge.aws.nda-partners.com"
FRONTEND_URL="https://plan-de-charge.aws.nda-partners.com"

echo "🔍 Test de l'API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [[ $API_STATUS == "200" ]]; then
  echo "✅ API accessible ($API_STATUS)"
else
  echo "❌ API inaccessible ($API_STATUS)"
  exit 1
fi

echo "🔍 Test du frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
if [[ $FRONTEND_STATUS == "200" ]]; then
  echo "✅ Frontend accessible ($FRONTEND_STATUS)"
else
  echo "❌ Frontend inaccessible ($FRONTEND_STATUS)"
  exit 1
fi

echo "🔍 Test de la base de données..."
DB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/api/v1/collaborators?limit=1)
if [[ $DB_STATUS == "200" ]]; then
  echo "✅ Base de données accessible ($DB_STATUS)"
else
  echo "❌ Base de données inaccessible ($DB_STATUS)"
  exit 1
fi

echo "🔍 Test des logs ECS..."
LOG_GROUPS=$(aws logs describe-log-groups --log-group-name-prefix "/ecs/plan-charge-prod" --query "logGroups[0].logGroupName" --output text)
if [[ $LOG_GROUPS != "None" ]]; then
  echo "✅ Logs ECS disponibles ($LOG_GROUPS)"
else
  echo "⚠️ Aucun log ECS trouvé"
fi

echo "🔍 Test du service ECS..."
SERVICE_STATUS=$(aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend --query "services[0].status" --output text)
RUNNING_COUNT=$(aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend --query "services[0].runningCount" --output text)
DESIRED_COUNT=$(aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend --query "services[0].desiredCount" --output text)

if [[ $SERVICE_STATUS == "ACTIVE" ]] && [[ $RUNNING_COUNT == $DESIRED_COUNT ]]; then
  echo "✅ Service ECS en fonctionnement ($RUNNING_COUNT/$DESIRED_COUNT tâches actives)"
else
  echo "❌ Service ECS en problème (Status: $SERVICE_STATUS, Tâches: $RUNNING_COUNT/$DESIRED_COUNT)"
  exit 1
fi

echo "✅ Tous les tests de production sont passés avec succès !"
