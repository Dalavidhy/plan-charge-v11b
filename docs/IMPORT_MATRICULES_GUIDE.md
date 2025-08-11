# Guide d'Import des Matricules

## Fichiers Disponibles

### 1. Fichier CSV pour import via l'interface
- **Emplacement** : `/template/matricules_production.csv`
- **Format** : email,matricule
- **Utilisation** : Import via l'interface web "Gérer les matricules" > "Importer"

### 2. Script Python pour import direct
- **Emplacement** : `/import_matricules_production.py` (interactif) ou `/import_matricules_auto.py` (automatique)
- **Utilisation** : Import direct en base de données

## Méthode 1 : Import via l'Interface Web (Recommandé)

1. **Connectez-vous** à l'application en tant qu'administrateur
2. **Naviguez** vers "Tickets Restaurant"
3. **Cliquez** sur "Gérer les matricules"
4. **Cliquez** sur "Importer"
5. **Sélectionnez** le fichier `/template/matricules_production.csv`
6. **Confirmez** l'import

## Méthode 2 : Import via Script Python

### Prérequis
- Docker Compose doit être en cours d'exécution
- Base de données PostgreSQL accessible

### Étapes

1. **Démarrer les services** :
```bash
docker-compose up -d
```

2. **Exécuter le script d'import** :
```bash
cd backend
python ../import_matricules_auto.py
```

Ou avec confirmation manuelle :
```bash
cd backend
python ../import_matricules_production.py
```

## Matricules de Production

| Email | Matricule |
|-------|-----------|
| david.alhyar@nda-partners.com | 1 |
| vincent.mirzaian@nda-partners.com | 2 |
| maria.zavlyanova@nda-partners.com | 3 |
| tristan.lepennec@nda-partners.com | 5 |
| elmehdi.elouardi@nda-partners.com | 7 |
| maxime.rodrigues@nda-partners.com | 8 |
| efflam.kervoas@nda-partners.com | 9 |
| sami.benouattaf@nda-partners.com | 11 |
| alexandre.linck@nda-partners.com | 12 |
| nail.ferroukhi@nda-partners.com | 14 |
| soukaina.elkourdi@nda-partners.com | 15 |
| malek.attia@nda-partners.com | 16 |
| thomas.deruy@nda-partners.com | 17 |
| valerie.patureau@nda-partners.com | 19 |
| berenger.de-kerever@nda-partners.com | 112 |

## Vérification

Après l'import, vous pouvez vérifier que les matricules sont correctement associés :

1. **Via l'interface** : Onglet "Aperçu" dans Tickets Restaurant
2. **Via la base de données** :
```sql
SELECT 
    u.email,
    u.first_name,
    u.last_name,
    emm.matricule_tr
FROM employee_matricule_mapping emm
JOIN users u ON u.id = emm.user_id
ORDER BY emm.matricule_tr;
```

## Résolution de Problèmes

### Utilisateur non trouvé
- Vérifiez que l'email dans le CSV correspond exactement à celui en base
- Assurez-vous que l'utilisateur est actif

### Matricule déjà existant
- Le système mettra à jour le matricule existant
- Aucune action requise

### Erreur de connexion à la base
- Vérifiez que Docker Compose est démarré
- Vérifiez les variables d'environnement dans `.env`

## Format du Fichier CSV

Le fichier CSV doit respecter le format suivant :
- **Encodage** : UTF-8
- **Séparateur** : virgule (,)
- **En-têtes** : email,matricule
- **Format matricule** : Numéro simple (1, 2, 3... 112) sans préfixe