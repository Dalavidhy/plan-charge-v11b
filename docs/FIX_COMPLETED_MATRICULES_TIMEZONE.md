# ✅ Correction terminée - Matricules et erreur timezone

**Date**: 21/08/2025  
**Version**: plan-charge-backend:matricules-timezone-fix-v3  
**Task Definition**: plan-charge-prod-backend:12

## 🎯 Problèmes résolus

### 1. **Erreur de timezone dans l'authentification**
- **Fichier**: `app/models/audit.py:59`
- **Erreur**: `TypeError: can't compare offset-naive and offset-aware datetimes`
- **Cause**: `datetime.utcnow()` (naive) vs `DateTime(timezone=True)` (aware)
- **Solution**: Remplacé par `datetime.now(timezone.utc)` (aware)

### 2. **Perte des matricules lors des synchronisations Gryzzly**
- **Fichier**: `app/services/gryzzly_sync.py`
- **Cause**: Écrasement systématique des champs avec `None` depuis l'API Gryzzly
- **Solution**: Préservation conditionnelle des matricules existants

## 🔧 Corrections apportées

### Correction timezone (`app/models/audit.py`)
```python
# AVANT (problématique)
return datetime.utcnow() > self.expires_at

# APRÈS (corrigé)  
return datetime.now(timezone.utc) > self.expires_at
```

### Correction matricules (`app/services/gryzzly_sync.py`)
```python
# Dans _parse_collaborator_data
matricule = data.get("matricule")
if matricule is not None:
    result["matricule"] = matricule
    logger.info(f"Gryzzly sync: Setting matricule {matricule} for {data.get('email')}")
else:
    logger.info(f"Gryzzly sync: Preserving existing matricule for {data.get('email')}")

# Dans sync_collaborators  
if key == "matricule" and value is None and getattr(existing, "matricule", None) is not None:
    logger.info(f"Gryzzly sync: Preserving existing matricule {getattr(existing, 'matricule')} for {existing.email}")
    continue
```

## 📊 État de déploiement

### Infrastructure
- **Service ECS**: `plan-charge-prod-backend` - ✅ ACTIF
- **Tâches en cours**: 1/2 tâches opérationnelles
- **Load Balancer**: 1 cible saine (10.0.1.65)
- **Task Definition**: Version 12 déployée

### Base de données
- **Matricules réinjectés**: 15/15 ✅
- **État actuel**: 30 collaborateurs, 15 avec matricule (50%)
- **Liste des matricules**: 1,2,3,5,7,8,9,11,12,14,15,16,17,19,112

### Images Docker
- **Image stable**: `557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend:matricules-timezone-fix-v3`
- **Digest SHA**: `sha256:bdd50cf895ae0df2168db48aaec2c380b34e3e712d120769f93ec20d970ef9b6`

## 🧪 Tests à effectuer

### 1. Test de synchronisation Gryzzly
- [ ] Déclencher une synchronisation complète
- [ ] Vérifier absence d'erreurs de timezone
- [ ] Confirmer que les 15 matricules persistent
- [ ] Vérifier les logs de préservation

### 2. Test d'affichage TR  
- [ ] Accéder à la page des droits TR
- [ ] Vérifier que les 15 collaborateurs éligibles sont affichés
- [ ] Confirmer le calcul correct des droits

### 3. Test de régression
- [ ] Vérifier que l'authentification fonctionne sans erreur
- [ ] Tester les autres synchronisations (Payfit)
- [ ] Confirmer la stabilité générale du système

## ⚡ Commandes de validation

```bash
# Vérifier les matricules en base
DATABASE_URL=$(aws ssm get-parameter --name "/plan-charge/prod/database-url" --with-decryption --region eu-west-3 --query 'Parameter.Value' --output text | sed 's/postgresql+asyncpg:/postgresql:/')

ssh ec2-user@51.44.163.97 "echo 'SELECT COUNT(*) as total, COUNT(matricule) as avec_matricule FROM gryzzly_collaborators;' | psql \"$DATABASE_URL\""

# Vérifier l'état du service
aws ecs describe-services --cluster plan-charge-prod-cluster --services plan-charge-prod-backend --region eu-west-3

# Vérifier les logs récents
aws logs tail /ecs/plan-charge-prod --region eu-west-3 --since 10m | grep -E "sync|matricule|ERROR"
```

## 📋 Résumé des changements

### Commit principal
- **Hash**: À définir après commit
- **Message**: "fix: Corriger l'erreur de timezone et préserver les matricules lors des syncs"
- **Fichiers modifiés**:
  - `app/models/audit.py` - Correction timezone
  - `app/services/gryzzly_sync.py` - Préservation matricules (déjà committé)

### Déploiement
- **Image Docker**: `matricules-timezone-fix-v3`
- **Task Definition**: Version 12
- **Service**: Déployé et opérationnel

---

**🎉 Status**: En attente de test de synchronisation finale  
**👤 Responsable**: Équipe développement  
**📅 Prochaine étape**: Validation par test de synchronisation Gryzzly