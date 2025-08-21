# Intervention : Réinjection des Matricules en Production

## 📅 Date : 21 Janvier 2025

## 🎯 Objectif
Réinjecter les matricules des collaborateurs dans la table `gryzzly_collaborators` suite à leur disparition après la synchronisation Payfit/Gryzzly.

## ⚠️ Impact
- **Criticité** : HAUTE - Les matricules sont essentiels pour le calcul des droits TR
- **Services impactés** : Module Titres Restaurant, synchronisation Payfit/Gryzzly
- **Utilisateurs concernés** : 15 collaborateurs NDA Partners
- **Durée estimée** : 10-15 minutes

## 📋 Prérequis

### 1. Accès nécessaires
- Accès AWS Console avec permissions RDS
- Accès SSM Session Manager pour le bastion
- Credentials PostgreSQL de production
- Accès CloudWatch Logs pour monitoring

### 2. Outils requis
- AWS CLI configuré
- PostgreSQL client (psql)
- Session Manager plugin

## 🔐 Étapes de sécurité

### 1. Créer un snapshot RDS avant intervention
```bash
aws rds create-db-snapshot \
    --db-instance-identifier plan-charge-db \
    --db-snapshot-identifier plan-charge-db-before-matricules-$(date +%Y%m%d-%H%M%S) \
    --region eu-west-3
```

### 2. Vérifier le snapshot
```bash
aws rds describe-db-snapshots \
    --db-snapshot-identifier plan-charge-db-before-matricules-* \
    --region eu-west-3 \
    --query 'DBSnapshots[0].Status'
```

## 🚀 Procédure d'intervention

### Étape 1 : Connexion au bastion AWS
```bash
# Récupérer l'ID de l'instance bastion
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=*bastion*" \
    --region eu-west-3 \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text

# Se connecter via SSM
aws ssm start-session \
    --target i-XXXXXXXXXXXXX \
    --region eu-west-3
```

### Étape 2 : Connexion à la base RDS depuis le bastion
```bash
# Variables d'environnement (à adapter)
export PGHOST=plan-charge-db.XXXXXXXXXXXX.eu-west-3.rds.amazonaws.com
export PGPORT=5432
export PGDATABASE=plancharge_db
export PGUSER=plancharge_user

# Connexion
psql -h $PGHOST -U $PGUSER -d $PGDATABASE -p $PGPORT
```

### Étape 3 : Exécuter le script SQL
```sql
-- Copier-coller le contenu de update_matricules_production.sql
-- Le script est en transaction, donc sécurisé
```

### Étape 4 : Validation des résultats
Avant de faire COMMIT, vérifier :
- ✅ Nombre de lignes mises à jour (devrait être 15)
- ✅ Pas de matricules en double
- ✅ Tous les matricules attendus sont présents
- ✅ Les emails correspondent bien aux matricules

### Étape 5 : Finalisation
```sql
-- Si tout est OK
COMMIT;

-- Si problème détecté
ROLLBACK;
```

## 🔍 Vérifications post-intervention

### 1. Vérifier dans l'application
```bash
# Tester l'endpoint des droits TR
curl https://api.plan-charge.nda-partners.com/api/v1/tr/rights/2025/01 \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Vérifier les logs CloudWatch
```bash
aws logs tail /aws/ecs/plan-charge-backend \
    --follow \
    --region eu-west-3 \
    --filter-pattern "matricule"
```

### 3. Requête de vérification SQL
```sql
-- Vérifier que les matricules sont bien présents
SELECT COUNT(*) as total,
       COUNT(matricule) as avec_matricule
FROM gryzzly_collaborators;

-- Lister les collaborateurs avec matricules
SELECT email, first_name, last_name, matricule
FROM gryzzly_collaborators
WHERE matricule IS NOT NULL
ORDER BY CAST(matricule AS INTEGER);
```

## 📊 Matricules à réinjecter

| Email | Matricule | Nom |
|-------|-----------|-----|
| david.alhyar@nda-partners.com | 1 | David Al Hyar |
| vincent.mirzaian@nda-partners.com | 2 | Vincent Mirzaian |
| maria.zavlyanova@nda-partners.com | 3 | Maria Zavlyanova |
| tristan.lepennec@nda-partners.com | 5 | Tristan Le Pennec |
| elmehdi.elouardi@nda-partners.com | 7 | Mohammed elmehdi Elouardi |
| maxime.rodrigues@nda-partners.com | 8 | Maxime Rodrigues |
| efflam.kervoas@nda-partners.com | 9 | Efflam Kervoas |
| sami.benouattaf@nda-partners.com | 11 | Sami Benouattaf |
| alexandre.linck@nda-partners.com | 12 | Alexandre Linck |
| nail.ferroukhi@nda-partners.com | 14 | Naïl Ferroukhi |
| soukaina.elkourdi@nda-partners.com | 15 | Soukaïna El Kourdi |
| malek.attia@nda-partners.com | 16 | Malek Attia |
| thomas.deruy@nda-partners.com | 17 | Thomas Deruy |
| valerie.patureau@nda-partners.com | 19 | Valérie Patureau |
| berenger.de-kerever@nda-partners.com | 112 | Bérenger Guillotou de Keréver |

## 🔄 Rollback en cas de problème

### Option 1 : ROLLBACK dans la transaction
Si le script n'a pas encore été committé :
```sql
ROLLBACK;
```

### Option 2 : Restauration depuis le backup
Si besoin de restaurer depuis la table temporaire (dans la même session) :
```sql
UPDATE gryzzly_collaborators gc
SET matricule = gcb.matricule
FROM gryzzly_collaborators_backup_20250121 gcb
WHERE gc.id = gcb.id;
```

### Option 3 : Restauration depuis le snapshot RDS
En dernier recours :
```bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier plan-charge-db-restored \
    --db-snapshot-identifier plan-charge-db-before-matricules-XXXXXX \
    --region eu-west-3
```

## 📝 Notes importantes

1. **Transaction obligatoire** : Le script utilise une transaction pour permettre un rollback facile
2. **Backup temporaire** : Une table temporaire est créée pour pouvoir revenir en arrière
3. **Vérifications automatiques** : Le script vérifie les doublons et les matricules manquants
4. **Logs détaillés** : Utilisation de RAISE NOTICE pour tracer l'exécution
5. **Updated_at** : Le champ est mis à jour pour traçabilité

## 🚨 Contacts en cas d'urgence

- **Responsable technique** : David Al Hyar
- **AWS Support** : Via console AWS Support Center
- **Monitoring** : CloudWatch Dashboard plan-charge-production

## ✅ Checklist finale

- [ ] Snapshot RDS créé et vérifié
- [ ] Script SQL préparé et relu
- [ ] Connexion bastion testée
- [ ] Connexion PostgreSQL établie
- [ ] Script exécuté avec succès
- [ ] Résultats vérifiés avant COMMIT
- [ ] COMMIT effectué
- [ ] Tests applicatifs réalisés
- [ ] Logs CloudWatch vérifiés
- [ ] Documentation mise à jour