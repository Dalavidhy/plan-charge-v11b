# Guide de Dépannage - Plan de Charge

Ce document recense les problèmes courants rencontrés et leurs solutions.

## 🔴 Problèmes Résolus en Production

### 1. Backend Docker - Container qui s'arrête après les migrations

**Symptôme** : 
- Erreur 503 Service Unavailable sur tous les endpoints API
- Le container backend démarre, exécute les migrations puis s'arrête
- ECS montre 0 tâches en cours d'exécution

**Cause** :
Le Dockerfile du backend n'avait pas d'instruction `CMD`, donc le container s'arrêtait après l'exécution du script `docker-entrypoint.sh`.

**Solution** :
Ajouter l'instruction CMD dans le Dockerfile :
```dockerfile
# backend/Dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Commandes de diagnostic** :
```bash
# Vérifier l'état du service ECS
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend

# Voir les logs du container
aws logs tail /ecs/plan-charge-prod --since 5m

# Vérifier pourquoi les tâches s'arrêtent
aws ecs list-tasks --cluster plan-charge-prod-cluster --service-name plan-charge-prod-backend --desired-status STOPPED
```

### 2. ALB - Mauvais routage des requêtes API

**Symptôme** :
- Erreur 503 sur `/api/v1/*` même avec le backend en marche
- Les requêtes API retournent la page HTML du frontend

**Cause** :
L'Application Load Balancer n'avait pas de règles de routage pour diriger les requêtes `/api/*` vers le backend. Toutes les requêtes allaient au frontend par défaut.

**Solution** :
Créer des règles de routage dans l'ALB :
```bash
# Règle pour /api/* (priorité 50)
aws elbv2 create-rule \
  --listener-arn [LISTENER_ARN] \
  --priority 50 \
  --conditions Field=path-pattern,Values="/api/*" \
  --actions Type=forward,TargetGroupArn=[BACKEND_TARGET_GROUP_ARN]

# Règle pour /health (priorité 10)
aws elbv2 create-rule \
  --listener-arn [LISTENER_ARN] \
  --priority 10 \
  --conditions Field=path-pattern,Values="/health" \
  --actions Type=forward,TargetGroupArn=[BACKEND_TARGET_GROUP_ARN]
```

**Commandes de diagnostic** :
```bash
# Lister les règles de l'ALB
aws elbv2 describe-rules --listener-arn [LISTENER_ARN]

# Vérifier la santé des targets
aws elbv2 describe-target-health --target-group-arn [TARGET_GROUP_ARN]

# Tester directement sur l'ALB
curl http://[ALB_DNS]/api/v1/health
```

### 3. CloudFront - Custom Error Pages interceptent les erreurs API

**Symptôme** :
- Les endpoints API retournent la page HTML au lieu des erreurs JSON
- Les erreurs 403 (Not authenticated) sont remplacées par index.html
- Les erreurs 404 sont également remplacées par index.html

**Cause** :
CloudFront était configuré avec des "Custom Error Responses" qui transformaient les erreurs 403 et 404 en réponse 200 avec le contenu de index.html. C'est une configuration classique pour les SPA, mais elle ne doit pas s'appliquer aux routes API.

**Solution** :
Supprimer les Custom Error Responses de CloudFront :
```bash
# Récupérer la configuration actuelle
aws cloudfront get-distribution-config --id [DISTRIBUTION_ID] > cf-config.json

# Modifier le fichier pour supprimer CustomErrorResponses
jq '.DistributionConfig | .CustomErrorResponses = {"Quantity": 0, "Items": []}' cf-config.json > cf-updated.json

# Appliquer la nouvelle configuration
aws cloudfront update-distribution \
  --id [DISTRIBUTION_ID] \
  --distribution-config file://cf-updated.json \
  --if-match [ETAG]
```

**Configuration correcte** :
- Cache behavior pour `/api/*` avec TTL=0 (pas de cache)
- Pas de Custom Error Responses globales
- Les erreurs API doivent être transmises telles quelles

**Commandes de diagnostic** :
```bash
# Vérifier la configuration CloudFront
aws cloudfront get-distribution-config --id [DISTRIBUTION_ID]

# Créer une invalidation de cache
aws cloudfront create-invalidation --distribution-id [DISTRIBUTION_ID] --paths "/*"

# Tester avec curl
curl -I https://[DOMAIN]/api/v1/auth/me
```

## 🔧 Problèmes Courants

### Cache Navigateur

**Symptôme** : Les changements ne sont pas visibles même après correction

**Solution** :
- Hard refresh : `Ctrl+Shift+R` (Windows/Linux) ou `Cmd+Shift+R` (Mac)
- Ouvrir les DevTools > Network > cocher "Disable cache"
- Tester dans une fenêtre de navigation privée

### Service Worker

**Symptôme** : Les requêtes API sont interceptées ou cachées

**Solution** :
- DevTools > Application > Service Workers
- Cliquer sur "Unregister" pour désactiver temporairement
- Vider le cache du Service Worker

## 📊 Commandes Utiles de Diagnostic

### AWS ECS
```bash
# État des services
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend

# Logs des containers
aws logs tail /ecs/plan-charge-prod --since 10m --follow

# Tâches en cours
aws ecs list-tasks --cluster plan-charge-prod-cluster --service-name plan-charge-prod-backend
```

### AWS ALB
```bash
# Santé des targets
aws elbv2 describe-target-health --target-group-arn [TG_ARN]

# Règles de routage
aws elbv2 describe-rules --listener-arn [LISTENER_ARN]
```

### AWS CloudFront
```bash
# Status de distribution
aws cloudfront get-distribution --id [DIST_ID] --query "Distribution.Status"

# Créer invalidation
aws cloudfront create-invalidation --distribution-id [DIST_ID] --paths "/api/*"

# Vérifier invalidation
aws cloudfront get-invalidation --distribution-id [DIST_ID] --id [INV_ID]
```

### Docker Local
```bash
# Reconstruire et redémarrer
docker compose down && docker compose up --build -d

# Voir les logs
docker compose logs -f backend

# Accéder au container
docker compose exec backend bash

# Vérifier la santé
curl http://localhost:8000/health
```

## 🎯 Checklist de Déploiement

Avant chaque déploiement, vérifier :

1. ✅ Le Dockerfile backend contient bien l'instruction CMD
2. ✅ Les règles ALB sont configurées pour `/api/*` et `/health`
3. ✅ CloudFront n'a pas de Custom Error Responses
4. ✅ Les variables d'environnement sont correctement définies
5. ✅ Les health checks sont configurés sur `/health`
6. ✅ Au moins 2 tâches backend sont en cours d'exécution
7. ✅ Les targets sont healthy dans l'ALB
8. ✅ CloudFront cache behavior pour `/api/*` avec TTL=0

## 📝 Notes Importantes

- **Toujours tester** les endpoints API avec `curl` pour éviter les problèmes de cache navigateur
- **Attendre 5-10 minutes** après une modification CloudFront pour la propagation complète
- **Vérifier les logs** ECS pour diagnostiquer les problèmes de démarrage
- **Les erreurs 403** sur les endpoints authentifiés sont normales sans token