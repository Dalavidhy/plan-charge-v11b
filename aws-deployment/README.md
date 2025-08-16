# 🚀 Déploiement AWS - Plan de Charge

Infrastructure haute disponibilité pour Plan de Charge dans la région **eu-west-3 (Paris)**.

## 🏗️ Architecture

```
Internet → Route53 → CloudFront → ALB → ECS Fargate
                                   ↓
                              RDS PostgreSQL + ElastiCache Redis
```

### Services AWS utilisés

- **ECS Fargate** : Containers sans serveur (backend, frontend, celery)
- **RDS PostgreSQL** : Base de données managée (db.t3.micro)
- **ElastiCache Redis** : Cache et broker Celery (cache.t3.micro)
- **Application Load Balancer** : Répartition de charge avec SSL
- **CloudFront** : CDN global pour performance
- **Route53** : DNS et health checks
- **VPC** : Réseau privé sécurisé (2 AZ)
- **Parameter Store** : Gestion des secrets

## 💰 Coûts Estimés

| Service | Configuration | Coût/mois |
|---------|---------------|-----------|
| **ECS Fargate** | 5 tâches (512MB-1GB) | ~40€ |
| **RDS PostgreSQL** | db.t3.micro | ~18€ |
| **ElastiCache Redis** | cache.t3.micro | ~15€ |
| **ALB** | Standard | ~25€ |
| **CloudFront** | 10GB transfer | ~5€ |
| **Route53** | Zone + queries | ~2€ |
| **NAT Gateway** | Single NAT | ~50€ |
| **Total** | | **~155€/mois** |

### 💡 Optimisations possibles
- Sans NAT Gateway (VPC endpoints) : **~105€/mois**
- Aurora Serverless v2 : **~95€/mois**

## 🚀 Déploiement Rapide

### 1. Prérequis

```bash
# Installer les outils nécessaires
brew install terraform awscli

# Configurer AWS CLI
aws configure
```

### 2. Déploiement complet

```bash
# 1. Configurer Route53 et créer les certificats SSL
./aws-deployment/scripts/01-setup-route53.sh

# 2. Créer les repositories ECR
./aws-deployment/scripts/02-create-ecr.sh

# 3. Builder et pusher les images Docker
./aws-deployment/scripts/03-build-and-push.sh

# 4. Déployer l'infrastructure complète
./aws-deployment/scripts/04-deploy-infrastructure.sh

# 5. Tester le déploiement
./aws-deployment/scripts/05-test-deployment.sh
```

## 📋 Configuration DNS

### Chez OVH (nda-partners.com)

Ajouter ces NS records pour `aws.nda-partners.com` :
```
aws.nda-partners.com    NS    ns-1651.awsdns-14.co.uk
aws.nda-partners.com    NS    ns-661.awsdns-18.net
aws.nda-partners.com    NS    ns-284.awsdns-35.com
aws.nda-partners.com    NS    ns-1261.awsdns-29.org
```

### Route53 (AWS)

Automatiquement configuré par Terraform :
- `plan-de-charge.aws.nda-partners.com` → CloudFront
- `alb.aws.nda-partners.com` → ALB (debug)

## 🔐 Secrets Configuration

Secrets gérés dans AWS Parameter Store :

```bash
# Secrets à configurer manuellement
aws ssm put-parameter --name "/plan-charge/prod/azure-tenant-id" --value "your-tenant-id"
aws ssm put-parameter --name "/plan-charge/prod/azure-client-secret" --value "your-secret" --type SecureString
aws ssm put-parameter --name "/plan-charge/prod/payfit-api-key" --value "your-key" --type SecureString
aws ssm put-parameter --name "/plan-charge/prod/gryzzly-api-key" --value "your-key" --type SecureString
```

## 🔧 Opérations

### Mise à jour des images

```bash
# Builder et pusher nouvelles images
./aws-deployment/scripts/03-build-and-push.sh

# Redéployer les services ECS
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --force-new-deployment
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-frontend --force-new-deployment
```

### Monitoring

```bash
# Logs en temps réel
aws logs tail /ecs/plan-charge-prod --follow

# État des services
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend plan-charge-prod-frontend

# Métriques CloudWatch
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization
```

### Scaling

```bash
# Scaler le backend
aws ecs update-service --cluster plan-charge-prod-cluster --service plan-charge-prod-backend --desired-count 4

# Auto-scaling configuré automatiquement (CPU > 70%, Memory > 80%)
```

## 🌐 URLs d'accès

- **Application** : https://plan-de-charge.aws.nda-partners.com
- **API** : https://plan-de-charge.aws.nda-partners.com/api/v1
- **Documentation** : https://plan-de-charge.aws.nda-partners.com/docs
- **ALB Direct** : https://alb.aws.nda-partners.com (debug)

## 🛡️ Sécurité

### Réseau
- VPC privé avec subnets publics/privés
- Security Groups restrictifs
- SSL/TLS partout (CloudFront + ALB)

### Données
- RDS chiffré at-rest
- Parameter Store pour secrets
- Backup automatique RDS (7 jours)

### Accès
- IAM roles avec permissions minimales
- Pas d'accès SSH direct aux containers
- ECS Exec pour debugging sécurisé

## 📊 Monitoring

### CloudWatch
- Logs centralisés ECS
- Métriques de performance
- Health checks Route53

### Alertes
- CPU/Memory > seuils
- Erreurs HTTP 5xx
- Health check failures

## 🚨 Troubleshooting

### Application inaccessible
```bash
# Vérifier DNS
dig plan-de-charge.aws.nda-partners.com

# Vérifier CloudFront
curl -I https://plan-de-charge.aws.nda-partners.com

# Vérifier ALB directement
curl -I https://alb.aws.nda-partners.com
```

### API ne répond pas
```bash
# Logs backend
aws logs tail /ecs/plan-charge-prod --filter="backend" --follow

# État du service
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend
```

### Base de données
```bash
# Connection test depuis ECS
aws ecs execute-command --cluster plan-charge-prod-cluster --task <task-id> --container backend --command "psql $DATABASE_URL -c 'SELECT 1'"
```

## 📁 Structure des fichiers

```
aws-deployment/
├── scripts/
│   ├── 01-setup-route53.sh      # Configuration DNS et SSL
│   ├── 02-create-ecr.sh         # Repositories Docker
│   ├── 03-build-and-push.sh     # Build et push images
│   ├── 04-deploy-infrastructure.sh # Déploiement Terraform
│   └── 05-test-deployment.sh    # Tests complets
├── terraform/
│   ├── main.tf                  # Configuration principale
│   ├── variables.tf             # Variables
│   ├── vpc.tf                   # Réseau
│   ├── rds.tf                   # Base de données
│   ├── elasticache.tf           # Redis
│   ├── ecs.tf                   # Task definitions
│   ├── ecs-services.tf          # Services ECS
│   ├── alb.tf                   # Load Balancer
│   ├── cloudfront.tf            # CDN
│   ├── route53.tf               # DNS
│   ├── secrets.tf               # Parameter Store
│   └── outputs.tf               # Outputs
├── docker/
│   ├── backend/Dockerfile.prod  # Backend optimisé
│   └── frontend/
│       ├── Dockerfile.simple    # Frontend optimisé
│       ├── nginx.conf           # Configuration Nginx
│       └── default.conf         # Virtual host
└── dns-info.env                 # Variables d'environnement
```

## 🎯 Prochaines étapes

1. **Configuration Azure AD** avec les nouvelles URLs
2. **Tests de charge** pour valider la performance
3. **Monitoring avancé** (APM, métriques métier)
4. **CI/CD** avec GitHub Actions
5. **Backup/Restore** procédures
6. **Disaster Recovery** plan

---

**Support** : Déploiement géré par Terraform, logs dans CloudWatch, monitoring Route53.
**Coût** : ~155€/mois pour une architecture production-ready haute disponibilité.