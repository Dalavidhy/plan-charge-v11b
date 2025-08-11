# Configuration CORS - Plan Charge v8

## Vue d'ensemble

Ce document décrit la configuration CORS (Cross-Origin Resource Sharing) du backend Plan Charge v8. La configuration CORS est essentielle pour permettre au frontend (port 3200) de communiquer avec le backend (port 8200).

## Architecture

### Module CORS (`backend/app/core/cors.py`)

Le module CORS fournit une configuration centralisée avec les fonctionnalités suivantes :

1. **Normalisation des origines** : Suppression des slashes finaux et validation du format
2. **Support de formats multiples** : 
   - Chaînes séparées par des virgules
   - Listes Python
   - Format JSON
3. **Support des wildcards** : Permet des patterns comme `http://localhost:*` ou `https://*.example.com`
4. **Validation stricte** : Vérifie que les origines ont le bon format (http:// ou https://)

### Configuration par défaut

```python
# Configuration CORS dans backend/app/core/config.py
BACKEND_CORS_ORIGINS = "http://localhost:3200"

# Options CORS appliquées
{
    "allow_origins": ["http://localhost:3200"],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    "expose_headers": [
        "Content-Length",
        "Content-Range",
        "X-Total-Count",
    ],
    "max_age": 3600,  # 1 heure
}
```

## Configuration

### Variables d'environnement

```bash
# Dans .env ou comme variable d'environnement
BACKEND_CORS_ORIGINS=http://localhost:3200

# Multiples origines
BACKEND_CORS_ORIGINS=http://localhost:3200,https://app.plancharge.com

# Avec wildcards
BACKEND_CORS_ORIGINS=http://localhost:*,https://*.plancharge.com
```

### Docker Compose

```yaml
backend:
  environment:
    - BACKEND_CORS_ORIGINS=http://localhost:3200
```

## Utilisation

### Import et configuration dans FastAPI

```python
from app.core.cors import CORSConfig
from fastapi.middleware.cors import CORSMiddleware

# Parse et valide les origines CORS
origins = CORSConfig.parse_origins(settings.BACKEND_CORS_ORIGINS)

# Applique le middleware CORS
cors_options = CORSConfig.get_cors_options(origins)
app.add_middleware(CORSMiddleware, **cors_options)
```

### Vérification des origines

```python
# Vérifier si une origine est autorisée
is_allowed = CORSConfig.is_origin_allowed(
    "http://localhost:3200", 
    ["http://localhost:3200", "https://app.example.com"]
)
```

## Tests

### Tests unitaires (`backend/tests/test_cors.py`)

Les tests unitaires vérifient :
- La normalisation des origines
- Le parsing de différents formats
- La validation des origines
- Le support des wildcards

### Tests d'intégration (`backend/tests/test_cors_integration.py`)

Les tests d'intégration vérifient :
- Les headers CORS dans les réponses HTTP
- Le blocage des origines non autorisées
- Le support des credentials
- Les requêtes preflight OPTIONS

### Exécution des tests

```bash
# Tous les tests CORS
cd backend
python run_tests.py cors

# Tests unitaires uniquement
python -m pytest tests/test_cors.py -v

# Tests d'intégration uniquement
python -m pytest tests/test_cors_integration.py -v
```

## Débogage

### Logs de configuration

Au démarrage, le backend affiche les origines CORS configurées :

```
CORS Origins configured: ['http://localhost:3200']
```

### Vérification manuelle

```bash
# Test avec curl
curl -i -X OPTIONS http://localhost:8200/api/v1/health \
  -H "Origin: http://localhost:3200" \
  -H "Access-Control-Request-Method: GET"

# Réponse attendue
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3200
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
```

### Erreurs courantes

1. **"CORS policy blocked"** : Vérifier que l'origine du frontend est dans BACKEND_CORS_ORIGINS
2. **"Invalid origin format"** : S'assurer que les origines commencent par http:// ou https://
3. **Headers manquants** : Vérifier que le middleware CORS est bien appliqué dans main.py

## Intégration CI/CD

Les tests CORS sont automatiquement exécutés dans GitHub Actions :

```yaml
# .github/workflows/backend-tests.yml
- name: Run tests with coverage
  run: |
    python -m pytest -v --cov=app

- name: Run specific test categories
  run: |
    python run_tests.py cors --skip-checks
```

## Sécurité

### Bonnes pratiques

1. **Ne jamais utiliser "*"** comme origine en production
2. **Lister explicitement** toutes les origines autorisées
3. **Utiliser HTTPS** en production
4. **Limiter les headers exposés** aux seuls nécessaires
5. **Configurer un max_age approprié** pour réduire les requêtes preflight

### Exemple de configuration production

```bash
# Production
BACKEND_CORS_ORIGINS=https://app.plancharge.com,https://www.plancharge.com

# Staging avec sous-domaines
BACKEND_CORS_ORIGINS=https://*.staging.plancharge.com
```

## Références

- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Tutorial](https://fastapi.tiangolo.com/tutorial/cors/)
- [OWASP CORS Security](https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny)