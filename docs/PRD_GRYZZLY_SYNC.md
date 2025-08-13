# PRD : Intégration Gryzzly dans Plan Charge v11

## 1. Vue d'ensemble

### 1.1 Objectif
Intégrer l'API Gryzzly pour synchroniser les utilisateurs, projets, tâches et temps passés (time entries) dans Plan Charge v11, permettant une vision consolidée des données de gestion du temps et des projets.

### 1.2 Contexte
Gryzzly est un outil de gestion du temps et des projets utilisé par l'organisation. L'intégration permettra de :
- Synchroniser automatiquement les données depuis Gryzzly
- Visualiser les temps passés par projet et utilisateur
- Mapper les utilisateurs Gryzzly avec les utilisateurs Plan Charge
- Analyser les données de productivité et d'allocation des ressources

### 1.3 Périmètre
- ✅ Synchronisation des utilisateurs
- ✅ Synchronisation des projets et clients
- ✅ Synchronisation des tâches
- ✅ Synchronisation des temps passés (time entries)
- ✅ Dashboard de visualisation
- ✅ Historique des synchronisations
- ❌ Création/modification dans Gryzzly (lecture seule)
- ❌ Synchronisation temps réel (batch uniquement)

## 2. Architecture technique

### 2.1 API Gryzzly

#### Caractéristiques
- **Format** : RPC-style (POST uniquement)
- **Base URL** : https://api.gryzzly.io/v1
- **Authentification** : Bearer token (API key)
- **Rate limiting** : 50 requêtes par 10 secondes
- **Format des endpoints** : `/v1/RESSOURCE.ACTION`

#### Endpoints principaux
```
POST /v1/users.list          # Liste des utilisateurs
POST /v1/projects.list       # Liste des projets
POST /v1/tasks.list         # Liste des tâches
POST /v1/declarations.list   # Liste des temps passés
POST /v1/customers.list      # Liste des clients
```

### 2.2 Modèles de données

#### GryzzlyUser
```python
class GryzzlyUser(BaseModel):
    id: UUID                      # ID interne
    gryzzly_id: str              # ID Gryzzly
    email: str                    # Email unique
    first_name: str              # Prénom
    last_name: str               # Nom
    is_active: bool              # Statut actif
    local_user_id: UUID          # Lien avec User local
    metadata_json: dict          # Métadonnées Gryzzly
    last_synced_at: datetime     # Dernière sync
    created_at: datetime         # Création
    updated_at: datetime         # Modification
```

#### GryzzlyProject
```python
class GryzzlyProject(BaseModel):
    id: UUID                      # ID interne
    gryzzly_id: str              # ID Gryzzly
    name: str                    # Nom du projet
    code: str                    # Code projet
    description: str             # Description
    is_active: bool              # Statut actif
    gryzzly_client_id: str       # ID client Gryzzly
    gryzzly_client_name: str     # Nom client
    budget_hours: float          # Budget en heures
    hourly_rate: float           # Taux horaire
    metadata_json: dict          # Métadonnées
    last_synced_at: datetime     # Dernière sync
```

#### GryzzlyTask
```python
class GryzzlyTask(BaseModel):
    id: UUID                      # ID interne
    gryzzly_id: str              # ID Gryzzly
    gryzzly_project_id: str      # ID projet Gryzzly
    name: str                    # Nom de la tâche
    description: str             # Description
    is_active: bool              # Statut actif
    metadata_json: dict          # Métadonnées
    last_synced_at: datetime     # Dernière sync
```

#### GryzzlyTimeEntry
```python
class GryzzlyTimeEntry(BaseModel):
    id: UUID                      # ID interne
    gryzzly_id: str              # ID Gryzzly
    gryzzly_user_id: str         # ID utilisateur
    gryzzly_task_id: str         # ID tâche
    gryzzly_project_id: str      # ID projet (dénormalisé)
    date: date                   # Date de la déclaration
    duration: int                # Durée en secondes
    hours: float                 # Heures (calculé)
    days: float                  # Jours (calculé)
    description: str             # Description
    hourly_cost: float           # Coût horaire
    metadata_json: dict          # Métadonnées
    last_synced_at: datetime     # Dernière sync
```

#### GryzzlySyncLog
```python
class GryzzlySyncLog(BaseModel):
    id: UUID                      # ID
    sync_type: str               # Type (users, projects, etc.)
    sync_status: str             # Statut (started, success, failed)
    started_at: datetime         # Début
    completed_at: datetime       # Fin
    records_synced: int          # Nombre synchronisés
    records_created: int         # Nombre créés
    records_updated: int         # Nombre mis à jour
    records_failed: int          # Nombre échoués
    error_message: str           # Message d'erreur
    metadata_json: dict          # Métadonnées
    triggered_by: str            # Déclenché par
```

### 2.3 Client API

#### GryzzlyAPIClient
```python
class GryzzlyAPIClient:
    def __init__(self):
        self.base_url = settings.GRYZZLY_API_URL
        self.api_key = settings.GRYZZLY_API_KEY
        self.rate_limiter = RateLimiter(50, 10)  # 50 req/10s
        
    async def _make_request(self, endpoint: str, data: dict) -> dict:
        """Execute request with rate limiting and retry"""
        await self.rate_limiter.acquire()
        # Implementation avec httpx, retry logic, error handling
        
    async def get_users(self, limit=100, offset=0) -> List[dict]:
        """Get users with pagination"""
        
    async def get_projects(self, limit=100, offset=0) -> List[dict]:
        """Get projects with pagination"""
        
    async def get_tasks(self, project_id=None) -> List[dict]:
        """Get tasks, optionally filtered by project"""
        
    async def get_time_entries(self, start_date, end_date, user_id=None) -> List[dict]:
        """Get time entries for date range"""
        
    async def get_all_users(self) -> List[dict]:
        """Get all users with automatic pagination"""
        
    async def get_all_projects(self) -> List[dict]:
        """Get all projects with automatic pagination"""
```

#### RateLimiter
```python
class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        # Implementation avec asyncio.sleep si nécessaire
```

### 2.4 Service de synchronisation

#### GryzzlyService
```python
class GryzzlyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = GryzzlyAPIClient()
        
    async def sync_users(self) -> Dict[str, int]:
        """Synchronise les utilisateurs"""
        # 1. Récupérer depuis API
        # 2. Créer/Mettre à jour en base
        # 3. Mapper avec utilisateurs locaux (par email)
        # 4. Logger dans GryzzlySyncLog
        
    async def sync_projects(self) -> Dict[str, int]:
        """Synchronise les projets"""
        # Similar logic
        
    async def sync_tasks(self) -> Dict[str, int]:
        """Synchronise les tâches"""
        # Similar logic
        
    async def sync_time_entries(self, start_date=None, end_date=None) -> Dict[str, int]:
        """Synchronise les temps passés"""
        # Default: 3 mois avant, 1 mois après
        # Similar logic avec gestion des dates
        
    async def sync_all(self) -> Dict[str, Any]:
        """Synchronisation complète dans l'ordre"""
        # 1. Users
        # 2. Projects
        # 3. Tasks
        # 4. Time entries
        
    async def get_sync_status(self) -> Dict[str, Any]:
        """Retourne le statut de synchronisation"""
```

## 3. Endpoints API

### 3.1 Endpoints de synchronisation

```python
# Status et statistiques
GET  /api/v1/gryzzly/status          # État de synchronisation
GET  /api/v1/gryzzly/stats           # Statistiques globales

# Déclenchement de synchronisation
POST /api/v1/gryzzly/sync/test-connection  # Test connexion
POST /api/v1/gryzzly/sync/users           # Sync utilisateurs
POST /api/v1/gryzzly/sync/projects        # Sync projets
POST /api/v1/gryzzly/sync/tasks           # Sync tâches
POST /api/v1/gryzzly/sync/time-entries    # Sync temps (avec dates optionnelles)
POST /api/v1/gryzzly/sync/full            # Sync complète

# Consultation des données
GET  /api/v1/gryzzly/users               # Liste utilisateurs
GET  /api/v1/gryzzly/projects            # Liste projets
GET  /api/v1/gryzzly/tasks               # Liste tâches
GET  /api/v1/gryzzly/time-entries        # Liste temps avec filtres
GET  /api/v1/gryzzly/sync-logs           # Historique des syncs

# Agrégations et métriques
GET  /api/v1/gryzzly/time-entries/by-project  # Temps par projet
GET  /api/v1/gryzzly/time-entries/by-user     # Temps par utilisateur
GET  /api/v1/gryzzly/projects/metrics         # Métriques projets
```

### 3.2 Format des réponses enrichies

Les endpoints de liste retourneront des données enrichies avec jointures :

```json
// GET /api/v1/gryzzly/time-entries
{
  "id": "uuid",
  "gryzzly_id": "gryzzly_id",
  "date": "2025-01-15",
  "hours": 7.5,
  "days": 1.0,
  "description": "Développement feature X",
  
  // Enrichissement utilisateur
  "user_id": "gryzzly_user_id",
  "user_name": "Jean Dupont",
  "user_email": "jean.dupont@company.com",
  
  // Enrichissement projet
  "project_id": "gryzzly_project_id",
  "project_name": "Projet Alpha",
  "project_code": "ALPHA",
  
  // Enrichissement tâche
  "task_id": "gryzzly_task_id",
  "task_name": "Development"
}
```

## 4. Frontend

### 4.1 Service TypeScript

```typescript
// gryzzly.service.ts
export interface GryzzlyUser {
  id: string;
  gryzzly_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  is_active: boolean;
  local_user_id?: string;
  last_synced_at: string;
}

export interface GryzzlyProject {
  id: string;
  gryzzly_id: string;
  name: string;
  code?: string;
  description?: string;
  client_name?: string;
  budget_hours?: number;
  hourly_rate?: number;
  is_active: boolean;
}

export interface GryzzlyTimeEntry {
  id: string;
  date: string;
  hours: number;
  days: number;
  description?: string;
  // Enriched fields
  user_name?: string;
  project_name?: string;
  task_name?: string;
}

class GryzzlyService {
  async getStatus(): Promise<GryzzlySyncStatus>;
  async syncUsers(): Promise<SyncResponse>;
  async syncProjects(): Promise<SyncResponse>;
  async syncTimeEntries(startDate?: string, endDate?: string): Promise<SyncResponse>;
  async syncFull(): Promise<SyncResponse>;
  async getUsers(params?: UserParams): Promise<GryzzlyUser[]>;
  async getProjects(params?: ProjectParams): Promise<GryzzlyProject[]>;
  async getTimeEntries(params?: TimeEntryParams): Promise<GryzzlyTimeEntry[]>;
}
```

### 4.2 Composants React

#### GryzzlyDashboard
Page principale avec :
- Cards de statistiques (users, projects, time entries)
- Boutons de synchronisation
- État de connexion API
- Tabs pour naviguer entre les vues

#### GryzzlyUsers
- Tableau des utilisateurs synchronisés
- Mapping avec utilisateurs locaux
- Filtres (actifs uniquement)
- Actions de sync

#### GryzzlyProjects
- Tableau des projets
- Informations client
- Budget et taux horaire
- Métriques (heures consommées vs budget)

#### GryzzlyTimeEntries
- Tableau des temps passés
- Filtres par date, utilisateur, projet
- Agrégations (total heures/jours)
- Export CSV

#### GryzzlySyncLogs
- Historique des synchronisations
- Statut, durée, nombre d'enregistrements
- Messages d'erreur
- Filtres par type et statut

## 5. Configuration

### 5.1 Variables d'environnement

```env
# Gryzzly API Configuration
GRYZZLY_API_URL=https://api.gryzzly.io/v1
GRYZZLY_API_KEY=your_api_key_here
GRYZZLY_USE_MOCK=false  # Pour tests avec données mockées
```

### 5.2 Configuration backend

```python
# config.py
class Settings(BaseSettings):
    GRYZZLY_API_URL: str = "https://api.gryzzly.io/v1"
    GRYZZLY_API_KEY: str
    GRYZZLY_USE_MOCK: bool = False
```

## 6. Plan d'implémentation

### Phase 1 : Backend Core (2-3 jours)
1. Créer les modèles SQLAlchemy
2. Générer les migrations Alembic
3. Implémenter GryzzlyAPIClient avec rate limiting
4. Tests unitaires du client API

### Phase 2 : Service de synchronisation (2-3 jours)
1. Implémenter GryzzlyService
2. Créer les endpoints de synchronisation
3. Ajouter les background tasks
4. Tests d'intégration

### Phase 3 : Endpoints de consultation (1-2 jours)
1. Endpoints de liste avec pagination
2. Enrichissement avec jointures
3. Endpoints d'agrégation
4. Tests API

### Phase 4 : Frontend Base (2-3 jours)
1. Service TypeScript
2. Dashboard principal
3. Composants de liste basiques
4. Intégration avec l'API

### Phase 5 : Frontend Avancé (2-3 jours)
1. Filtres et recherche
2. Agrégations et métriques
3. Export de données
4. Optimisations UX

### Phase 6 : Tests et optimisation (1-2 jours)
1. Tests end-to-end
2. Optimisation des requêtes
3. Gestion d'erreur améliorée
4. Documentation

## 7. Considérations techniques

### 7.1 Performance
- Pagination sur toutes les listes
- Utilisation de `selectinload` pour éviter N+1
- Cache des données statiques (users, projects)
- Background tasks pour syncs longues

### 7.2 Sécurité
- API key stockée de manière sécurisée
- Validation des données entrantes
- Logs sans données sensibles
- Accès admin pour certaines syncs

### 7.3 Monitoring
- Logs détaillés des syncs
- Métriques de performance
- Alertes sur échecs répétés
- Dashboard de monitoring

### 7.4 Gestion d'erreur
- Retry automatique avec backoff
- Gestion du rate limiting
- Fallback sur données en cache
- Messages d'erreur explicites

## 8. Tests requis

### 8.1 Tests unitaires
- Client API avec mocks
- Service de synchronisation
- Parsing des données
- Rate limiter

### 8.2 Tests d'intégration
- Connexion API réelle
- Synchronisation complète
- Mapping utilisateurs
- Gestion d'erreurs

### 8.3 Tests frontend
- Affichage des données
- Actions de synchronisation
- Filtres et pagination
- Export de données

### 8.4 Tests de performance
- Sync de gros volumes
- Rate limiting
- Requêtes optimisées
- Cache efficace

## 9. Critères de succès

### 9.1 Fonctionnels
- ✅ Synchronisation complète sans erreur
- ✅ Mapping automatique des utilisateurs
- ✅ Visualisation claire des données
- ✅ Historique des synchronisations

### 9.2 Techniques
- ✅ Temps de sync < 30 secondes pour 1000 entrées
- ✅ Pas de dépassement du rate limit
- ✅ Disponibilité > 99%
- ✅ Temps de réponse < 500ms

### 9.3 UX
- ✅ Interface intuitive
- ✅ Feedback clair sur les actions
- ✅ Gestion d'erreur gracieuse
- ✅ Performance perçue rapide

## 10. Évolutions futures

### Court terme
- Synchronisation automatique programmée
- Webhooks pour sync temps réel
- Export avancé (Excel, PDF)

### Moyen terme
- Création/modification dans Gryzzly
- Validation des temps avant sync
- Règles de mapping complexes

### Long terme
- BI et analytics avancés
- Prédictions et ML
- Intégration avec autres outils

## 11. Références

- [API Gryzzly Documentation](https://api.gryzzly.io/docs)
- [Swagger Gryzzly](docs/gryzzly_swagger.json)
- [Implementation v8](../plan-charge-v8/backend/app/services/gryzzly_service.py)
- [PRD Payfit](PRD_PAYFIT_SYNC.md) - Pour cohérence d'implémentation

---

*Document créé le : 2025-01-15*
*Dernière mise à jour : 2025-01-15*
*Version : 1.0*
*Auteur : Plan Charge Team*