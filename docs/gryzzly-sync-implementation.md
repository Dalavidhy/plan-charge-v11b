# Documentation de l'implémentation de la synchronisation Gryzzly

## Vue d'ensemble

L'intégration Gryzzly dans Plan Charge v8 permet de synchroniser automatiquement :
- Les utilisateurs
- Les projets
- Les tâches et sous-tâches avec hiérarchie complète
- Les entrées de temps (time entries)

## Architecture technique

### 1. Modèles de données

#### GryzzlyTask
Le modèle `GryzzlyTask` gère la hiérarchie des tâches avec une relation auto-référentielle :

```python
class GryzzlyTask(Base):
    __tablename__ = "gryzzly_tasks"
    
    # Identifiants
    id = Column(UUID(as_uuid=True), primary_key=True)
    gryzzly_id = Column(String(255), unique=True, nullable=False)
    
    # Relation projet
    gryzzly_project_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_projects.id"))
    
    # Hiérarchie des tâches
    parent_id = Column(UUID(as_uuid=True), ForeignKey("gryzzly_tasks.id"), nullable=True)
    is_container = Column(Boolean, default=False)  # Tâche conteneur/groupe
    
    # Attributs budget
    budget_type = Column(String(20))  # none, detailed, global, time
    budget_amount = Column(Numeric(10, 2))
    hourly_rate = Column(Numeric(10, 2))
    hourly_rate_mode = Column(String(20))  # task, group, contributor
    planned_duration = Column(Integer)  # En secondes
```

### 2. Service de synchronisation

Le service `GryzzlySyncService` utilise une approche en deux passes pour gérer les relations parent-enfant :

```python
async def sync_tasks(self):
    # Première passe : créer toutes les tâches sans relations parent
    task_mapping = {}  # gryzzly_id -> db_task
    
    for task_data in gryzzly_tasks:
        # Créer ou mettre à jour la tâche
        task_mapping[task_data["id"]] = task
    
    # Deuxième passe : établir les relations parent-enfant
    for task_data in gryzzly_tasks:
        if task_data.get("parent_id"):
            # Lier la tâche à son parent
```

### 3. API REST

Les endpoints suivants ont été ajoutés :

- `POST /api/v1/gryzzly/sync/tasks` - Déclenche la synchronisation des tâches
- `GET /api/v1/gryzzly/tasks` - Liste les tâches avec filtres optionnels :
  - `project_id` : Filtrer par projet
  - `parent_id` : Filtrer par tâche parent
  - `is_container` : Filtrer les tâches conteneurs

## Flux de synchronisation

### 1. Synchronisation complète

```python
# Ordre de synchronisation respecté
1. Utilisateurs (sync_users)
2. Projets (sync_projects) 
3. Tâches (sync_tasks)
4. Entrées de temps (sync_time_entries)
```

### 2. Gestion des dates ISO

L'API Gryzzly retourne des dates avec le suffixe 'Z' qui n'est pas supporté par `fromisoformat()` de Python :

```python
# Conversion nécessaire
datetime.fromisoformat(task_data["start_at"].replace('Z', '+00:00'))
```

### 3. Mock Data pour les tests

Le `MockGryzzlyApiClient` fournit des données de test réalistes :
- 4 utilisateurs (3 actifs, 1 inactif)
- 4 projets (3 actifs, 1 inactif)
- 3 tâches avec hiérarchie :
  - 2 tâches racines
  - 1 sous-tâche

## Résultats de synchronisation

### Test exécuté avec succès

```
Starting Gryzzly synchronization test with mock data...
============================================================

1. Testing USER synchronization...
   Status: success
   Records synced: 4
   Records failed: 0
   Total users in database: 4

2. Testing PROJECT synchronization...
   Status: success
   Records synced: 4
   Records failed: 0
   Total projects in database: 4

3. Testing TASK synchronization...
   Status: success
   Records synced: 3
   Records failed: 0
   Total tasks in database: 3
   Root tasks: 2
   - User Authentication
     └─ JWT Implementation
   - UI Design System

4. Testing FULL synchronization...
   Full sync completed!
   - users: success (4 synced)
   - projects: success (4 synced)
   - tasks: success (3 synced)
   - time_entries: success (186 synced)

✅ Synchronization test completed successfully!
```

## Attributs synchronisés

### Projets
- Identifiant Gryzzly
- Nom et code projet
- Description
- Client (ID et nom)
- Budget en heures
- Taux horaire
- Statut actif/inactif
- Métadonnées

### Tâches
- Identifiant Gryzzly
- Nom de la tâche
- Projet associé
- Tâche parent (hiérarchie)
- Type conteneur (is_container)
- Dates (début, fin, complétion)
- Budget (type, montant)
- Taux horaire et mode
- Durée planifiée
- Tags et groupes
- Métadonnées

## Configuration

### Variables d'environnement

```env
# API Gryzzly
GRYZZLY_API_KEY=your_api_key
GRYZZLY_API_URL=https://api.grizzly.fr/public/v2
GRYZZLY_USE_MOCK=true  # Pour les tests avec données mock
```

### Base de données

Une migration a été créée pour ajouter la table `gryzzly_tasks` :

```sql
CREATE TABLE gryzzly_tasks (
    id UUID PRIMARY KEY,
    gryzzly_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    gryzzly_project_id UUID REFERENCES gryzzly_projects(id),
    parent_id UUID REFERENCES gryzzly_tasks(id),
    is_container BOOLEAN DEFAULT FALSE,
    -- autres colonnes...
);
```

## Prochaines étapes

1. **Interface utilisateur** : Développer les composants React pour afficher les projets et tâches synchronisés
2. **Synchronisation automatique** : Mettre en place un cron job pour la synchronisation périodique
3. **Webhooks** : Implémenter les webhooks Gryzzly pour une synchronisation en temps réel
4. **Mapping utilisateurs** : Améliorer la correspondance entre utilisateurs Gryzzly et utilisateurs locaux
5. **Gestion des conflits** : Stratégie de résolution des conflits lors de modifications concurrentes

## Points d'attention

1. **Performance** : La synchronisation en deux passes est nécessaire pour gérer les relations parent-enfant
2. **Limites API** : Respecter les limites de taux de l'API Gryzzly
3. **Cohérence des données** : S'assurer que les projets existent avant de synchroniser les tâches
4. **Gestion des erreurs** : Logging détaillé pour tracer les échecs de synchronisation

## Conclusion

L'implémentation permet une synchronisation complète et robuste des données Gryzzly avec :
- Gestion correcte de la hiérarchie des tâches
- Support des attributs de budget et planification
- Traçabilité complète via les logs de synchronisation
- Mode mock pour les tests et le développement

La base backend est maintenant prête pour le développement de l'interface utilisateur.