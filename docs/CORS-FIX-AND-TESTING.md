# Correction CORS et Guide de Test

## Problèmes Résolus

### 1. Erreur CORS
**Problème** : Le backend ne retournait pas le header `Access-Control-Allow-Origin`

**Causes** :
- La variable d'environnement était `CORS_ORIGINS` au lieu de `BACKEND_CORS_ORIGINS` 
- Le middleware CORS n'était pas configuré correctement

**Solution** :
1. Renommé `CORS_ORIGINS` en `BACKEND_CORS_ORIGINS` dans `.env`
2. Corrigé la configuration dans `config.py` pour lire correctement la variable
3. Mis à jour `main.py` pour toujours configurer le middleware CORS

### 2. Erreur TypeScript
**Problème** : Syntaxe TypeScript dans les fichiers JavaScript

**Solution** : Suppression de toute la syntaxe TypeScript (voir TYPESCRIPT-FIX-SUMMARY.md)

## Test de l'Application

### 1. Vérifier que les services sont lancés
```bash
docker compose ps
```
Tous les services doivent être "Up"

### 2. Tester l'API directement
```bash
# Test de santé
curl http://localhost:8000/health

# Test de login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@plancharge.com&password=admin123"
```

### 3. Accéder à l'interface Web
1. Ouvrir http://localhost:3000
2. Se connecter avec :
   - Email : admin@plancharge.com
   - Password : admin123

### 4. Vérifier les fonctionnalités
Une fois connecté :
1. **Dashboard** : Statistiques générales
2. **Gryzzly** : 
   - Onglet Sync : Synchronisation manuelle
   - Onglet Users : Liste des utilisateurs
   - Onglet Projects : Liste des projets
   - Onglet Time Entries : Entrées de temps

### 5. Configuration pour API Réelles

Pour utiliser les vraies API :

1. Modifier `.env` :
```env
GRYZZLY_USE_MOCK=false
GRYZZLY_API_KEY=votre-cle-api-gryzzly

PAYFIT_USE_MOCK=false  
PAYFIT_API_KEY=votre-cle-api-payfit
PAYFIT_COMPANY_ID=votre-company-id
```

2. Redémarrer le backend :
```bash
docker compose restart backend
```

## Résolution de Problèmes

### Si l'erreur "string is not defined" persiste :
1. Vider le cache du navigateur
2. Ouvrir la console développeur (F12)
3. Recharger la page avec Ctrl+Shift+R

### Si l'erreur CORS revient :
1. Vérifier que `BACKEND_CORS_ORIGINS` est bien défini dans `.env`
2. Vérifier les logs : `docker compose logs backend`
3. Redémarrer le backend : `docker compose restart backend`

### Pour voir les logs en temps réel :
```bash
# Frontend
docker compose logs -f frontend

# Backend
docker compose logs -f backend
```

## État Final
✅ Frontend compile sans erreurs TypeScript
✅ CORS configuré correctement
✅ Login fonctionnel
✅ Navigation dans l'application
✅ Prêt pour les API réelles