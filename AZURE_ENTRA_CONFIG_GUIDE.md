# Guide de Configuration Azure Entra ID pour Plan de Charge

## ⚠️ IMPORTANT : Configuration d'Entreprise

Ce guide vous aide à configurer correctement Azure Entra ID (anciennement Azure AD) pour une application d'entreprise avec les bonnes permissions et le bon flux d'authentification.

## 🗑️ Étape 0 : Nettoyer l'ancienne configuration

Si vous avez déjà une App Registration :
1. Allez sur [Azure Portal](https://portal.azure.com)
2. Azure Active Directory > App registrations
3. Trouvez "Plan de Charge SSO"
4. Cliquez dessus puis sur "Delete"
5. Confirmez la suppression

## 🆕 Étape 1 : Créer une nouvelle App Registration

### 1.1 Création de l'application

1. Dans Azure Portal, allez dans **Azure Active Directory** > **App registrations**
2. Cliquez sur **New registration**
3. Configurez comme suit :
   - **Name** : `Plan de Charge - Production`
   - **Supported account types** : `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI** : 
     - Platform: `Single-page application (SPA)`
     - URI: `http://localhost:3200/auth/callback`

4. Cliquez sur **Register**

### 1.2 Noter les identifiants

Après création, notez :
- **Application (client) ID** : `[votre-client-id]`
- **Directory (tenant) ID** : `[votre-tenant-id]`

## 🔐 Étape 2 : Configuration de l'authentification

### 2.1 Platform Configuration

1. Dans votre App Registration, allez dans **Authentication**
2. Vérifiez que vous avez bien :
   - Platform : **Single-page application**
   - Redirect URIs : `http://localhost:3200/auth/callback`
3. Dans **Advanced settings** :
   - ✅ Allow public client flows : **No**
4. Dans **Implicit grant and hybrid flows** :
   - ❌ Access tokens : **Non coché**
   - ❌ ID tokens : **Non coché**
   
   ⚠️ **Important** : Pour une SPA moderne, nous utilisons le flux Authorization Code avec PKCE, PAS le flux implicite !

### 2.2 Ajouter les URLs de production (si nécessaire)

Si vous déployez en production, ajoutez aussi :
- `https://votre-domaine.com/auth/callback`

## 🎫 Étape 3 : Créer un Client Secret (pour le backend)

⚠️ **Note** : Pour une architecture SPA + API Backend, le secret est stocké côté backend uniquement.

1. Allez dans **Certificates & secrets**
2. Cliquez sur **New client secret**
3. Configuration :
   - **Description** : `Plan de Charge Backend Secret`
   - **Expires** : `24 months` (ou selon votre politique)
4. Cliquez sur **Add**
5. **COPIEZ IMMÉDIATEMENT** la valeur du secret (elle ne sera plus visible après)

## 🔑 Étape 4 : Configuration des API Permissions

### 4.1 Permissions Microsoft Graph

1. Allez dans **API permissions**
2. Cliquez sur **Add a permission**
3. Choisissez **Microsoft Graph**
4. Choisissez **Delegated permissions**
5. Ajoutez ces permissions :
   - `User.Read` (lecture du profil utilisateur)
   - `openid` (connexion OpenID)
   - `profile` (informations de profil)
   - `email` (adresse email)
   - `offline_access` (refresh tokens)

### 4.2 Grant Admin Consent

⚠️ **CRUCIAL** : Cette étape est obligatoire pour une app d'entreprise

1. Après avoir ajouté les permissions
2. Cliquez sur **Grant admin consent for [Your Organization]**
3. Confirmez en cliquant sur **Yes**
4. Vérifiez que toutes les permissions ont une coche verte ✅ dans la colonne "Status"

## 🏢 Étape 5 : Configuration Enterprise Application

### 5.1 Accéder à l'Enterprise Application

1. Allez dans **Azure Active Directory** > **Enterprise applications**
2. Recherchez votre application "Plan de Charge - Production"
3. Cliquez dessus

### 5.2 Configuration des utilisateurs

1. Allez dans **Users and groups**
2. Cliquez sur **Add user/group**
3. Ajoutez :
   - Les utilisateurs individuels autorisés
   - OU un groupe contenant tous les utilisateurs @nda-partners.com

### 5.3 Properties

1. Allez dans **Properties**
2. Configurez :
   - **Enabled for users to sign-in?** : Yes
   - **User assignment required?** : Yes (recommandé pour contrôler l'accès)
   - **Visible to users?** : Yes

## 📝 Étape 6 : Configuration du Branding (optionnel)

1. Dans votre App Registration, allez dans **Branding & properties**
2. Configurez :
   - **Logo** : Upload le logo de votre entreprise
   - **Homepage URL** : `https://votre-domaine.com`
   - **Terms of service URL** : (si applicable)
   - **Privacy statement URL** : (si applicable)

## 🔧 Étape 7 : Configuration de l'application

### Variables d'environnement Backend (.env)

```env
# Azure AD Configuration
AZURE_AD_TENANT_ID=[votre-tenant-id]
AZURE_AD_CLIENT_ID=[votre-client-id]
AZURE_AD_CLIENT_SECRET=[votre-secret]
AZURE_AD_REDIRECT_URI=http://localhost:3200/auth/callback

# SSO Settings
FEATURE_SSO=true
SSO_MANDATORY=true
SSO_ALLOWED_DOMAINS=nda-partners.com
```

### Variables d'environnement Frontend (.env)

```env
# Azure AD Configuration (Public - pas de secret ici !)
VITE_AZURE_AD_TENANT_ID=[votre-tenant-id]
VITE_AZURE_AD_CLIENT_ID=[votre-client-id]
VITE_AZURE_AD_REDIRECT_URI=http://localhost:3200/auth/callback
```

## ✅ Étape 8 : Vérification de la configuration

### Checklist Azure Portal

- [ ] App Registration créée en mode Single-tenant
- [ ] Platform configurée en SPA
- [ ] Redirect URI correcte
- [ ] Client Secret créé et copié
- [ ] Permissions accordées (User.Read, openid, profile, email, offline_access)
- [ ] Admin consent donné ✅
- [ ] Enterprise Application configurée
- [ ] Users/Groups assignés
- [ ] User assignment required = Yes

### Test de connexion

1. Ouvrez une fenêtre de navigation privée
2. Allez sur http://localhost:3200
3. Cliquez sur "Se connecter avec Microsoft"
4. Vous devriez voir la page de connexion Microsoft
5. Connectez-vous avec un compte @nda-partners.com
6. **Première connexion** : Acceptez les permissions demandées
7. Vous devriez être redirigé vers l'application

## 🚨 Troubleshooting

### Erreur : "AADSTS65001: The user or administrator has not consented"

**Solution** : L'admin consent n'a pas été donné. Retournez dans API permissions et cliquez sur "Grant admin consent".

### Erreur : "AADSTS50011: Reply URL mismatch"

**Solution** : Vérifiez que l'URL de callback est EXACTEMENT la même dans :
- Azure Portal (Redirect URIs)
- Variable d'environnement AZURE_AD_REDIRECT_URI
- Variable d'environnement VITE_AZURE_AD_REDIRECT_URI

### Erreur : "AADSTS700016: Application not found"

**Solution** : Vérifiez le Client ID et Tenant ID dans vos variables d'environnement.

### Erreur : "AADSTS7000218: Invalid client secret"

**Solution** : Le secret a expiré ou est incorrect. Créez un nouveau secret dans Azure Portal.

### Redirections multiples

**Solution** : Assurez-vous d'utiliser le bon flow (Authorization Code avec PKCE) et non le flow implicite.

## 📚 Références

- [Microsoft identity platform documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [SPA authorization code flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [MSAL.js for SPA](https://github.com/AzureAD/microsoft-authentication-library-for-js)

## 🔒 Sécurité

### Bonnes pratiques

1. **Ne jamais** exposer le Client Secret côté frontend
2. **Toujours** utiliser HTTPS en production
3. **Activer** User assignment required dans Enterprise Application
4. **Limiter** les permissions au strict nécessaire
5. **Renouveler** les secrets régulièrement (avant expiration)
6. **Auditer** régulièrement les accès dans Azure AD Sign-in logs

### Architecture recommandée

```
[Browser/SPA] <--PKCE--> [Azure AD] <--Token--> [Browser/SPA]
     |                                              |
     v                                              v
[Backend API] <--Validate Token--> [Azure AD]
```

Le frontend utilise PKCE (sans secret), le backend valide les tokens.