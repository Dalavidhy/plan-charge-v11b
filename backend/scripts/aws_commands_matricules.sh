#!/bin/bash

# =============================================================================
# Script de commandes AWS pour l'intervention matricules
# Date : 2025-01-21
# =============================================================================

set -e  # Exit on error

# Configuration
REGION="eu-west-3"
DB_INSTANCE="plan-charge-prod-db"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SNAPSHOT_NAME="plan-charge-prod-db-before-matricules-${TIMESTAMP}"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Intervention Matricules Production ===${NC}"
echo "Date: $(date)"
echo ""

# =============================================================================
# 1. Créer un snapshot RDS
# =============================================================================
echo -e "${YELLOW}Étape 1: Création du snapshot RDS...${NC}"
aws rds create-db-snapshot \
    --db-instance-identifier ${DB_INSTANCE} \
    --db-snapshot-identifier ${SNAPSHOT_NAME} \
    --region ${REGION}

echo "Snapshot créé: ${SNAPSHOT_NAME}"
echo "Attente de la création du snapshot..."

# Attendre que le snapshot soit disponible
aws rds wait db-snapshot-completed \
    --db-snapshot-identifier ${SNAPSHOT_NAME} \
    --region ${REGION}

echo -e "${GREEN}✓ Snapshot créé avec succès${NC}"
echo ""

# =============================================================================
# 2. Vérifier le snapshot
# =============================================================================
echo -e "${YELLOW}Étape 2: Vérification du snapshot...${NC}"
SNAPSHOT_STATUS=$(aws rds describe-db-snapshots \
    --db-snapshot-identifier ${SNAPSHOT_NAME} \
    --region ${REGION} \
    --query 'DBSnapshots[0].Status' \
    --output text)

if [ "$SNAPSHOT_STATUS" = "available" ]; then
    echo -e "${GREEN}✓ Snapshot disponible et prêt${NC}"
else
    echo -e "${RED}✗ Erreur: Snapshot status: ${SNAPSHOT_STATUS}${NC}"
    exit 1
fi
echo ""

# =============================================================================
# 3. Récupérer l'ID de l'instance bastion
# =============================================================================
echo -e "${YELLOW}Étape 3: Recherche de l'instance bastion...${NC}"
BASTION_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=*bastion*" "Name=instance-state-name,Values=running" \
    --region ${REGION} \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$BASTION_ID" = "None" ] || [ -z "$BASTION_ID" ]; then
    echo -e "${RED}✗ Erreur: Aucune instance bastion trouvée${NC}"
    echo "Vérifiez manuellement avec: aws ec2 describe-instances --region ${REGION}"
    exit 1
fi

echo "Instance bastion trouvée: ${BASTION_ID}"
echo ""

# =============================================================================
# 4. Récupérer les informations RDS
# =============================================================================
echo -e "${YELLOW}Étape 4: Récupération des informations RDS...${NC}"
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE} \
    --region ${REGION} \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

RDS_PORT=$(aws rds describe-db-instances \
    --db-instance-identifier ${DB_INSTANCE} \
    --region ${REGION} \
    --query 'DBInstances[0].Endpoint.Port' \
    --output text)

echo "RDS Endpoint: ${RDS_ENDPOINT}"
echo "RDS Port: ${RDS_PORT}"
echo ""

# =============================================================================
# 5. Générer les commandes de connexion
# =============================================================================
echo -e "${YELLOW}Étape 5: Commandes de connexion${NC}"
echo ""
echo "Pour vous connecter au bastion:"
echo -e "${GREEN}aws ssm start-session --target ${BASTION_ID} --region ${REGION}${NC}"
echo ""
echo "Une fois sur le bastion, connectez-vous à PostgreSQL:"
echo -e "${GREEN}psql -h ${RDS_ENDPOINT} -U plancharge_user -d plancharge_db -p ${RDS_PORT}${NC}"
echo ""

# =============================================================================
# 6. Créer un fichier avec les informations de connexion
# =============================================================================
cat > connection_info_${TIMESTAMP}.txt << EOF
=== Informations de connexion - ${TIMESTAMP} ===

Snapshot créé: ${SNAPSHOT_NAME}
Instance Bastion: ${BASTION_ID}
RDS Endpoint: ${RDS_ENDPOINT}
RDS Port: ${RDS_PORT}

Commandes:
1. aws ssm start-session --target ${BASTION_ID} --region ${REGION}
2. psql -h ${RDS_ENDPOINT} -U plancharge_user -d plancharge_db -p ${RDS_PORT}

Script SQL à exécuter: update_matricules_production.sql
EOF

echo -e "${GREEN}✓ Informations sauvegardées dans: connection_info_${TIMESTAMP}.txt${NC}"
echo ""

# =============================================================================
# 7. Monitoring post-intervention
# =============================================================================
echo -e "${YELLOW}Commandes de monitoring post-intervention:${NC}"
echo ""
echo "Suivre les logs CloudWatch:"
echo -e "${GREEN}aws logs tail /aws/ecs/plan-charge-backend --follow --region ${REGION}${NC}"
echo ""
echo "Vérifier les métriques RDS:"
echo -e "${GREEN}aws cloudwatch get-metric-statistics \\
    --namespace AWS/RDS \\
    --metric-name DatabaseConnections \\
    --dimensions Name=DBInstanceIdentifier,Value=${DB_INSTANCE} \\
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \\
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \\
    --period 300 \\
    --statistics Average \\
    --region ${REGION}${NC}"
echo ""

# =============================================================================
# 8. Commande de rollback si nécessaire
# =============================================================================
echo -e "${YELLOW}En cas de problème, pour restaurer depuis le snapshot:${NC}"
echo -e "${RED}aws rds restore-db-instance-from-db-snapshot \\
    --db-instance-identifier plan-charge-db-restored \\
    --db-snapshot-identifier ${SNAPSHOT_NAME} \\
    --region ${REGION}${NC}"
echo ""

echo -e "${GREEN}=== Préparation terminée ===${NC}"
echo "Snapshot de sécurité créé: ${SNAPSHOT_NAME}"
echo "Vous pouvez maintenant procéder à l'intervention"
echo ""
echo -e "${YELLOW}⚠️  N'oubliez pas de faire COMMIT après vérification des résultats!${NC}"
