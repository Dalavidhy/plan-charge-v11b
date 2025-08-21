# 🔄 Solution temporaire - Matricules TR

**Date**: 21/08/2025  
**Status**: Solution temporaire active  
**Version service**: plan-charge-prod-backend:5 (stable)

## 🎯 Situation actuelle

### Problèmes identifiés
1. ✅ **Code corrigé** - Les fixes timezone et matricules sont développés et testés
2. ❌ **Déploiement bloqué** - Les versions avec fixes (12,13,14) échouent au démarrage
3. ✅ **Service opérationnel** - Version 5 stable en production (2/2 tâches)
4. ⚠️ **Perte matricules** - Les synchronisations Gryzzly effacent encore les matricules

### Impact utilisateur
- ✅ Application fonctionnelle 
- ⚠️ Droits TR indisponibles temporairement après chaque sync Gryzzly
- 🔄 Réinjection manuelle nécessaire après chaque synchronisation

## 🛠️ Solution temporaire mise en place

### 1. Réinjection automatisée des matricules
Script SQL disponible : `/tmp/reinject_matricules_production.sql`

**Commande rapide** :
```bash
DATABASE_URL=$(aws ssm get-parameter --name "/plan-charge/prod/database-url" --with-decryption --region eu-west-3 --query 'Parameter.Value' --output text | sed 's/postgresql+asyncpg:/postgresql:/')
ssh ec2-user@51.44.163.97 "psql \"$DATABASE_URL\" -f /tmp/reinject_matricules_production.sql"
```

### 2. Monitoring des synchronisations
Surveiller les synchronisations Gryzzly et réinjecter immédiatement après.

### 3. Communication utilisateurs
- Informer que les droits TR peuvent être temporairement indisponibles
- Délai max de restauration : 5 minutes après synchronisation

## 📋 Matricules à préserver (15 personnes)

| Matricule | Email | Nom Complet |
|-----------|--------|-------------|
| 1 | david.alhyar@nda-partners.com | David Al Hyar |
| 2 | vincent.mirzaian@nda-partners.com | Vincent Mirzaian |
| 3 | maria.zavlyanova@nda-partners.com | Maria Zavlyanova |
| 5 | tristan.lepennec@nda-partners.com | Tristan Le Pennec |
| 7 | elmehdi.elouardi@nda-partners.com | Elmehdi Elouardi |
| 8 | maxime.rodrigues@nda-partners.com | Maxime Rodrigues |
| 9 | efflam.kervoas@nda-partners.com | Efflam Kervoas |
| 11 | sami.benouattaf@nda-partners.com | Sami Benouattaf |
| 12 | alexandre.linck@nda-partners.com | Alexandre Linck |
| 14 | nail.ferroukhi@nda-partners.com | Naïl Ferroukhi |
| 15 | soukaina.elkourdi@nda-partners.com | Soukaïna El Kourdi |
| 16 | malek.attia@nda-partners.com | Malek Attia |
| 17 | thomas.deruy@nda-partners.com | Thomas Deruy |
| 19 | valerie.patureau@nda-partners.com | Valérie Patureau |
| 112 | berenger.de-kerever@nda-partners.com | Bérenger De Kerever |

## 🔧 Corrections développées (prêtes à déployer)

### 1. Fix timezone (`app/models/audit.py`)
```python
# AVANT
return datetime.utcnow() > self.expires_at

# APRÈS  
return datetime.now(timezone.utc) > self.expires_at
```

### 2. Fix préservation matricules (`app/services/gryzzly_sync.py`)
- Préservation conditionnelle des matricules existants
- Logs de traçabilité ajoutés
- Tests validés localement

### 3. Image Docker prête
- `557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend:matricules-timezone-fix-v3`
- Contient les 2 corrections
- Build validé pour architecture x86_64

## 🚨 Problème technique de déploiement

### Échecs constatés
- **Version 12** : 8 failed tasks - Paramètres SSM manquants
- **Version 13** : 2 failed tasks - Paramètres SSM corrigés mais échec
- **Version 14** : Tasks ne démarrent pas - Configuration simplifiée mais échec

### Hypothèses à investiguer
1. **Variables d'environnement manquantes** - L'app a peut-être besoin de paramètres non documentés
2. **Dépendances d'image** - L'image avec les fixes a peut-être des problèmes de dépendances
3. **Permissions IAM** - Rôles ou permissions manquants pour les nouvelles versions
4. **Health checks** - La nouvelle version ne répond pas aux health checks à temps

## 📅 Plan de correction définitive

### Phase 1: Investigation (URGENT)
- [ ] Analyser logs détaillés des échecs de versions 12-14
- [ ] Comparer configurations entre version 5 (qui marche) et version 14
- [ ] Tester l'image avec fixes en local/staging
- [ ] Identifier la différence critique qui empêche le démarrage

### Phase 2: Correction ciblée
- [ ] Corriger le problème de démarrage identifié
- [ ] Créer version 15 avec correction
- [ ] Tests de démarrage en staging
- [ ] Déploiement progressif (1 tâche puis 2)

### Phase 3: Validation définitive
- [ ] Synchronisation Gryzzly de test
- [ ] Validation persistance des matricules
- [ ] Tests droits TR complets
- [ ] Documentation finale

## 🔄 Procédure d'urgence

**En cas de synchronisation Gryzzly** :

1. **Vérifier les matricules** :
```bash
DATABASE_URL=$(aws ssm get-parameter --name "/plan-charge/prod/database-url" --with-decryption --region eu-west-3 --query 'Parameter.Value' --output text | sed 's/postgresql+asyncpg:/postgresql:/')
ssh ec2-user@51.44.163.97 "echo 'SELECT COUNT(matricule) FROM gryzzly_collaborators;' | psql \"$DATABASE_URL\""
```

2. **Si matricules perdus (count = 0), réinjecter immédiatement** :
```bash
ssh ec2-user@51.44.163.97 "psql \"$DATABASE_URL\" -f /tmp/reinject_matricules_production.sql"
```

3. **Vérifier le résultat (doit être 15)** :
```bash
ssh ec2-user@51.44.163.97 "echo 'SELECT COUNT(matricule) FROM gryzzly_collaborators;' | psql \"$DATABASE_URL\""
```

## ⏰ Temps de restauration
- **Détection** : Immédiate (après sync)  
- **Réinjection** : 30 secondes
- **Validation** : 15 secondes
- **Total** : < 1 minute

---

**🎯 Objectif** : Solution temporaire jusqu'à résolution du problème de déploiement  
**👤 Responsable** : Équipe développement  
**⏱️ SLA** : Matricules restaurés < 5 minutes après chaque synchronisation