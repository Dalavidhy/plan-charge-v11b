# Configuration Azure Entra SSO (OBLIGATOIRE)

Ce document explique comment configurer l'authentification SSO avec Azure Entra (anciennement Azure AD) pour l'application Plan de Charge.

## ⚠️ IMPORTANT: SSO EST OBLIGATOIRE

- **Aucune connexion locale possible** - Le SSO Azure AD est le SEUL moyen de se connecter
- **Domaine restreint** - Seuls les utilisateurs avec une adresse @nda-partners.com sont autorisés
- **Configuration requise** - L'application ne fonctionnera pas sans configuration Azure AD valide

## Configuration Azure Portal

### 1. Créer une App Registration

1. Connectez-vous au [Azure Portal](https://portal.azure.com)
2. Naviguez vers **Azure Active Directory** > **App registrations**
3. Cliquez sur **New registration**
4. Configurez l'application :
   - **Name**: Plan de Charge SSO
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: 
     - Type: Web
     - URI: `http://localhost:3200/auth/callback` (développement)
     - Ajoutez aussi votre URL de production si nécessaire

### 2. Récupérer les identifiants

Après création, notez les informations suivantes :

- **Application (client) ID**: Votre `AZURE_AD_CLIENT_ID`
- **Directory (tenant) ID**: Votre `AZURE_AD_TENANT_ID`

### 3. Créer un secret client

1. Dans votre app registration, allez dans **Certificates & secrets**
2. Cliquez sur **New client secret**
3. Donnez une description et une durée d'expiration
4. **IMPORTANT**: Copiez immédiatement la valeur du secret (`AZURE_AD_CLIENT_SECRET`)
   - Cette valeur ne sera plus visible après

### 4. Configurer les permissions API

1. Allez dans **API permissions**
2. Vérifiez que `User.Read` est présent (ajouté par défaut)
3. Cliquez sur **Grant admin consent** si nécessaire

## Configuration de l'application

### Backend (.env)

```env
# Azure AD Configuration
AZURE_AD_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_AD_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_AD_CLIENT_SECRET=your-client-secret-value
AZURE_AD_REDIRECT_URI=http://localhost:3200/auth/callback

# Activer SSO
FEATURE_SSO=true
```

### Frontend (.env)

```env
# Azure AD Configuration
VITE_AZURE_AD_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
VITE_AZURE_AD_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
VITE_AZURE_AD_REDIRECT_URI=http://localhost:3200/auth/callback
```

## Installation des dépendances

### Backend

```bash
cd backend
pip install -r requirements.txt
# ou avec Docker
docker-compose build backend
```

### Frontend

```bash
cd frontend
npm install
```

## Migration de la base de données

Appliquez la migration pour ajouter le champ `azure_id` aux utilisateurs :

```bash
# Avec Docker
docker-compose exec backend alembic upgrade head

# Sans Docker
cd backend
alembic upgrade head
```

## Utilisation

### Pour les utilisateurs

1. Sur la page de connexion, cliquez sur **"Se connecter avec Microsoft"**
2. Vous serez redirigé vers la page de connexion Microsoft
3. Entrez vos identifiants Azure AD
4. Après authentification, vous serez automatiquement connecté à l'application

### Première connexion

- Lors de la première connexion SSO, un compte utilisateur local est automatiquement créé
- Les informations (email, nom) sont synchronisées depuis Azure AD
- Aucun mot de passe local n'est créé (authentification SSO uniquement)

### Mode hybride

L'application supporte un mode hybride :
- Les utilisateurs peuvent se connecter via SSO (Azure AD)
- Les administrateurs peuvent garder un compte local (email/mot de passe)
- Utile pour les environnements de développement ou les comptes de secours

## Sécurité

### Points importants

1. **Secrets**: Ne jamais commiter les secrets dans le code
2. **HTTPS**: Utilisez HTTPS en production pour les redirect URIs
3. **Tokens**: Les tokens JWT sont stockés de manière sécurisée
4. **Session**: La session expire après le délai configuré

### Redirect URIs en production

Pour la production, mettez à jour les redirect URIs :

1. Dans Azure Portal, ajoutez votre URL de production
2. Mettez à jour les fichiers .env :
   ```env
   AZURE_AD_REDIRECT_URI=https://votre-domaine.com/auth/callback
   VITE_AZURE_AD_REDIRECT_URI=https://votre-domaine.com/auth/callback
   ```

## Dépannage

### Le bouton SSO n'apparaît pas

- Vérifiez que `FEATURE_SSO=true` dans le backend
- Vérifiez que toutes les variables Azure AD sont configurées
- Vérifiez les logs du backend pour les erreurs de configuration

### Erreur "Authentication failed"

- Vérifiez que le secret client est correct
- Vérifiez que le tenant ID et client ID correspondent
- Vérifiez les permissions dans Azure Portal

### Erreur de redirection

- Vérifiez que l'URL de callback est exactement la même dans :
  - Azure Portal
  - Backend .env
  - Frontend .env
- Incluez le port si nécessaire (ex: `:3200`)

### Utilisateur créé mais pas de connexion

- Vérifiez que la migration de base de données a été appliquée
- Vérifiez les logs pour les erreurs de création d'utilisateur

## Support

Pour toute question ou problème :
- Consultez les logs du backend : `docker-compose logs backend`
- Vérifiez la console du navigateur pour les erreurs frontend
- Contactez votre administrateur Azure AD pour les problèmes de permissions