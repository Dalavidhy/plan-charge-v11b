# 🚀 Connexion RDS Production - Intervention Matricules

## ✅ Snapshot de sécurité créé
- **Nom**: `plan-charge-prod-db-before-matricules-20250821-110342`
- **Statut**: DISPONIBLE ✅
- **Date**: 21/08/2025 11:03

## 📡 Informations de connexion

### Base de données RDS
- **Endpoint**: `plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com`
- **Port**: `5432`
- **Database**: `plancharge`
- **Username**: `plancharge`

## 🔐 Options de connexion

### Option 1: Via ECS Task (recommandé)

Créer une tâche ECS one-shot pour exécuter le script SQL :

```bash
# Créer une tâche ECS avec psql client
aws ecs run-task \
    --cluster plan-charge-cluster \
    --task-definition plan-charge-db-migration \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
    --region eu-west-3
```

### Option 2: Via Cloud9 ou AWS CloudShell

1. Ouvrir AWS CloudShell depuis la console AWS
2. Installer PostgreSQL client :
```bash
sudo yum install -y postgresql15
```

3. Se connecter à RDS :
```bash
export PGPASSWORD='[votre_mot_de_passe]'
psql -h plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com \
     -U plancharge \
     -d plancharge \
     -p 5432
```

### Option 3: Via un pod temporaire

Si vous avez un cluster EKS, créer un pod temporaire :

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: psql-client
spec:
  containers:
  - name: psql
    image: postgres:14
    command: ["sleep", "3600"]
```

## 📝 Script SQL à exécuter

Une fois connecté, exécuter le contenu du fichier :
`/backend/scripts/update_matricules_production.sql`

### Commandes SQL importantes :

```sql
-- Démarrer la transaction
BEGIN;

-- Exécuter le script complet...
-- (copier-coller le contenu de update_matricules_production.sql)

-- Vérifier les résultats avant de valider
SELECT email, matricule FROM gryzzly_collaborators 
WHERE matricule IS NOT NULL 
ORDER BY CAST(matricule AS INTEGER);

-- Si tout est OK
COMMIT;

-- Si problème
ROLLBACK;
```

## 🔍 Vérification post-intervention

### 1. Vérifier les logs CloudWatch
```bash
aws logs tail /aws/ecs/plan-charge-backend \
    --follow \
    --region eu-west-3 \
    --filter-pattern "matricule"
```

### 2. Tester l'API des droits TR
```bash
# Récupérer un token d'authentification d'abord
# Puis tester l'endpoint
curl -X GET https://api.plan-charge.nda-partners.com/api/v1/tr/rights/2025/01 \
     -H "Authorization: Bearer [TOKEN]"
```

### 3. Vérifier dans l'interface web
Accéder à : https://plan-charge.nda-partners.com/droits-tr

## 🔄 Rollback si nécessaire

### Restaurer depuis le snapshot
```bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier plan-charge-prod-db-restored \
    --db-snapshot-identifier plan-charge-prod-db-before-matricules-20250821-110342 \
    --region eu-west-3
```

## ⚠️ Notes importantes

1. **Le snapshot de sécurité est créé** : `plan-charge-prod-db-before-matricules-20250821-110342`
2. **Transaction SQL obligatoire** : Le script utilise BEGIN/COMMIT pour permettre un rollback
3. **15 matricules à mettre à jour** : Vérifier que tous sont bien insérés
4. **Pas de bastion détecté** : Utiliser ECS Task ou CloudShell pour la connexion

## 📞 Support
En cas de problème, vérifier :
- CloudWatch Logs : `/aws/ecs/plan-charge-backend`
- RDS Metrics dans CloudWatch
- Application Logs dans l'interface