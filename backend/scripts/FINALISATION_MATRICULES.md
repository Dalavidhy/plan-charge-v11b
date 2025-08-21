# 🚀 Finalisation de la mise à jour des matricules

## ✅ Actions réalisées

### 1. Snapshot de sécurité créé
- **Nom** : `plan-charge-prod-db-before-matricules-20250821-110342`
- **Statut** : DISPONIBLE ✅
- **Date** : 21/08/2025 11:03
- Backup complet de la base avant toute intervention

### 2. Scripts préparés
- ✅ `update_matricules_production.sql` - Script SQL sécurisé avec transaction
- ✅ `execute_matricules_update.py` - Script Python pour exécution automatique
- ✅ `execute_sql_direct.sh` - Script bash avec psql
- ✅ Documentation complète de l'intervention

### 3. PostgreSQL client installé
- ✅ PostgreSQL 14 installé via Homebrew
- Disponible dans : `/opt/homebrew/opt/postgresql@14/bin/psql`

## 🔐 Finalisation manuelle nécessaire

La connexion directe depuis votre machine locale vers RDS est bloquée par les règles de sécurité AWS. 

### Option 1 : Via AWS CloudShell (Recommandé)

1. **Ouvrez AWS CloudShell** dans la console AWS
   - Région : eu-west-3 (Paris)
   - https://eu-west-3.console.aws.amazon.com/cloudshell/

2. **Installez psql** :
```bash
sudo yum install -y postgresql15
```

3. **Récupérez le mot de passe** :
```bash
export PGPASSWORD=$(aws ssm get-parameter \
    --name "/plan-charge/prod/db-password" \
    --with-decryption \
    --region eu-west-3 \
    --query 'Parameter.Value' \
    --output text)
```

4. **Connectez-vous à la base** :
```bash
psql -h plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com \
     -U plancharge \
     -d plancharge \
     -p 5432
```

5. **Exécutez le script SQL** :
Copiez-collez le contenu de `/backend/scripts/update_matricules_production.sql`

### Option 2 : Via un container ECS temporaire

```bash
# Créer un container avec psql
aws ecs run-task \
    --cluster plan-charge-prod-cluster \
    --task-definition plan-charge-backend \
    --overrides '{
        "containerOverrides": [{
            "name": "backend",
            "command": ["sh", "-c", "apt-get update && apt-get install -y postgresql-client && psql $DATABASE_URL -f /tmp/update.sql"]
        }]
    }' \
    --network-configuration '{
        "awsvpcConfiguration": {
            "subnets": ["subnet-04e83c8c930637597", "subnet-075ba669585873bb8"],
            "securityGroups": ["sg-0a6cd0e7920726c46"],
            "assignPublicIp": "DISABLED"
        }
    }' \
    --region eu-west-3
```

## 📊 Vérification après exécution

### 1. Dans PostgreSQL
```sql
-- Vérifier les matricules
SELECT COUNT(*) as total,
       COUNT(matricule) as avec_matricule
FROM gryzzly_collaborators;

-- Lister les collaborateurs avec matricules
SELECT matricule, email, first_name || ' ' || last_name as nom
FROM gryzzly_collaborators
WHERE matricule IS NOT NULL
ORDER BY CAST(matricule AS INTEGER);
```

Résultat attendu : 15 collaborateurs avec matricules

### 2. Dans l'application web
- Accéder à : https://plan-charge.nda-partners.com/droits-tr
- Vérifier que les collaborateurs éligibles apparaissent

### 3. Via l'API (avec authentification)
```bash
# Se connecter d'abord pour obtenir un token
# Puis tester
curl -X GET https://api.plan-charge.nda-partners.com/api/v1/tr/rights/2025/01 \
     -H "Authorization: Bearer [TOKEN]"
```

## 📋 Matricules à vérifier

| Matricule | Email | Nom |
|-----------|-------|-----|
| 1 | david.alhyar@nda-partners.com | David Al Hyar |
| 2 | vincent.mirzaian@nda-partners.com | Vincent Mirzaian |
| 3 | maria.zavlyanova@nda-partners.com | Maria Zavlyanova |
| 5 | tristan.lepennec@nda-partners.com | Tristan Le Pennec |
| 7 | elmehdi.elouardi@nda-partners.com | Mohammed elmehdi Elouardi |
| 8 | maxime.rodrigues@nda-partners.com | Maxime Rodrigues |
| 9 | efflam.kervoas@nda-partners.com | Efflam Kervoas |
| 11 | sami.benouattaf@nda-partners.com | Sami Benouattaf |
| 12 | alexandre.linck@nda-partners.com | Alexandre Linck |
| 14 | nail.ferroukhi@nda-partners.com | Naïl Ferroukhi |
| 15 | soukaina.elkourdi@nda-partners.com | Soukaïna El Kourdi |
| 16 | malek.attia@nda-partners.com | Malek Attia |
| 17 | thomas.deruy@nda-partners.com | Thomas Deruy |
| 19 | valerie.patureau@nda-partners.com | Valérie Patureau |
| 112 | berenger.de-kerever@nda-partners.com | Bérenger Guillotou de Keréver |

## ⚠️ Important

- **Snapshot de sécurité disponible** pour rollback si nécessaire
- **Script SQL avec transaction** : permet ROLLBACK si problème
- **15 matricules** doivent être mis à jour
- **Pas de doublons** autorisés (vérification automatique dans le script)