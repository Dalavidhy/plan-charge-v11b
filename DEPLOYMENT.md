# Guide de Déploiement - Plan de Charge

## 🏗️ Architecture de Déploiement

### Infrastructure AWS
- **ECS Fargate** : Hébergement de l'application backend
- **ECR** : Registry Docker pour les images
- **RDS PostgreSQL** : Base de données
- **ElastiCache Redis** : Cache et sessions
- **S3 + CloudFront** : Frontend statique
- **ALB** : Load balancer pour l'API
- **SSM Parameter Store** : Gestion des secrets

### Environnements
- **Production uniquement** : `https://plan-de-charge.aws.nda-partners.com`

## 🚀 Déploiement Automatique via GitHub Actions

### Workflows Configurés

1. **Tests** (`.github/workflows/tests.yml`)
   - Tests backend (pytest + couverture)
   - Tests frontend (Jest + TypeScript)
   - Scans de sécurité (Trivy)
   - Tests d'intégration

2. **Backend** (`.github/workflows/backend-deploy.yml`)
   - Build Docker avec architecture x86_64
   - Push vers ECR
   - Mise à jour de la task definition ECS
   - Déploiement rolling avec health checks

3. **Frontend** (`.github/workflows/frontend-deploy.yml`)
   - Build de l'application React
   - Déploiement sur S3
   - Invalidation CloudFront
   - Tests de smoke

### Déclencheurs
- **Push sur `main`** : Déploiement automatique en production
- **Pull Request** : Tests automatiques uniquement

## 🔧 Configuration Manuelle

### Secrets GitHub Actions
```bash
# Clés d'accès AWS
AWS_ACCESS_KEY_ID=AKIAYDZ5Q34V7CIGNW3N
AWS_SECRET_ACCESS_KEY=***

# CloudFront
CLOUDFRONT_DISTRIBUTION_ID_PROD=E1I46WE3WLQ7A6

# Notifications (optionnel)
SLACK_WEBHOOK_URL=***
```

### Paramètres SSM (AWS)
```bash
/plan-charge/prod/database-url
/plan-charge/prod/jwt-secret
/plan-charge/prod/gryzzly-api-url
/plan-charge/prod/payfit-api-url
```

## 📦 Déploiement Manuel

### Script de Déploiement
```bash
# Déploiement complet
./scripts/deploy.sh

# Tests de production
./scripts/test-production.sh
```

### Commandes Individuelles

#### Backend
```bash
# Build et push de l'image
docker build --platform linux/amd64 -t plan-charge-backend backend/
aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin 557937909547.dkr.ecr.eu-west-3.amazonaws.com
docker tag plan-charge-backend:latest 557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend:latest
docker push 557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend:latest

# Mise à jour ECS
aws ecs register-task-definition --cli-input-json file://aws-deployment/task-definitions/production-task-definition.json
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --task-definition plan-charge-prod-backend
```

#### Frontend
```bash
# Build et déploiement
cd frontend
npm ci
npm run build
aws s3 sync dist/ s3://plan-charge-prod-frontend/ --delete
aws cloudfront create-invalidation --distribution-id E1I46WE3WLQ7A6 --paths "/*"
```

## 🔍 Monitoring et Vérification

### Health Checks
- **API** : `https://api.plan-de-charge.aws.nda-partners.com/health`
- **Frontend** : `https://plan-de-charge.aws.nda-partners.com`

### Logs
```bash
# Logs ECS
aws logs tail /ecs/plan-charge-prod-backend --follow

# Status du service
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend
```

### Métriques Clés
- **Temps de réponse API** : < 200ms
- **Uptime** : 99.9%
- **Health check ECS** : 30s interval, 3 retries, 60s start period

## 🛠️ Résolution de Problèmes

### Problèmes Courants

1. **Tasks ECS qui redémarrent**
   - Vérifier les logs : `aws logs tail /ecs/plan-charge-prod-backend`
   - Vérifier les health checks (startPeriod: 60s)
   - Vérifier les paramètres SSM

2. **Build Docker échoue**
   - Utiliser `--platform linux/amd64` pour la compatibilité AWS
   - Vérifier les dépendances backend

3. **Frontend inaccessible**
   - Vérifier l'invalidation CloudFront
   - Vérifier les politiques S3

### Rollback
```bash
# Rollback vers la version précédente
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --task-definition plan-charge-prod-backend:15
```

## 📋 Checklist de Déploiement

### Avant Déploiement
- [ ] Tests locaux passent
- [ ] Variables d'environnement correctes
- [ ] Paramètres SSM à jour
- [ ] Backup de la base de données

### Après Déploiement
- [ ] Health checks passent
- [ ] Tests de smoke OK
- [ ] Logs sans erreurs
- [ ] Métriques normales
- [ ] Fonctionnalités critiques testées

## 🔐 Sécurité

### Bonnes Pratiques
- Secrets stockés dans SSM Parameter Store
- Images Docker scannées avec Trivy
- HTTPS uniquement (CloudFront + ALB)
- Accès restreint aux ressources AWS
- Rotation régulière des clés

### Audit
- Logs d'accès ALB
- Logs d'application ECS
- Métriques CloudWatch
- Alerts sur les erreurs 5xx

## 📞 Support

- **Repository** : https://github.com/Dalavidhy/plan-charge-v11b
- **Environnement** : AWS eu-west-3
- **Monitoring** : CloudWatch + ALB logs