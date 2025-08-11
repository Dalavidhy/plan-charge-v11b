# Tests Automatisés - Plan Charge v8

## Vue d'ensemble

Plan Charge v8 dispose d'une suite complète de tests automatisés pour assurer la qualité du code et la stabilité des fonctionnalités. Les tests sont organisés en plusieurs catégories et peuvent être exécutés localement ou dans le pipeline CI/CD.

## Structure des Tests

### Tests Backend

```
backend/
├── tests/
│   ├── test_cors.py              # Tests unitaires CORS
│   ├── test_cors_integration.py  # Tests d'intégration CORS
│   └── ...                       # Autres tests
├── run_tests.py                  # Runner de tests catégorisés
├── test_features.py              # Tests de fonctionnalités end-to-end
└── pytest.ini                    # Configuration pytest
```

### Catégories de Tests

1. **CORS** : Configuration et sécurité cross-origin
2. **Auth** : Authentification et autorisation
3. **API** : Endpoints et logique métier
4. **Models** : Modèles de données et ORM

## Exécution des Tests

### Tests Unitaires et d'Intégration

```bash
# Tous les tests
cd backend
python run_tests.py all

# Tests CORS uniquement
python run_tests.py cors

# Tests avec coverage
python -m pytest --cov=app --cov-report=html

# Tests spécifiques
python -m pytest tests/test_cors.py -v
```

### Tests de Fonctionnalités

```bash
# S'assurer que le backend est lancé
cd backend
uvicorn app.main:app --reload --port 8200

# Dans un autre terminal
python test_features.py
```

### Options du Runner de Tests

```bash
# Ignorer les vérifications de qualité
python run_tests.py cors --skip-checks

# Sans coverage
python run_tests.py all --no-coverage

# Aide
python run_tests.py --help
```

## Intégration Continue (CI/CD)

### GitHub Actions

Les tests sont automatiquement exécutés sur chaque push et pull request :

```yaml
# .github/workflows/backend-tests.yml
- Tests unitaires avec coverage
- Linting (flake8)
- Type checking (mypy)
- Security scan (bandit)
- Tests CORS spécifiques
```

### Déclencheurs

- Push sur `main` ou `develop`
- Pull requests vers `main` ou `develop`
- Modifications dans le dossier `backend/`

## Écriture de Tests

### Test Unitaire (Exemple CORS)

```python
import pytest
from app.core.cors import CORSConfig

class TestCORSConfig:
    def test_normalize_origin_valid(self):
        """Test normalizing valid origins"""
        assert CORSConfig.normalize_origin("http://localhost:3000/") == "http://localhost:3000"
    
    def test_parse_origins_string(self):
        """Test parsing comma-separated origins"""
        result = CORSConfig.parse_origins("http://localhost:3000, https://example.com")
        assert result == ["http://localhost:3000", "https://example.com"]
```

### Test d'Intégration (Exemple API)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestCORSIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_headers_allowed_origin(self, client):
        """Test CORS headers for allowed origins"""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3200",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3200"
```

### Test de Fonctionnalité

```python
# Dans test_features.py
def test_authentication(self) -> bool:
    """Test l'authentification"""
    login_data = {
        "username": "admin@plancharge.com",
        "password": "admin123"
    }
    
    response = self.session.post(
        f"{API_V1_URL}/auth/login/access-token",
        data=login_data
    )
    
    return response.status_code == 200
```

## Bonnes Pratiques

### Organisation des Tests

1. **Un fichier par module** : `test_<module>.py`
2. **Classes pour grouper** : `TestCORSConfig`, `TestAuth`
3. **Noms descriptifs** : `test_parse_origins_with_wildcards`
4. **Fixtures pour la réutilisation** : Clients, données de test

### Assertions

```python
# Préférer des assertions spécifiques
assert response.status_code == 200
assert "error" not in response.json()

# Éviter les assertions génériques
assert response.ok  # Trop vague
```

### Mocking

```python
# Mocker les dépendances externes
@patch('app.services.external_api.call')
def test_with_mock(mock_call):
    mock_call.return_value = {"status": "ok"}
    # Test logic here
```

## Coverage

### Génération de Rapports

```bash
# Rapport en terminal
python -m pytest --cov=app --cov-report=term-missing

# Rapport HTML
python -m pytest --cov=app --cov-report=html

# Ouvrir le rapport
open htmlcov/index.html
```

### Objectifs de Coverage

- **Minimum** : 70% de coverage global
- **Cible** : 80% pour le code critique
- **Idéal** : 90%+ pour les nouveaux modules

## Débogage des Tests

### Tests qui échouent

1. **Vérifier l'environnement** : Variables, ports, services
2. **Logs détaillés** : `pytest -vv`
3. **Debugger** : `pytest --pdb`
4. **Un seul test** : `pytest tests/test_cors.py::TestCORSConfig::test_normalize_origin_valid`

### Problèmes Courants

1. **Port déjà utilisé** : Vérifier que le port 8200 est libre
2. **Base de données** : Utiliser une base de test ou mock
3. **CORS** : Vérifier BACKEND_CORS_ORIGINS
4. **Async** : Utiliser `pytest-asyncio` pour les tests async

## Commandes Utiles

```bash
# Installation des dépendances de test
pip install pytest pytest-cov pytest-asyncio flake8 mypy bandit

# Vérifier la configuration pytest
pytest --version
pytest --fixtures

# Nettoyer le cache pytest
find . -type d -name __pycache__ -exec rm -r {} +
find . -type d -name .pytest_cache -exec rm -r {} +

# Lancer les tests en mode watch
pytest-watch
```

## Workflow de Développement

1. **Avant de coder** : Écrire les tests (TDD)
2. **Pendant le développement** : Exécuter les tests concernés
3. **Avant de commit** : Exécuter tous les tests
4. **Après le push** : Vérifier la CI dans GitHub

## Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)