# Fix Affichage Collaborateurs Éligibles aux TR

## Problème Identifié

La page des droits TR n'affichait pas les collaborateurs éligibles aux titres restaurant. L'endpoint `/api/v1/tr/rights/{year}/{month}` retournait une liste vide dans la propriété `employees`.

## Analyse du Problème

### Cause Racine
Le service `TRService` dans `tr_service.py` essayait d'appeler directement la fonction `get_collaborators` depuis l'endpoint API (ligne 199). Cette approche ne fonctionnait pas car :

1. `get_collaborators` est une fonction endpoint FastAPI avec des dépendances (`Depends`)
2. Ces dépendances ne peuvent pas être résolues lors d'un appel direct depuis un service
3. L'appel échouait silencieusement et retournait une liste vide

### Données en Base
Vérification effectuée :
- **29 collaborateurs Gryzzly** actifs
- **65 employés Payfit**
- **39 contrats Payfit** (15 actifs, 24 inactifs)
- **0 overrides d'éligibilité TR** dans `tr_eligibility_overrides`

## Solution Implémentée

### Refactorisation du TRService

Remplacement de l'appel à l'endpoint par des requêtes SQL directes :

```python
async def calculate_all_tr_rights(self, year: int, month: int):
    # 1. Récupération des collaborateurs Gryzzly actifs avec matricule
    collaborators_query = select(GryzzlyCollaborator).where(
        and_(
            GryzzlyCollaborator.matricule.isnot(None),
            GryzzlyCollaborator.is_active == True
        )
    )
    
    # 2. Récupération des employés Payfit avec leurs contrats
    payfit_query = select(PayfitEmployee).options(selectinload(PayfitEmployee.contracts))
    
    # 3. Récupération des overrides manuels d'éligibilité
    overrides_result = await self.session.execute(select(TREligibilityOverride))
```

### Logique d'Éligibilité TR

La détermination de l'éligibilité suit cette hiérarchie :

1. **Override Manuel** (priorité maximale) : Si présent dans `tr_eligibility_overrides`
2. **Contrat Payfit Actif** : Si l'employé a au moins un contrat actif dans Payfit
3. **Par Défaut** : Si pas de données Payfit, les collaborateurs Gryzzly actifs sont éligibles

```python
# Check for manual override first
override = overrides_by_email.get(email_lower)
if override:
    eligible_tr = override.is_eligible
else:
    # Check if there's an active Payfit contract
    payfit_emp = payfit_map.get(email_lower)
    if payfit_emp and payfit_emp.contracts:
        active_contracts = [c for c in payfit_emp.contracts if c.is_active]
        eligible_tr = len(active_contracts) > 0
    else:
        # Default to eligible for active Gryzzly collaborators
        eligible_tr = True
```

## Résultats

### Avant le Fix
- L'endpoint retournait `"employees": []`
- Aucun collaborateur n'apparaissait dans la page TR

### Après le Fix
- Les collaborateurs éligibles sont correctement identifiés
- Basé sur les contrats actifs Payfit ou le statut Gryzzly par défaut
- Les overrides manuels sont respectés

## Déploiement

Le code a été commité mais nécessite un déploiement :

```bash
# Build et push de l'image Docker
docker build -t plan-charge-backend backend/
docker tag plan-charge-backend:latest [ECR_URI]:latest
docker push [ECR_URI]:latest

# Mise à jour du service ECS
aws ecs update-service --cluster plan-charge-prod-cluster \
  --service plan-charge-prod-backend --force-new-deployment
```

## Points Importants

1. **Données Payfit** : La synchronisation Payfit est en mode mock, donc les contrats existants proviennent probablement d'un import initial
2. **Éligibilité par Défaut** : Les collaborateurs sans données Payfit sont considérés éligibles s'ils sont actifs dans Gryzzly
3. **Overrides Manuels** : L'interface permet de modifier manuellement l'éligibilité via la table `tr_eligibility_overrides`

## Commandes de Vérification

### Vérifier les Collaborateurs Éligibles
```sql
SELECT g.email, g.matricule, pc.is_active as has_active_contract
FROM gryzzly_collaborators g
LEFT JOIN payfit_employees p ON LOWER(g.email) = LOWER(p.email)
LEFT JOIN payfit_contracts pc ON p.payfit_id = pc.payfit_employee_id AND pc.is_active = true
WHERE g.is_active = true AND g.matricule IS NOT NULL;
```

### Vérifier les Overrides
```sql
SELECT * FROM tr_eligibility_overrides;
```

## Status Final

✅ **Problème Résolu** : Le service TR récupère maintenant correctement les collaborateurs éligibles en utilisant des requêtes SQL directes au lieu d'essayer d'appeler l'endpoint API.