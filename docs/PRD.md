# Plan Charge v9 — Product Requirements Document (PRD)

> Ce document décrit la réécriture complète de l’application Plan Charge (v9), couvrant les objectifs produit, la portée, les exigences fonctionnelles et non-fonctionnelles, l’architecture cible, le schéma de base de données, les endpoints API, les règles métier, la stratégie de migration, de test et d’observabilité. Il sert de référence partagée pour les équipes produit, design, backend, frontend, QA et Ops.

## 1. Contexte & Objectifs

- Problème: visibilité limitée sur la charge, les capacités et les allocations des équipes; conflits d’affectation; difficulté à anticiper les risques.
- Objectif: fournir un outil fiable de planification de charge multi-équipes/multi-projets, avec calculs de capacité, détection de surallocation et rapports d’utilisation.
- KPI cibles (6–12 mois):
  - Taux d’utilisation des équipes connu pour 95% des semaines.
  - Réduction de 50% des surallocations (>100% de charge) à horizon 4 semaines.
  - Temps de réponse p95 < 300 ms pour 95% des endpoints.
  - Disponibilité mensuelle ≥ 99.9% (API critique).

## 2. Personas & Cas d’Usage

- Responsable de portefeuille: visualiser l’utilisation par équipe/projet, arbitrer les priorités, valider les plans.
- Manager d’équipe: gérer capacités, calendriers et congés, affecter la charge, détecter les conflits.
- Chef de projet: planifier les tâches/épopées, suivre l’avancement, ajuster les allocations.
- Collaborateur: voir ses affectations, disponibilités, signaler des indisponibilités.

Cas d’usage principaux:
- Visualiser la capacité et les allocations par semaine/mois, par équipe, par personne, par projet.
- Créer/éditer projets, tâches, affectations (en % ou en heures/jour) sur des périodes.
- Gérer calendriers (jours ouvrés) et jours fériés/congés.
- Détecter surallocations, conflits et indisponibilités; suggérer des résolutions.
- Produire rapports (utilisation, charge vs capacité, dérive, risques).
- Rechercher/filtrer par période, équipe, projet, statut, tag.

## 3. Portée v1 (In/Out)

In scope v1:
- Gestion organisations, équipes, utilisateurs, rôles (RBAC) basique.
- Projets, tâches, affectations, capacités, calendriers, jours fériés.
- Détection simple de surallocation (>100%) et conflits de temps.
- Rapports essentiels (utilisation, surcharges, capacité vs charge).
- API REST documentée, pagination/tri/filtre, sécurité JWT.
- Import CSV minimal (capacités, affectations) et export CSV/JSON.

Hors scope v1 (peut être v1.x/v2):
- SSO (SAML/OIDC complet), webhooks externes, intégrations Jira/Asana.
- Planification automatique optimisée, scénarios what‑if avancés.
- Timesheets (réels) et facturation.
- Gestion fine des dépendances entre tâches, diagrammes de Gantt.

## 4. Exigences Fonctionnelles

- Organisations & RBAC: Organisation > Équipes > Membres; rôles: owner, admin, manager, member, viewer.
- Projets & Tâches: projets avec statut, priorité, dates, tags; tâches avec estimations, statut, assignees multiples.
- Calendriers & Capacités: calendrier d’organisation (jours ouvrés), exceptions (jours fériés), capacités par personne (heures/semaine ou heures/jour), congés/absences.
- Affectations: pourcentage ou heures par période (jour/semaine); granularité hebdo par défaut; gestion de fractionnement par plage de dates.
- Détection: surallocation (charge > capacité), indisponibilité (congé/jour férié), double affectation critique.
- Rapports: utilisation par période/équipe/personne/projet; heatmap surallocations; export CSV.
- Historique & Audit: journaliser créations/modifications/suppressions, versionner les objets clés.
- Recherches: filtres combinables (q, tag, statut, période, équipe, projet), tri, pagination.
- Notifications: email in-app (v1: notifications in-app), sommaires hebdo (v1.1).

## 5. Exigences Non‑Fonctionnelles

- Performance: p95 < 300 ms pour lectures, < 600 ms pour écritures courantes; agrégations lourdes via jobs/optimisations.
- Disponibilité: 99.9% API; déploiements sans interruption via migrations compatibles.
- Sécurité: JWT Access/Refresh, RBAC; chiffrage au repos (PG + S3), TLS en transit; protection CSRF (frontend) et rate‑limit.
- RGPD: suppression/anonymisation sur demande; minimisation des données; rétention configurable (audit, logs).
- Observabilité: logs structurés (JSON), métriques (Prometheus), traces (OTel), corrélation request_id.
- Internationalisation: fr/en; fuseaux horaires par utilisateur; formats date/heure localisés.
- Accessibilité: WCAG 2.1 AA côté frontend.
- Scalabilité: horizontal backend; Redis pour cache/queues; Postgres partitionnement par semaines si nécessaire.

## 6. Architecture Cible

- Frontend: React + TypeScript, React Router, React Query, Tailwind/Chakra; E2E via Playwright/Cypress.
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic; Uvicorn/Gunicorn; background jobs via Celery/RQ (+ Redis).
- Base de données: PostgreSQL 14+; UUID v4; contraintes/fk/indexes; vue matérialisée pour agrégations lourdes.
- Cache/Queues: Redis; invalidation par clé; locks pour upserts concurrents.
- Fichiers: S3‑compatible pour pièces jointes/exports.
- Auth: JWT access (15 min), refresh (30 jours), rotation, liste de révocation; hachage argon2/bcrypt.
- Infrastructure Dev: Docker Compose local; CI: tests, lint, typecheck, scans sécurité; CD: migrations auto.

## 7. Modèle de Données (PostgreSQL)

Notes:
- Toutes les tables ont `id UUID PK`, `created_at`, `updated_at`, `deleted_at NULL` (soft delete sélectif pour entités business).
- Indexer les FKs et colonnes de recherche, ajouter contraintes d’unicité pertinentes.
- Horodatages en UTC; champs `tz` ou calculs côté app quand requis.

Schéma principal (simplifié):

### 7.1. Organisations, People & Users

- organizations
  - id (uuid, pk)
  - name (text, unique)
  - timezone (text, default 'Europe/Paris')
  - default_workweek (jsonb: e.g. {mon..fri: 8h})
  - created_at, updated_at, deleted_at

- people (identité canonique planifiable)
  - id (uuid, pk)
  - org_id (uuid fk organizations)
  - full_name (text)
  - active (bool, default true)
  - manager_id (uuid fk people, nullable)
  - cost_center (text, nullable)
  - location (text, nullable)
  - weekly_hours_default (numeric(5,2), nullable)
  - source (text: manual, payfit, gryzzly, import)
  - source_updated_at (timestamptz, nullable)
  - created_at, updated_at, deleted_at

- person_emails (emails multiples/alias)
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - email (citext)
  - kind (text: corporate, personal, integration)
  - is_primary (bool, default false)
  - verified (bool, default false)
  - source (text)
  - UNIQUE(person_id, email)

- person_identifiers (identifiants stables par source)
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - id_type (text: payfit_employee_id, payroll_number, gryzzly_user_id, hr_person_id)
  - id_value (text)
  - source (text)
  - UNIQUE(org_id, id_type, id_value)

- engagements (relation contrat/employabilité)
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - type (text: employee, contractor, mandataire, freelance)
  - start_date (date)
  - end_date (date, nullable)
  - weekly_hours_default (numeric(5,2), nullable)
  - payroll_eligible (bool, default true)
  - notes (text, nullable)
  - source (text)
  - external_contract_id (text, nullable)

- users (compte applicatif — optionnel, lié à une person)
  - id (uuid, pk)
  - org_id (uuid fk organizations)
  - person_id (uuid fk people, nullable)
  - email (citext, unique within org)
  - full_name (text)
  - password_hash (text) [nullable si SSO]
  - locale (text, default 'fr')
  - is_active (bool, default true)
  - created_at, updated_at, deleted_at
  - UNIQUE(org_id, email)

- roles (enum): owner, admin, manager, member, viewer

- user_org_roles
  - id (uuid, pk)
  - org_id (uuid fk)
  - user_id (uuid fk)
  - role (roles)
  - UNIQUE(org_id, user_id)

### 7.2. Équipes & Appartenances

- teams
  - id (uuid, pk)
  - org_id (uuid fk)
  - name (text)
  - lead_id (uuid fk people, nullable)
  - color (text, nullable)
  - created_at, updated_at, deleted_at
  - UNIQUE(org_id, name)

- team_members
  - id (uuid, pk)
  - org_id (uuid fk)
  - team_id (uuid fk)
  - person_id (uuid fk people)
  - active_from (date)
  - active_to (date, nullable)
  - role_in_team (text, nullable)
  - UNIQUE(team_id, person_id, active_from)

### 7.3. Calendriers, Fériés, Capacités, Absences

- calendars
  - id (uuid, pk)
  - org_id (uuid fk)
  - name (text)
  - workweek (jsonb, default_workweek override)
  - created_at, updated_at, deleted_at
  - UNIQUE(org_id, name)

- holidays
  - id (uuid, pk)
  - org_id (uuid fk)
  - calendar_id (uuid fk calendars)
  - date (date)
  - label (text)
  - is_full_day (bool, default true)
  - hours (numeric(5,2), nullable when full_day)
  - UNIQUE(calendar_id, date, label)

- capacities
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - calendar_id (uuid fk calendars, nullable)
  - period_start (date, monday)
  - period_end (date, sunday) [inclus]
  - hours_per_week (numeric(5,2))
  - notes (text, nullable)
  - UNIQUE(person_id, period_start)
  - INDEX(person_id, period_start, period_end)

- absences
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - start_date (date)
  - end_date (date)
  - type (text: vacation, sick, other)
  - hours_per_day (numeric(4,2), nullable)
  - notes (text, nullable)

### 7.4. Projets, Épopées, Tâches

- projects
  - id (uuid, pk)
  - org_id (uuid fk)
  - name (text)
  - key (text) [code court, unique dans l’org]
  - status (text: proposed, active, paused, done, cancelled)
  - priority (int, default 100)
  - start_date (date, nullable), end_date (date, nullable)
  - owner_id (uuid fk people, nullable)
  - team_id (uuid fk teams, nullable)
  - tags (text[])
  - created_at, updated_at, deleted_at
  - UNIQUE(org_id, key)

- project_members
  - id (uuid, pk)
  - org_id (uuid fk)
  - project_id (uuid fk)
  - person_id (uuid fk people)
  - role (text: manager, contributor, viewer)
  - UNIQUE(project_id, person_id)

- epics
  - id (uuid, pk)
  - org_id (uuid fk)
  - project_id (uuid fk)
  - name (text)
  - status (text)
  - order_index (int)

- tasks
  - id (uuid, pk)
  - org_id (uuid fk)
  - project_id (uuid fk)
  - epic_id (uuid fk epics, nullable)
  - title (text)
  - description (text)
  - status (text: todo, in_progress, blocked, done, cancelled)
  - estimate_hours (numeric(6,2), nullable)
  - start_date (date, nullable), due_date (date, nullable)
  - tags (text[])
  - order_index (int)
  - created_by (uuid fk users)
  - created_at, updated_at, deleted_at

- task_assignees
  - id (uuid, pk)
  - org_id (uuid fk)
  - task_id (uuid fk)
  - person_id (uuid fk people)
  - UNIQUE(task_id, person_id)

- task_dependencies
  - id (uuid, pk)
  - org_id (uuid fk)
  - task_id (uuid fk)
  - depends_on_task_id (uuid fk tasks)
  - type (text: blocks, relates)
  - UNIQUE(task_id, depends_on_task_id)

### 7.5. Affectations & Plan de Charge

- allocations
  - id (uuid, pk)
  - org_id (uuid fk)
  - project_id (uuid fk)
  - task_id (uuid fk, nullable si allocation projet)
  - person_id (uuid fk people)
  - start_date (date)
  - end_date (date)
  - percent (numeric(5,2), nullable)
  - hours_per_week (numeric(5,2), nullable)
  - source (text: manual, import, rule)
  - notes (text, nullable)
  - CHECK (percent IS NOT NULL OR hours_per_week IS NOT NULL)
  - INDEX(person_id, start_date, end_date)
  - INDEX(project_id, start_date, end_date)

- allocation_breakdowns (optionnel v1.1 si granularité journalière)
  - id (uuid, pk)
  - allocation_id (uuid fk)
  - date (date)
  - hours (numeric(4,2))
  - UNIQUE(allocation_id, date)

### 7.6. Commentaires, Pièces Jointes, Tags

- comments
  - id (uuid, pk)
  - org_id (uuid fk)
  - entity_type (text: project, task)
  - entity_id (uuid)
  - author_id (uuid fk users)
  - body (text)
  - created_at
  - INDEX(entity_type, entity_id)

- attachments
  - id (uuid, pk)
  - org_id (uuid fk)
  - entity_type (text)
  - entity_id (uuid)
  - filename (text)
  - content_type (text)
  - storage_key (text)
  - size_bytes (int)
  - created_at

- tags
  - id (uuid, pk)
  - org_id (uuid fk)
  - name (text)
  - color (text, nullable)
  - UNIQUE(org_id, name)

- entity_tags
  - id (uuid, pk)
  - org_id (uuid fk)
  - entity_type (text)
  - entity_id (uuid)
  - tag_id (uuid fk tags)
  - UNIQUE(entity_type, entity_id, tag_id)

### 7.7. Sécurité, Sessions, Audit

- api_tokens
  - id (uuid, pk)
  - org_id (uuid fk)
  - name (text)
  - token_hash (text)
  - scopes (text[])
  - created_by (uuid fk users)
  - created_at, revoked_at

- refresh_tokens
  - id (uuid, pk)
  - user_id (uuid fk)
  - org_id (uuid fk)
  - token_hash (text)
  - expires_at (timestamptz)
  - created_at, revoked_at
  - device_info (jsonb)

- audit_logs
  - id (uuid, pk)
  - org_id (uuid fk)
  - actor_id (uuid fk users, nullable system)
  - action (text)
  - entity_type (text)
  - entity_id (uuid)
  - before (jsonb, nullable)
  - after (jsonb, nullable)
  - ip (inet, nullable)
  - user_agent (text, nullable)
  - created_at
  - INDEX(org_id, entity_type, entity_id, created_at)

### 7.8. Intégrations & Staging

- external_providers
  - id (uuid, pk)
  - org_id (uuid fk)
  - provider_key (text: payfit, gryzzly, ticket_resto, ...)
  - name (text)
  - capabilities (jsonb: {roster:bool, absences:bool, timesheets:bool, benefits:bool})
  - auth_type (text)
  - created_at

- external_connections
  - id (uuid, pk)
  - org_id (uuid fk)
  - provider_id (uuid fk external_providers)
  - status (text: connected, error, revoked)
  - credentials (jsonb)
  - webhook_secret (text, nullable)
  - last_sync_at (timestamptz, nullable)
  - error (text, nullable)

- external_accounts
  - id (uuid, pk)
  - org_id (uuid fk)
  - provider_id (uuid fk external_providers)
  - external_user_id (text)
  - person_id (uuid fk people, nullable)
  - raw_profile (jsonb)
  - active (bool, default true)
  - UNIQUE(provider_id, external_user_id)

- stg_roster
  - id (uuid, pk)
  - provider_id (uuid fk)
  - external_user_id (text)
  - payload (jsonb)
  - seen_at (timestamptz)

- stg_absences
  - id (uuid, pk)
  - provider_id (uuid fk)
  - external_absence_id (text)
  - user_external_id (text)
  - start_date (date)
  - end_date (date)
  - type (text)
  - hours_per_day (numeric(4,2), nullable)
  - payload (jsonb)

- stg_timesheets
  - id (uuid, pk)
  - provider_id (uuid fk)
  - external_entry_id (text)
  - user_external_id (text)
  - date (date)
  - hours (numeric(5,2))
  - project_key (text, nullable)
  - task_title (text, nullable)
  - payload (jsonb)

- sync_jobs
  - id (uuid, pk)
  - org_id (uuid fk)
  - provider_id (uuid fk)
  - kind (text: roster, absences, timesheets)
  - state (text: queued, running, success, error)
  - started_at, finished_at
  - stats (jsonb)

- sync_events
  - id (uuid, pk)
  - org_id (uuid fk)
  - provider_id (uuid fk)
  - event_type (text)
  - external_id (text)
  - payload (jsonb)
  - received_at (timestamptz)

- identity_links (journal des décisions de rapprochement)
  - id (uuid, pk)
  - org_id (uuid fk)
  - external_account_id (uuid fk)
  - person_id (uuid fk)
  - action (text: auto_link, manual_link, unlink)
  - reason (text, nullable)
  - score (numeric(4,3), nullable)
  - decided_by (uuid fk users, nullable)
  - decided_at (timestamptz)

- identity_match_rules (whitelist d’alias/traits)
  - id (uuid, pk)
  - org_id (uuid fk)
  - rule (jsonb)
  - created_by (uuid fk users)
  - created_at

### 7.9. Avantages & Éligibilités

- benefit_types
  - id (uuid, pk)
  - org_id (uuid fk)
  - key (text: meal_voucher, health, transport)
  - name (text)
  - UNIQUE(org_id, key)

- benefit_policies
  - id (uuid, pk)
  - org_id (uuid fk)
  - benefit_type_id (uuid fk)
  - rules (jsonb)  # ex: {includes: {engagement_types:["employee"]}, excludes: {locations:["remote-only"]}}
  - active (bool, default true)
  - effective_from (date, nullable)
  - effective_to (date, nullable)

- person_benefits
  - id (uuid, pk)
  - org_id (uuid fk)
  - person_id (uuid fk people)
  - benefit_type_id (uuid fk)
  - eligible (bool)
  - effective_from (date)
  - effective_to (date, nullable)
  - source (text: policy, manual)
  - reason (text, nullable)

## 8. Règles Métier Clés

- Capacité: somme des heures ouvrées selon calendrier − absences − fériés.
- Conversion % ↔ heures: hours = percent × base_hours (par semaine). Base issue de capacities/workweek.
- Surallocation: pour une personne, pour une période (jour/semaine), si somme(allocations en heures) > capacité sur la même période.
- Conflits: affectations qui se chevauchent avec type bloquant (ex: 2 projets à 80% la même semaine ⇒ 160%).
- Priorité: projets avec priorité plus faible en nombre sont servis avant pour résolutions automatiques (v1.1: suggestions).
- Périmètre temporel: calculs au minimum hebdomadaire (lundi‑dimanche), granularité quotidienne optionnelle.
- Fuseaux horaires: stock en UTC, calcule selon timezone de l’org pour les vues par jour.

Identité & Propriété des données:
- Personne canonique: toute planification se fait sur `person_id` (internes, mandataires, freelances).
- Propriété: si Payfit est connecté, il est maître des attributs RH (nom, email corporate, actif) et des absences; sinon source=manual.
- Capacités: dérivées de `weekly_hours_default` (people/engagements) + calendrier; overrides via `capacities`.
- Avantages: éligibilité par défaut via `benefit_policies`; exceptions via `person_benefits`.

Rapprochement d’identité (matching) multi‑sources:
- Normalisation: noms sans accents/casse; emails normalisés; clés phonétiques facultatives.
- Déterministe: lien direct par `external_user_id` déjà connu; par identifiant fort (`payfit_employee_id`, `payroll_number`); ou par email exact existant dans `person_emails`.
- Probabiliste (scores):
  - Nom complet exact: +0.35; phonétique proche: +0.20
  - Date d’entrée ±7j: +0.25
  - Manager/équipe identiques: +0.20
  - Cost center/site identique: +0.15
  - Domaine email identique + local-part proche (Levenshtein ≤2): +0.20
  - Seuils: score ≥ 0.90 ⇒ auto‑link; 0.60–0.90 ⇒ revue; < 0.60 ⇒ aucune correspondance.
- Traçabilité: décisions journalisées dans `identity_links`; règles explicites dans `identity_match_rules`.

## 9. API REST (FastAPI) — Design

Conventions générales:
- Auth: Bearer JWT; `Authorization: Bearer <access_token>`; refresh via `/auth/refresh`.
- Pagination: `page`, `page_size` (max 100); tri `sort=field,-other`.
- Filtrage: query params standards (ex: `status=active`, `team_id=...`, `from=YYYY‑MM‑DD`, `to=...`).
- ETags: `If-None-Match` pour GET, `If-Match` pour PUT/PATCH (optimistic locking via `updated_at`).
- Erreurs: JSON `{error: {code, message, details}}` avec codes HTTP appropriés.

### 9.1 Auth
- POST `/auth/login` {email, password} → {access_token, refresh_token, user}
- POST `/auth/refresh` {refresh_token} → {access_token, refresh_token}
- POST `/auth/logout` {refresh_token}
- POST `/auth/forgot` {email}
- POST `/auth/reset` {token, new_password}

### 9.2 Organisations, People, Utilisateurs, Rôles
- GET `/me` → profil + org par défaut + rôles
- GET `/orgs` | POST `/orgs` | GET `/orgs/{id}` | PATCH `/orgs/{id}` | DELETE soft
- GET `/people` | POST `/people` | GET `/people/{id}` | PATCH | DELETE soft
- GET `/users` | POST `/users` | GET `/users/{id}` | PATCH | DELETE soft (optionnel v1)
- POST `/users/{id}/roles` {role}
- GET `/teams` | POST | GET `/teams/{id}` | PATCH | DELETE
- POST `/teams/{id}/members` {person_id, active_from}
- DELETE `/teams/{id}/members/{person_id}`

Remarque: `team_members` et endpoints associés utilisent désormais `person_id` au lieu de `user_id`.

### 9.3 Calendriers, Capacités, Absences
- GET/POST/PATCH `/calendars`, `/calendars/{id}`
- GET/POST `/calendars/{id}/holidays` | DELETE `{holiday_id}`
- GET `/capacities?person_id&from&to` | POST `/capacities` (bulk upsert support)
- GET/POST/PATCH `/absences`, `/absences/{id}`

### 9.4 Projets, Épopées, Tâches
- GET/POST/PATCH `/projects`, `/projects/{id}` | DELETE
- POST `/projects/{id}/members` | DELETE
- GET/POST/PATCH `/epics`, `/epics/{id}`
- GET `/tasks?project_id&status&assignee_person_id&q&from&to`
- POST `/tasks` | GET `/tasks/{id}` | PATCH | DELETE
- POST `/tasks/{id}/assignees` {person_id} | DELETE
- POST `/tasks/{id}/dependencies` {depends_on_task_id, type} | DELETE

### 9.5 Affectations & Rapports
- GET `/allocations?person_id&project_id&from&to`
- POST `/allocations` (création simple ou bulk: tableau) → retourne détails et conflits détectés
- PATCH `/allocations/{id}` | DELETE
- POST `/allocations:bulk-upsert` {allocations: [...], mode: merge|replace}
- GET `/reports/utilization?group_by=team|person|project&from&to`
- GET `/reports/overbookings?from&to`
- GET `/reports/capacity-vs-load?team_id&from&to`
- GET `/exports/allocations.csv?from&to`

### 9.6 Commentaires, Fichiers, Tags
- GET/POST/PATCH `/comments` | `/comments/{id}`
- POST `/attachments` (pré-signe S3), GET `/attachments/{id}` (signed URL), DELETE
- GET/POST `/tags` | POST `/tags/assign` {entity_type, entity_id, tag_id}

### 9.7 Identité & Intégrations
- GET `/integrations/providers`
- GET/POST `/integrations/connections`
- POST `/integrations/{connection_id}/sync?kind=roster|absences|timesheets&dry_run=true`
- POST `/integrations/{connection_id}/webhook`
- GET `/external-accounts?provider=gryzzly&unlinked=true`
- POST `/external-accounts/{id}/link` {person_id, reason}
- GET `/identity/matches?min_score=0.6`
- POST `/identity/resolve` {external_account_id, action: link|new|ignore, person_id?}

### 9.8 Avantages (Benefits)
- GET `/benefits/types` | POST `/benefits/types`
- GET `/benefits/policies` | POST `/benefits/policies` | PATCH `/benefits/policies/{id}`
- GET `/people/{id}/benefits` | POST `/people/{id}/benefits` (override eligible, period, reason)

### 9.7 Modèles de Payload (extraits)

```json
POST /allocations
{
  "project_id": "...",
  "task_id": "...",
  "person_id": "...",
  "start_date": "2025-01-06",
  "end_date": "2025-02-02",
  "percent": 50,
  "source": "manual",
  "notes": "Sprint 1-4",
  "dry_run": true
}
```
Réponse (dry_run):
```json
{
  "allocation": {"id": null, "effective_hours_per_week": 14.0},
  "conflicts": [
    {"week": "2025-01-13", "overbooking_hours": 6.0, "details": [
      {"allocation_id": "...", "project": "PRJ-1", "percent": 80}
    ]}
  ],
  "warnings": ["holiday on 2025-01-20"]
}
```

## 10. Sécurité & Permissions (RBAC)

- owner: tout, y compris suppression d’org et gestion facturation (si applicable).
- admin: gestion utilisateurs/équipes/projets de l’org.
- manager: gestion des membres de son équipe, capacités, absences; affectations dans projets de l’équipe.
- member: consulter, éditer ses affectations; commenter.
- viewer: lecture seule.
- Scopes API tokens: `read:*`, `write:allocations`, `manage:projects`, etc.

## 11. Stratégie de Migration & Données

- Identifiants: utiliser UUID v4; mapping depuis v8 via table de correspondance si reprise.
- Migrations: Alembic versionnées; `zero-downtime` (ajout colonnes nullable, backfill, switch, drop ancien champ en étape ultérieure).
- Reprise v8 (si existante):
  1) Export v8 (users, teams, projects, tasks, allocations, capacities, calendars)
  2) Normalisation (dates, tz, duplicates)
  3) Import batch idempotent (`external_id`, `source='legacy'`)
  4) Validation par rapports comparatifs (totaux hebdo)

## 12. Plan de Livraison (Phases)

- Phase 0: PRD, UX flows, maquettes, validation technique.
- Phase 1: Schéma DB + Auth + RBAC minimal, CRUD org/users/teams/projects.
- Phase 2: Tâches + Capacités + Calendriers + Absences.
- Phase 3: Affectations + Détection de surallocations + Rapports de base.
- Phase 4: Exports + Import CSV + Notifications in‑app + Audit.
- Phase 5: Durcissement perf/sécu, i18n, A11y, tests E2E, hardening.
- Feature flags: activer progressivement rapports et bulk upserts.

## 13. Tests & Qualité

- Backend: pytest, coverage ≥ 85%; tests unitaires (services/calculs), intégration (repos/API), e2e (scénarios principaux).
- Frontend: tests composants, intégration vues clés; E2E parcours gestion plan de charge.
- Données de test: fixtures semaines continues avec fériés et absences.
- Performance: tests de charge sur endpoints `/reports/*` et `/allocations:bulk-upsert`.
- Sécurité: tests JWT, RBAC, injections SQL, IDOR, rate‑limit.

## 14. Observabilité & Exploitation

- Logs: JSON; niveau info/debug pour dev, warning+ en prod; corrélation `X-Request-ID`.
- Métriques: requêtes par endpoint, latence p50/95/99, erreurs 4xx/5xx, jobs en file, hit/miss cache.
- Traces: OTel; spans pour DB (SQLAlchemy), HTTP, Redis, S3.
- Alertes: erreurs 5xx en hausse, latence p95>500ms, jobs en retard, espace disque PG, mémoire Redis.
- Santé: `/healthz` (liveness) et `/readyz` (readiness) + script `scripts/system-status.sh`.

## 15. UI/UX (Synthèse)

- Vues: Calendrier équipe (hebdo/mensuel), Tableau personne, Vue projet, Rapports.
- Interactions: glisser‑déposer pour ajuster affectations; inline edit pour %/heures.
- Filtres: période, équipe, personne, projet, statut, tag.
- Accessibilité: navigation clavier, contrastes, focus visibles, labels.

## 16. Ouvertures & Risques

- Risques: complexité calcul sur large fenêtre, qualité données d’entrée, changements d’organisation.
- Mitigations: agrégations matérialisées par semaine, jobs de pré‑calcul, validations d’import, feature flags.
- Évolutions: intégrations Jira/Asana, webhooks, scénarios what‑if, suggestions IA.

## 17. Glossaire

- Capacité: heures disponibles sur une période (après calendrier/absences).
- Allocation: temps planifié pour une tâche/projet (en % ou heures).
- Surallocation: somme des allocations > capacité sur période.
- Période: intervalle jalonné (jour, semaine ISO, mois).

---

# Annexes

## A. Indexation & Performances (guidelines)

- Index composés: `(user_id, start_date, end_date)`, `(project_id, start_date)`, `(org_id, status)`.
- Partitions par semaine sur `allocations` si volume > 50M lignes.
- Vues matérialisées hebdo: `utilization_by_user_week(user_id, week_start, hours_allocated, capacity_hours)`.
- Verrous applicatifs (Redis) pour bulk upserts par `(user_id, week)`.

## B. Exemple d’OpenAPI (extrait)

```yaml
openapi: 3.0.3
info:
  title: Plan Charge API
  version: 1.0.0
servers:
  - url: /api
paths:
  /allocations:
    get:
      parameters:
        - in: query
          name: user_id
          schema: { type: string, format: uuid }
        - in: query
          name: from
          schema: { type: string, format: date }
        - in: query
          name: to
          schema: { type: string, format: date }
      responses:
        '200':
          description: OK
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AllocationCreate'
      responses:
        '201': { description: Created }
components:
  schemas:
    AllocationCreate:
      type: object
      required: [project_id, user_id, start_date, end_date]
      properties:
        project_id: { type: string, format: uuid }
        task_id: { type: string, format: uuid, nullable: true }
        user_id: { type: string, format: uuid }
        start_date: { type: string, format: date }
        end_date: { type: string, format: date }
        percent: { type: number, minimum: 0, maximum: 100, nullable: true }
        hours_per_week: { type: number, minimum: 0, nullable: true }
        source: { type: string, enum: [manual, import, rule] }
```

## C. Stratégie de Calcul (résumé)

- Étape 1: Élargir requête aux allocations interférentes pour la fenêtre [from, to].
- Étape 2: Projeter allocations en heures hebdo selon calendrier/capacités.
- Étape 3: Soustraire absences/fériés de la capacité de base.
- Étape 4: Détecter conflits (overbooking) et générer suggestions (v1.1).
- Étape 5: Mettre en cache par `(user_id, week_start)` avec invalidation sur changement.

## D. Formats d’Export CSV

- allocations.csv: `person_email,project_key,task_title,start_date,end_date,percent,hours_per_week`
- capacities.csv: `person_email,period_start,hours_per_week`
- absences.csv: `person_email,start_date,end_date,type`

## E. Checklists d’Acceptance (extraits)

- Créer une équipe, ajouter 3 membres avec capacités distinctes.
- Créer 2 projets; affecter le même membre à 80% sur les deux la même semaine ⇒ surallocation détectée.
- Marquer un jour férié; recalculer capacité et vérifier baisse d’heures disponibles.
- Exporter allocations d’une période; comparer totaux aux rapports d’utilisation.

## F. Intégrations API — Payfit & Gryzzly (spécification d’extraction)

- Objectif: décrire précisément les appels effectués pour synchroniser les données sources dans les tables de staging (`stg_*`) puis les normaliser via le modèle canonique.

- Environnements (env):
  - Gryzzly: `GRYZZLY_API_URL` (par défaut: https://api.gryzzly.com/v1), `GRYZZLY_API_KEY`
  - Payfit: `PAYFIT_API_URL` (par défaut: https://partner-api.payfit.com), `PAYFIT_API_KEY`, `PAYFIT_COMPANY_ID`

- Sécurité: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`.

- Stratégie sync commune:
  - Idempotence: upsert par identifiant externe dans `external_accounts`/`stg_*` (UNIQUE `(provider_id, external_id)`).
  - Pagination: boucles jusqu’à épuisement; conserver `nextPageToken` (Payfit) et `offset/limit` (Gryzzly).
  - Fenêtrage temporel: paramètres `from/to` (Gryzzly déclarations) et périodes (Payfit absences).
  - Limites: 429 → backoff/retry; erreurs 5xx → retry exponentiel; journaliser dans `sync_jobs`/`sync_events`.

### F.1 Gryzzly

- Auth: API Key (Bearer). Endpoints en POST; pagination via `offset/limit`; charge utile JSON; objets renvoyés dans `{ data: [...] }`.

- POST `/users.list`
  - Body: `{ "offset": <int>, "limit": <int> }`
  - Extraction → `stg_roster` et `external_accounts` (provider=gryzzly): `id`, `email`, `name`, `is_disabled`, `role`, `hourly_rate`, `hourly_cost`, `groups`, `created_at`, `updated_at`, `raw_profile` complet.
  - Mapping: `external_user_id = id`; `active = !is_disabled`.

- POST `/projects.list`
  - Body: `{ "offset": <int>, "limit": <int> }`
  - Extraction → `gryzzly_projects` (ou staging dédié): `id`, `name`, `code`, `description`, `customer_id`, `archived_at`, `budget_hours`, `hourly_rate`, `color`, `created_at`, `updated_at`, `raw_profile`.

- POST `/tasks.list`
  - Body: `{ "offset": <int>, "limit": <int>, "project_ids"?: [str] }`
  - Extraction → staging tâches: `id`, `project_id`, `name`, `is_group`, `start_at`, `end_at`, `completed_at`, `budget_type`, `budget_amount`, `hourly_rate`, `hourly_rate_mode`, `planned_duration`, `tags`, `groups`, `created_at`, `updated_at`, `raw_profile`.

- POST `/declarations.list`
  - Body: `{ "offset": <int>, "limit": <int<=1000>, "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "user_ids": [str], "task_ids": [str] }`
  - Stratégie: lister d’abord tous les utilisateurs (`/users.list` → `get_all_users`) puis appeler `/declarations.list` par utilisateur (limite 1000/req) avec filtrage optionnel par `task_ids`.
  - Extraction → `stg_timesheets` (ou `gryzzly_time_entries`): `id`, `user_id`, `task_id`, `date`, `duration` (→ `hours=duration/3600`, `days` calculé: 1.0 si ≥7h; 0.5 si 3–7h; sinon `hours/8`), `description`, `hourly_cost`, `edited_by`, `created_at`, `updated_at`, `raw_profile`.

- Recos: limite ~50 req/10s; respecter Retry-After; fenêtrage incrémental des déclarations (rolling) et full sync périodique users/projects/tasks.

### F.2 Payfit

- Auth: API Key (Bearer) + `company_id` dans le chemin.
- Particularités: GET avec pagination via `meta.nextPageToken`; taille de page `maxResults`.

- GET `/companies/{company_id}/collaborators`
  - Query: `maxResults=50`, `nextPageToken` (si présent), `includeInProgressContracts=false`.
  - Extraction → `stg_roster` (provider=payfit): `id`, `matricule`, `firstName`, `lastName`, `secondLastName`, `birthName`, `birthDate`, `terminationDate`, `gender`, `emails[] {email,type}`, `managerId`, `teamName`, `nationality`, `countryOfBirth`, `contracts[] {id,startDate,endDate,status}`, `phoneNumbers[]`, `addresses[]`, autres champs → `raw_profile`.
  - Mapping: `person_identifiers` (`payfit_employee_id=id`, `payroll_number=matricule` si présent), `person_emails` (type: professional→corporate, personal→personal).

- GET `/companies/{company_id}/contracts`
  - Query: `maxResults=50`, `nextPageToken`.
  - Extraction → staging contrats: `contractId`, `collaboratorId`, `startDate`, `endDate?`, `status`, `jobName?`, `standardWeeklyHours?`, `fullTimeEquivalent?`, `isFullTime?`, `probationEndDate?` → normalisation vers `engagements` (`weekly_hours_default = standardWeeklyHours`).

- Absences (selon disponibilité API partenaire):
  - Endpoint typique: GET `/companies/{company_id}/absences?from=YYYY-MM-DD&to=YYYY-MM-DD&status=approved|pending`.
  - Extraction → `stg_absences`: `id`, `contractId`, `startDate {date, moment}`, `endDate {date, moment}`, `type`, `status` → normalisation `payfit_absences` puis `absences` (person_id) avec durée calculée.
  - Fenêtrage: 90 jours passés + 60 jours futurs; relecture des statuts `pending`.

- Recos: itérer jusqu’à absence de `nextPageToken`; upsert idempotent par `id`; minimiser/chiffrer données sensibles (SSN/IBAN/BIC) et purger selon politique.

### F.3 Mapping → Modèle canonique
- Roster Payfit → `people`, `person_emails`, `person_identifiers`, `engagements` (heures hebdo dérivées).
- Users Gryzzly → `external_accounts` (provider=gryzzly); lien vers `people` via matching d’identité.
- Déclarations Gryzzly → `stg_timesheets` puis reporting réel vs planifié; pas d’impact direct sur allocations v1.
- Absences Payfit → `absences` (person_id) après mapping `contractId`→collaborator→person via `person_identifiers`/`external_accounts`.

### F.4 Échec, Retry, Observabilité
- 401/403: mettre `external_connections.status=error`, alerter.
- 429: respecter `Retry-After`; backoff exponentiel sinon.
- 5xx: retry exponentiel (3 tentatives).
- Journal: `sync_jobs` (state, stats), `sync_events` (raw events/webhooks), `identity_links` (décisions de rapprochement).
