# Test de l'API Gryzzly

## Configuration Actuelle

- **API URL** : https://api.gryzzly.io/v1
- **API KEY** : Configurée dans .env
- **USE_MOCK** : false

## Erreur Rencontrée

```
httpx.HTTPStatusError: Client error '405 Method Not Allowed' for url 'https://api.gryzzly.io/v1/users?page=1&per_page=100'
```

L'endpoint `/users` retourne une erreur 405, ce qui signifie que la méthode HTTP (GET) n'est pas autorisée ou que l'endpoint n'existe pas.

## Solutions Possibles

1. **Vérifier la documentation de l'API Gryzzly** pour connaître les vrais endpoints
2. **Adapter le client** pour utiliser les bons endpoints
3. **Tester avec curl** pour identifier les endpoints disponibles

## Test Manuel de l'API

Pour tester manuellement l'API Gryzzly :

```bash
# Test de l'endpoint users
curl -X GET "https://api.gryzzly.io/v1/users" \
  -H "Authorization: Bearer yK2ub8bg4xgThndR4_NHiD6_k-l7Zxdb" \
  -H "Accept: application/json"

# Ou essayer d'autres endpoints possibles
# /employees, /team, /members, etc.
```

## Prochaines Étapes

1. Identifier les vrais endpoints de l'API Gryzzly
2. Mettre à jour le client pour utiliser ces endpoints
3. Relancer la synchronisation