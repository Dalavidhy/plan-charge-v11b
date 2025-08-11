### Plan de refonte from scratch – Plan Charge v8

Ce document décrit une refonte complète, orientée fiabilité, maintenabilité et testabilité. Il couvre l’architecture, le schéma de données, les contrats d’API, la sécurité, l’observabilité, les tests et l’industrialisation (Docker).

### Objectifs
- **Stabilité**: endpoints prévisibles, erreurs standardisées, migration de schéma maîtrisée.
- **Sécurité**: JWT access/refresh avec rotation, RBAC, durcissement CORS/headers.
- **Performance**: indexes, requêtes n+1 évitées, caches ciblés.
- **Clarté**: séparation nette domaine/services/repos/API, typage strict.
- **Ops**: déploiement Docker, health/readiness, métriques Prometheus.

### Stack technique
- **Backend**: FastAPI (>=0.115), Pydantic v2, SQLAlchemy 2.0, Alembic, passlib[bcrypt], python-jose, httpx.
- **Base**: PostgreSQL 15+, UUID natifs, extensions `uuid-ossp`, `pgcrypto`.
- **Queue (optionnel)**: Redis + Celery (synchros asynchrones).
- **Frontend**: React 18, CRA/Vite, MUI. (Non bloquant pour la refonte backend.)
- **Observabilité**: `prometheus-client`, logs JSON, trace-id par requête.

### Architecture applicative (DDD light)
```
backend/app/
  main.py
  core/            # config, sécurité, cors, middlewares
  api/
    v1/
      api.py
      endpoints/   # contrôleurs HTTP fins, pas de logique métier
  domain/          # logique métier pure (entités, services de domaine)
    auth/
    users/
    plan_charge/
    integrations/  # drivers Payfit, Gryzzly
  repositories/    # accès persistance (SQLAlchemy)
  services/        # cas d’usage applicatifs (orchestrations)
  db/              # session, base, migrations Alembic
  tests/
```

### Schéma de base de données (proposition)
- `users` (UUID, email unique, hash, prénom/nom, `status`, `is_active`, `is_superuser`, timestamps, `last_login_at`).
- `roles` (RBAC) et tables de jonction:
  - `roles` (id, name), `permissions` (id, code), `role_permissions`, `user_roles`.
  - Alternative minimaliste: enum `user_role` si RBAC fin non requis à court terme.
- `refresh_tokens` (rotation anti-rejeu): id, `user_id`, token hashé, `expires_at`, `revoked_at`, index sur `user_id`, `expires_at`.
- `audit_logs`: audits lecture/écriture (action, ressource, ip, user-agent, metadata JSONB).
- Noyau métier plan de charge:
  - `projects` (id, code, nom, statut, dates, BU),
  - `assignments` (id, `user_id`, `project_id`, taux, dates),
  - `forecasts` (id, `user_id`, mois, capacité, charge, source),
  - indexes: (`user_id`, `mois`), (`project_id`, `mois`).
- Intégrations:
  - `user_mappings` (`user_id`, `gryzzly_user_id`, `payfit_employee_id`, metadata, `created_by_id`).

Principes:
- UUID partout, contraintes `NOT NULL` et `CHECK` pertinentes.
- Indexes sur colonnes de filtrage, clés étrangères en cascade maîtrisée.
- Alembic pour toute évolution (no-ops bannis).

### Authentification et autorisation
- JWT **access** court (30 min), **refresh** long (7 jours) avec rotation et révocation.
- Hashage bcrypt via `passlib`, politique de complexité configurable.
- Endpoints:
  - `POST /api/v1/auth/login` (form urlencoded: username/password)
  - `POST /api/v1/auth/refresh` (body: refresh_token)
  - `GET /api/v1/auth/me` (bearer) – profil courant
  - `POST /api/v1/auth/logout` – côté client, + invalidation refresh côté serveur (si stocké)
- RBAC middleware: dépendance FastAPI vérifiant rôle/permission par endpoint.

### Contrats d’API et conventions
- Préfixe: `/api/v1`.
- Réponses paginées: `items`, `total`, `page`, `size`.
- Erreurs: format de type RFC 7807 light `{type, title, status, detail, instance}`.
- Validation Pydantic v2 stricte; dates en ISO 8601, montants en décimaux.

### Services d’intégration (Payfit, Gryzzly)
- Adapteurs/clients isolés sous `domain/integrations/*` + interfaces testables.
- Mode mock activable via env (`*_USE_MOCK=true`).
- Retries et timeouts httpx, logs synthétiques, métriques par endpoint externe.

### Observabilité & SRE
- Endpoints: `/health` (liveness), `/metrics` (Prometheus), `/readiness`.
- Logs JSON corrélés par `X-Request-ID`.
- Compteurs/latences par route FastAPI et par client externe.

### Sécurité
- CORS whitelist configurable.
- En-têtes de sécurité (Nginx + FastAPI): HSTS, X-Content-Type-Options, X-Frame-Options, CSP de base.
- Secrets par variables d’environnement (jamais en repo).
- Rate limiting (Nginx) optionnel.

### Tests
- Unitaires (domain/services), intégration (repos + DB éphémère), e2e API.
- Fixtures DB (transactions rollback), données seed.
- Couverture cible: 80% domain/services.

### Migrations & Seeds
- Alembic: scripts up/down, `autogenerate` contrôlé.
- Script `seed_admin.py` pour créer l’admin par défaut (env de dev). MDP à changer en prod.

### Docker & exécution
- `docker-compose.yml`: postgres, redis, backend, frontend, nginx, mailhog, adminer.
- `docker-compose.dev.yml`: montages volumes, reload, ports exposés.
- Backend: user non-root, multi-stage (build deps + runtime maigre), healthcheck.
- Frontend: installation `--legacy-peer-deps` en dev pour absorber conflits de peer deps.

Commandes clés:
```
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis backend
curl http://localhost:8200/health
# seed admin (dev uniquement)
docker compose exec -e DATABASE_URL=postgresql://plancharge:plancharge123@postgres:5432/plan_charge_v8 backend \
  python scripts/create_admin_user.py
```

### Plan d’implémentation (par incréments)
1) Socle: config, sécurité, CORS, `/health`, `/metrics`, DB + Alembic, users minimal.
2) Auth JWT + refresh rotation, RBAC de base, `users/me`.
3) Noyau plan de charge: `projects`, `assignments`, `forecasts` + endpoints lecture.
4) Intégrations (mock d’abord), services de synchro (tasks async si besoin).
5) Observabilité complète, logs JSON, dashboards Prometheus+Grafana (optionnel).
6) Dureté & perf: indexes, profilage requêtes, tests charge ciblés.
7) Nettoyage/Docs: README, guides run, playbooks incident.

### Stratégie de migration depuis l’existant
- Cartographier tables actuelles → nouvelles tables (mapping champs, typages, enums → tables).
- Scripts ETL (Python + SQL) idempotents, par étapes (users → projets → assignments → forecasts).
- Validation post-migration (comptages, checks d’intégrité, invariants métier).

### Checklist de sortie
- Tests verts (unit/int/e2e), couverture atteinte.
- Scan sécurité (Bandit) et linters OK.
- Health/metrics opérationnels, logs structurés.
- RBAC vérifié, mots de passe admin régénérés.

### Notes
- Maintenir la simplicité: logique métier dans `domain`, I/O dans `api`/`repositories`.
- Pas de logique dans les contrôleurs; orchestrations dans `services`.

