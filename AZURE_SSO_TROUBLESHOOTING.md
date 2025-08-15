# Guide de dépannage Azure AD SSO

## 🔍 Diagnostic de l'erreur "Nous n'avons pas pu vous connecter"

Cette erreur peut avoir plusieurs causes. Suivez ce guide étape par étape pour identifier et résoudre le problème.

## 1. Vérifier la configuration dans Azure Portal

### ✅ Vérifier l'App Registration

1. Connectez-vous à [Azure Portal](https://portal.azure.com)
2. Allez dans **Azure Active Directory** > **App registrations**
3. Trouvez votre application "Plan de Charge SSO"
4. Vérifiez ces éléments :

#### Application (client) ID
- Doit correspondre exactement à : `5f6d8aed-0572-407e-8981-e379330c5c53`

#### Directory (tenant) ID  
- Doit correspondre exactement à : `1e1ef656-4a7f-4ea3-b5b8-2713d2e6f74d`

### ✅ Vérifier les Redirect URIs

**C'EST LE PROBLÈME LE PLUS COURANT !**

1. Dans votre App Registration, allez dans **Authentication**
2. Dans la section **Platform configurations** > **Web**
3. Vérifiez que cette URL EXACTE est présente :
   ```
   http://localhost:3200/auth/callback
   ```
   
   ⚠️ **ATTENTION** : L'URL doit être EXACTEMENT identique, incluant :
   - Le protocole (`http://` pas `https://`)
   - Le port (`:3200`)
   - Le chemin (`/auth/callback`)

4. Si l'URL n'est pas présente :
   - Cliquez sur **Add a redirect URI**
   - Ajoutez : `http://localhost:3200/auth/callback`
   - Cliquez sur **Save**

### ✅ Vérifier le Client Secret

1. Allez dans **Certificates & secrets**
2. Vérifiez que votre secret n'est pas expiré
3. Si expiré, créez un nouveau secret et mettez à jour le fichier `.env`

## 2. Vérifier la configuration locale

### Exécuter le script de vérification

```bash
python3 scripts/check_azure_config.py
```

Tous les points doivent être marqués avec ✓

### Vérifier les logs du backend

```bash
docker compose logs backend --tail 50
```

Cherchez des messages d'erreur comme :
- `AADSTS50011` : Redirect URI mismatch
- `AADSTS70000` : Invalid authorization code
- `invalid_client` : Client credentials incorrects

## 3. Erreurs communes et solutions

### Erreur : "Redirect URI mismatch"

**Symptôme** : Message d'erreur Azure AD indiquant que l'URI de redirection ne correspond pas

**Solution** :
1. Vérifiez dans Azure Portal que l'URI est EXACTEMENT : `http://localhost:3200/auth/callback`
2. Assurez-vous qu'il n'y a pas d'espace ou de caractère invisible
3. Sauvegardez les changements dans Azure Portal

### Erreur : "Invalid client credentials"

**Symptôme** : Erreur 401 lors de l'échange du code

**Solution** :
1. Vérifiez que le Client Secret dans `.env` est correct
2. Le secret ne doit pas contenir de guillemets
3. Créez un nouveau secret si nécessaire

### Erreur : "Access denied. Only users from authorized domains"

**Symptôme** : L'utilisateur est refusé après authentification

**Solution** :
1. Vérifiez que l'email de l'utilisateur se termine par `@nda-partners.com`
2. L'utilisateur doit faire partie du tenant Azure AD

### Erreur : "duplicate key value violates unique constraint"

**Symptôme** : Erreur de base de données lors de la connexion

**Solution** (déjà appliquée) :
```bash
docker compose exec postgres psql -U plancharge -d plancharge -c "DELETE FROM refresh_tokens;"
docker compose restart backend
```

## 4. Test manuel du flux SSO

### Étape 1 : Générer l'URL de test

```bash
python3 scripts/check_azure_config.py
```

Copiez l'URL générée à la fin du script.

### Étape 2 : Tester dans le navigateur

1. Ouvrez un navigateur en navigation privée
2. Collez l'URL de test
3. Connectez-vous avec vos identifiants Azure AD
4. Observez la redirection :
   - Succès : Redirigé vers `http://localhost:3200/auth/callback?code=...`
   - Échec : Message d'erreur Azure AD

### Étape 3 : Vérifier la console du navigateur

1. Ouvrez les outils de développement (F12)
2. Allez dans l'onglet Console
3. Recherchez les messages d'erreur

## 5. Réinitialisation complète

Si rien ne fonctionne, essayez une réinitialisation complète :

```bash
# 1. Arrêter tous les services
docker compose down

# 2. Nettoyer les volumes Docker
docker compose down -v

# 3. Reconstruire les images
docker compose build

# 4. Redémarrer
docker compose up -d

# 5. Appliquer les migrations
docker compose exec backend alembic upgrade head

# 6. Vérifier la configuration
python3 scripts/check_azure_config.py
```

## 6. Informations de débogage

### Variables d'environnement requises

```env
AZURE_AD_TENANT_ID=1e1ef656-4a7f-4ea3-b5b8-2713d2e6f74d
AZURE_AD_CLIENT_ID=5f6d8aed-0572-407e-8981-e379330c5c53
AZURE_AD_CLIENT_SECRET=SSA8Q~FajGzMhh6.g~hS1MuXWwG-6oX4lHNU_aSG
AZURE_AD_REDIRECT_URI=http://localhost:3200/auth/callback
```

### Endpoints de test

- Backend API Status : http://localhost:8000/api/v1/auth/sso/status
- Frontend : http://localhost:3200
- Callback URL : http://localhost:3200/auth/callback

## 7. Contact support

Si le problème persiste après avoir suivi ce guide :

1. Collectez les informations suivantes :
   - Capture d'écran de l'erreur
   - Logs du backend : `docker compose logs backend --tail 100`
   - Console du navigateur (F12 > Console)
   - Résultat du script : `python3 scripts/check_azure_config.py`

2. Vérifiez avec votre administrateur Azure AD :
   - Que l'application est bien configurée
   - Que votre compte a les permissions nécessaires
   - Que le tenant ID est correct

## Commandes utiles pour le débogage

```bash
# Voir les logs en temps réel
docker compose logs -f backend

# Vérifier l'état des conteneurs
docker compose ps

# Redémarrer le backend
docker compose restart backend

# Vérifier la base de données
docker compose exec postgres psql -U plancharge -d plancharge -c "SELECT email, azure_id FROM users;"

# Nettoyer les tokens
docker compose exec postgres psql -U plancharge -d plancharge -c "DELETE FROM refresh_tokens;"
```