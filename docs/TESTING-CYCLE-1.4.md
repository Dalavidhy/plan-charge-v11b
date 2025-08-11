# Instructions de Test - Cycle 1.4 : Intégration Frontend

## 🚀 Démarrage Rapide

### 1. Lancer Docker Compose

```bash
# Si pas déjà lancé
docker compose up -d

# Vérifier l'état
docker compose ps
```

### 2. Accéder à l'Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Adminer (DB)**: http://localhost:8080
- **MailHog**: http://localhost:8025

### 3. Connexion

- **Email**: admin@plancharge.com
- **Password**: admin123

## 📋 Tests à Effectuer

### Test 1: Authentification

1. Accéder à http://localhost:3000
2. Vous devriez être redirigé vers `/login`
3. Entrer les identifiants ci-dessus
4. Cliquer sur "Sign In"
5. ✅ Vous devriez être redirigé vers le Dashboard

### Test 2: Navigation

1. Une fois connecté, vérifier la barre de navigation latérale
2. Cliquer sur "Dashboard" - affiche les statistiques
3. Cliquer sur "Gryzzly" - affiche l'intégration Gryzzly
4. ✅ Les autres menus (Companies, Projects, Users) sont désactivés

### Test 3: Dashboard Principal

Sur la page Dashboard, vérifier:
- 📊 4 cartes de statistiques en haut
- 📝 Activités récentes (côté gauche)
- 🔗 Statut des intégrations (côté droit)
- ✅ Statut du système (en bas)

### Test 4: Intégration Gryzzly

1. Naviguer vers la page Gryzzly (`/gryzzly`)
2. Vérifier les 4 cartes de statistiques:
   - Total Users (4)
   - Projects (4, dont 3 actifs)
   - Time Entries (66)
   - Total Hours (313.5)

### Test 5: Synchronisation Gryzzly

Dans l'onglet "Sync":
1. Cliquer sur "Full Synchronization"
2. Attendre le message de succès
3. Les statistiques devraient se mettre à jour
4. L'historique de synchronisation apparaît en bas

**Boutons de synchronisation disponibles:**
- Full Synchronization
- Sync Users
- Sync Projects  
- Sync Time

### Test 6: Visualisation des Données

**Onglet Users:**
- Liste des utilisateurs Gryzzly synchronisés
- Recherche par nom/email
- Filtre "Show only unmatched"
- Statut actif/inactif
- Lien avec utilisateur local

**Onglet Projects:**
- Liste des projets avec détails
- Code projet, client, budget
- Technologies utilisées
- Filtre "Active only"

**Onglet Time Entries:**
- Sélection de période (date picker)
- Statistiques: Total, Billable, Validated
- Tableau détaillé des entrées
- Groupé par utilisateur et projet

### Test 7: Déconnexion

1. Cliquer sur l'icône utilisateur en haut à droite
2. Sélectionner "Logout"
3. ✅ Retour à la page de login

## 🔧 Configuration API Réelles

Pour utiliser les vraies API au lieu des données mock:

### 1. Modifier le fichier `.env`

```bash
# Gryzzly API Configuration
GRYZZLY_API_URL=https://api.gryzzly.io/v1
GRYZZLY_API_KEY=votre-cle-api-gryzzly
GRYZZLY_USE_MOCK=false  # Passer à false

# Payfit API Configuration  
PAYFIT_API_URL=https://api.payfit.com/v1
PAYFIT_API_KEY=votre-cle-api-payfit
PAYFIT_COMPANY_ID=votre-company-id
PAYFIT_USE_MOCK=false  # Passer à false
```

### 2. Redémarrer le Backend

```bash
docker compose restart backend
```

### 3. Tester la Synchronisation

Les données réelles seront alors synchronisées depuis les API.

## 🐛 Résolution des Problèmes

### Frontend ne charge pas
```bash
docker compose logs frontend
docker compose restart frontend
```

### Erreur d'authentification
```bash
# Vérifier le backend
docker compose logs backend
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@plancharge.com&password=admin123"
```

### Base de données
```bash
# Accéder à Adminer
http://localhost:8080
# Serveur: postgres
# User: plancharge
# Password: plancharge123
# Database: plan_charge_v8
```

### Voir les emails envoyés
```bash
# MailHog capture tous les emails
http://localhost:8025
```

## 📊 Données de Test

Le système utilise des données mock par défaut:
- **4 utilisateurs** (John Doe, Jane Smith, Bob Wilson, Alice Johnson)
- **4 projets** (E-Commerce, Banking App, Analytics, Migration)
- **66 entrées de temps** sur 30 jours
- **313.5 heures** au total

## ✅ Checklist Complète

- [ ] Docker Compose démarré
- [ ] Login fonctionnel
- [ ] Navigation dans l'app
- [ ] Dashboard visible
- [ ] Page Gryzzly accessible
- [ ] Synchronisation testée
- [ ] Onglet Users fonctionnel
- [ ] Onglet Projects fonctionnel
- [ ] Onglet Time Entries fonctionnel
- [ ] Logout fonctionnel

## 🎯 Points Clés du Cycle 1.4

✅ **Implémenté:**
- Interface React avec Material-UI
- Dashboard principal
- Intégration Gryzzly complète
- Synchronisation avec données mock
- Visualisation des données
- Configuration pour API réelles

⏳ **À venir (Cycle 1.5):**
- Interface Payfit
- Gestion des Companies/Projects
- Gestion des utilisateurs
- Rapports avancés