# Guide de Déploiement AWS - Plan de Charge

## 📋 Architecture de Production

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  CloudFront │────▶│     ALB      │────▶│  ECS Fargate │
│     CDN     │     │ Load Balancer│     │   Services   │
└─────────────┘     └──────────────┘     └──────────────┘
                             │                    │
                             ▼                    ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   Frontend   │     │   Backend    │
                    │  Target Group│     │ Target Group │
                    └──────────────┘     └──────────────┘
```

## 🚀 Composants AWS

### ECS Fargate

**Cluster** : `plan-charge-prod-cluster`

**Services** :
- `plan-charge-prod-frontend` : Service frontend React
- `plan-charge-prod-backend` : Service backend FastAPI

**Configuration recommandée** :
```yaml
Frontend:
  CPU: 0.5 vCPU
  Memory: 1 GB
  Desired Count: 2
  Health Check: /
  Port: 80

Backend:
  CPU: 1 vCPU
  Memory: 2 GB
  Desired Count: 2
  Health Check: /health
  Port: 8000
```

### Application Load Balancer (ALB)

**Nom** : `plan-charge-prod-alb`

**Listener Rules** (ordre important !) :
1. **Priority 10** : `/health` → Backend Target Group
2. **Priority 50** : `/api/*` → Backend Target Group
3. **Priority 100** : `/docs` → Backend Target Group
4. **Priority 200** : `/robots.txt` → Frontend Target Group
5. **Default** : `*` → Frontend Target Group

**Target Groups** :
- `plan-charge-prod-frontend-tg` : Port 80, Protocol HTTP
- `plan-charge-prod-backend-tg` : Port 8000, Protocol HTTP

**Health Checks** :
```yaml
Frontend:
  Path: /
  Interval: 30s
  Timeout: 5s
  Healthy Threshold: 2
  Unhealthy Threshold: 3

Backend:
  Path: /health
  Interval: 30s
  Timeout: 5s
  Healthy Threshold: 2
  Unhealthy Threshold: 3
```

### CloudFront Distribution

**Distribution ID** : `E3U93II4ZE9MCI`
**Domain** : `plan-de-charge.aws.nda-partners.com`

**Cache Behaviors** :
```yaml
/api/*:
  Origin: ALB
  TTL: 0 (no cache)
  Forward Headers: ALL
  Forward Cookies: ALL
  Forward Query Strings: true

/docs*:
  Origin: ALB
  TTL: 3600
  Compress: true

/assets/*:
  Origin: ALB
  TTL: 2592000 (30 days)
  Compress: true

Default (*):
  Origin: ALB
  TTL: 86400 (1 day)
  Compress: true
```

**⚠️ IMPORTANT** : Ne PAS configurer de Custom Error Responses pour éviter que les erreurs API soient remplacées par index.html

### RDS PostgreSQL

**Instance** : `plan-charge-prod-db`
**Engine** : PostgreSQL 14
**Size** : db.t3.medium
**Storage** : 100 GB SSD
**Backup** : 7 jours de rétention

### ElastiCache Redis

**Cluster** : `plan-charge-prod-redis`
**Node Type** : cache.t3.micro
**Engine** : Redis 7

### ECR (Elastic Container Registry)

**Repositories** :
- `plan-charge/frontend`
- `plan-charge/backend`

## 📦 Processus de Déploiement

### 1. Build et Push des Images Docker

```bash
# Login ECR
aws ecr get-login-password --region eu-west-3 | \
  docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.eu-west-3.amazonaws.com

# Build Backend
cd backend
docker build -t plan-charge-backend .
docker tag plan-charge-backend:latest [ACCOUNT_ID].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/backend:latest
docker push [ACCOUNT_ID].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/backend:latest

# Build Frontend
cd ../frontend
docker build -t plan-charge-frontend .
docker tag plan-charge-frontend:latest [ACCOUNT_ID].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/frontend:latest
docker push [ACCOUNT_ID].dkr.ecr.eu-west-3.amazonaws.com/plan-charge/frontend:latest
```

### 2. Update Task Definitions

```bash
# Register new task definition
aws ecs register-task-definition --cli-input-json file://task-definition-backend.json
aws ecs register-task-definition --cli-input-json file://task-definition-frontend.json
```

### 3. Update Services

```bash
# Update Backend Service
aws ecs update-service \
  --cluster plan-charge-prod-cluster \
  --service plan-charge-prod-backend \
  --force-new-deployment

# Update Frontend Service
aws ecs update-service \
  --cluster plan-charge-prod-cluster \
  --service plan-charge-prod-frontend \
  --force-new-deployment
```

### 4. Monitor Deployment

```bash
# Watch service status
aws ecs wait services-stable \
  --cluster plan-charge-prod-cluster \
  --services plan-charge-prod-backend plan-charge-prod-frontend

# Check running tasks
aws ecs list-tasks --cluster plan-charge-prod-cluster --service-name plan-charge-prod-backend

# View logs
aws logs tail /ecs/plan-charge-prod --follow
```

### 5. Invalidate CloudFront Cache

```bash
# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id E3U93II4ZE9MCI \
  --paths "/*"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id E3U93II4ZE9MCI \
  --id [INVALIDATION_ID]
```

## 🔧 Variables d'Environnement

### Backend (ECS Task Definition)

```json
{
  "environment": [
    {"name": "DATABASE_URL", "value": "postgresql://user:pass@rds-endpoint:5432/dbname"},
    {"name": "REDIS_URL", "value": "redis://redis-endpoint:6379/0"},
    {"name": "JWT_SECRET_KEY", "value": "SECRET_FROM_SECRETS_MANAGER"},
    {"name": "ENVIRONMENT", "value": "production"},
    {"name": "CORS_ORIGINS", "value": "https://plan-de-charge.aws.nda-partners.com"},
    {"name": "AZURE_CLIENT_ID", "value": "FROM_SECRETS_MANAGER"},
    {"name": "AZURE_CLIENT_SECRET", "value": "FROM_SECRETS_MANAGER"},
    {"name": "AZURE_TENANT_ID", "value": "FROM_SECRETS_MANAGER"}
  ]
}
```

### Frontend (Runtime Config)

Le frontend utilise un fichier `config.js` chargé au runtime :

```javascript
window.__RUNTIME_CONFIG__ = {
  API_URL: 'https://plan-de-charge.aws.nda-partners.com/api/v1',
  AZURE_CLIENT_ID: 'your-client-id',
  AZURE_TENANT_ID: 'your-tenant-id',
  AZURE_REDIRECT_URI: 'https://plan-de-charge.aws.nda-partners.com'
};
```

## 🔒 Sécurité

### Security Groups

**ALB Security Group** :
- Inbound : 80 (HTTP) from 0.0.0.0/0
- Inbound : 443 (HTTPS) from 0.0.0.0/0
- Outbound : All traffic

**ECS Tasks Security Group** :
- Inbound : 8000 from ALB Security Group (backend)
- Inbound : 80 from ALB Security Group (frontend)
- Outbound : All traffic

**RDS Security Group** :
- Inbound : 5432 from ECS Tasks Security Group
- Outbound : None

**Redis Security Group** :
- Inbound : 6379 from ECS Tasks Security Group
- Outbound : None

### Secrets Management

Utiliser AWS Secrets Manager pour :
- JWT_SECRET_KEY
- Database credentials
- Azure AD credentials
- API keys externes

```bash
# Créer un secret
aws secretsmanager create-secret \
  --name plan-charge/prod/jwt-secret \
  --secret-string "your-secret-key"

# Référencer dans Task Definition
{
  "secrets": [
    {
      "name": "JWT_SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:plan-charge/prod/jwt-secret"
    }
  ]
}
```

## 📊 Monitoring

### CloudWatch Alarms

Configurer des alarmes pour :
- ECS Service : CPU > 80%, Memory > 80%
- ALB : Target Unhealthy Count > 0
- ALB : HTTP 5xx errors > 10/min
- RDS : CPU > 80%, Storage < 10GB
- Redis : Memory > 80%, Evictions > 0

### CloudWatch Logs

Log Groups :
- `/ecs/plan-charge-prod` : Logs des containers ECS
- `/aws/rds/instance/plan-charge-prod-db` : Logs PostgreSQL
- `/aws/elasticache/redis/plan-charge-prod` : Logs Redis

### X-Ray Tracing

Activer X-Ray pour tracer les requêtes :
```python
# backend/app/main.py
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

app.add_middleware(XRayMiddleware, recorder=xray_recorder)
```

## 🚨 Rollback Procedure

En cas de problème après déploiement :

1. **Rollback Task Definition** :
```bash
# Lister les révisions précédentes
aws ecs list-task-definitions --family-prefix plan-charge-backend

# Update service avec ancienne révision
aws ecs update-service \
  --cluster plan-charge-prod-cluster \
  --service plan-charge-prod-backend \
  --task-definition plan-charge-backend:PREVIOUS_REVISION
```

2. **Rollback Database** :
```bash
# Si migrations appliquées
docker compose exec backend alembic downgrade -1
```

3. **Invalidate CloudFront** :
```bash
aws cloudfront create-invalidation --distribution-id E3U93II4ZE9MCI --paths "/*"
```

## 📝 Checklist de Déploiement

Avant le déploiement :
- [ ] Tests passent en local
- [ ] Variables d'environnement vérifiées
- [ ] Backup de la base de données effectué
- [ ] Task definitions mises à jour
- [ ] Security groups vérifiés

Pendant le déploiement :
- [ ] Images Docker construites et poussées
- [ ] Services ECS mis à jour
- [ ] Migrations de base de données appliquées
- [ ] Health checks verts
- [ ] Logs sans erreurs

Après le déploiement :
- [ ] Tests de smoke en production
- [ ] Monitoring des métriques
- [ ] CloudFront invalidé si nécessaire
- [ ] Documentation mise à jour

## 🆘 Support et Contacts

- **AWS Support** : Via console AWS
- **On-call** : Équipe DevOps
- **Escalation** : Lead technique

## 📚 Ressources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [ALB Documentation](https://docs.aws.amazon.com/elasticloadbalancing/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Plan Charge Wiki Interne](internal-wiki-link)