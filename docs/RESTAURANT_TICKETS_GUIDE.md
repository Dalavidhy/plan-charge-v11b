# Guide d'utilisation - Tickets Restaurant

## Vue d'ensemble

La fonctionnalité Tickets Restaurant permet de générer automatiquement les fichiers CSV pour la commande mensuelle de tickets restaurant, en tenant compte des absences PayFit de chaque employé.

## Fonctionnalités principales

### 1. Aperçu des tickets
- Visualisation en temps réel du nombre de tickets par employé
- Calcul automatique basé sur les jours travaillés et les absences PayFit
- Filtrage et tri des employés
- Export de la vue en CSV

### 2. Gestion des matricules
- Association des employés avec leur matricule TR
- Import en masse via fichier CSV
- Modification individuelle des matricules
- Validation automatique des doublons

### 3. Génération des fichiers
- Sélection du mois et de l'année
- Prévisualisation avant génération
- Génération du fichier CSV au format requis
- Téléchargement automatique

## Guide étape par étape

### Étape 1 : Accéder à la fonctionnalité

1. Connectez-vous à l'application
2. Dans le menu principal, cliquez sur "Tickets Restaurant"
3. La page s'ouvre sur l'onglet "Aperçu"

### Étape 2 : Gérer les matricules

#### Import en masse
1. Cliquez sur "Gérer les matricules"
2. Cliquez sur "Importer"
3. Sélectionnez un fichier CSV avec le format :
   ```csv
   email,matricule
   john.doe@company.com,TR001
   jane.smith@company.com,TR002
   ```
4. Confirmez l'import

#### Modification individuelle
1. Dans le modal "Gestion des matricules"
2. Cliquez sur l'icône d'édition à côté d'un employé
3. Saisissez le nouveau matricule
4. Cliquez sur l'icône de sauvegarde

### Étape 3 : Vérifier l'aperçu

1. L'onglet "Aperçu" affiche tous les employés actifs
2. Pour chaque employé, vous voyez :
   - Nom complet
   - Matricule TR
   - Jours travaillés dans le mois
   - Jours d'absence (depuis PayFit)
   - Nombre de tickets calculé
3. Les employés sans matricule sont signalés par un warning ⚠️

### Étape 4 : Générer le fichier

1. Cliquez sur l'onglet "Génération"
2. Sélectionnez le mois et l'année
3. Cliquez sur "Générer"
4. Une barre de progression indique l'avancement
5. Le fichier est automatiquement téléchargé

### Format du fichier généré

Le fichier CSV généré respecte le format suivant :
```csv
Annee;Mois;Matricule;Nb jours
2025;1;TR001;20
2025;1;TR002;18
2025;1;TR003;22
```

- Séparateur : point-virgule (;)
- Encodage : UTF-8 avec BOM (compatible Excel)
- Nom du fichier : `tickets_restaurants_AAAA_mois.csv`

## Calcul des tickets

### Règles de calcul

1. **Jours ouvrables** = Jours du mois - weekends - jours fériés
2. **Jours d'absence** = Somme des absences PayFit approuvées
3. **Tickets** = Jours ouvrables - Jours d'absence

### Jours fériés 2025

Les jours fériés suivants sont automatiquement exclus :
- 1er janvier - Jour de l'an
- 21 avril - Lundi de Pâques
- 1er mai - Fête du travail
- 8 mai - Victoire 1945
- 29 mai - Ascension
- 9 juin - Lundi de Pentecôte
- 14 juillet - Fête nationale
- 15 août - Assomption
- 1er novembre - Toussaint
- 11 novembre - Armistice 1918
- 25 décembre - Noël

### Types d'absences pris en compte

Toutes les absences PayFit avec statut "approved" sont décomptées :
- Congés payés
- RTT
- Congés maladie
- Congés sans solde
- Autres types d'absences

## Résolution des problèmes

### Employé sans matricule
- L'employé apparaît avec un warning dans l'aperçu
- Il ne sera pas inclus dans le fichier généré
- Solution : Assigner un matricule via "Gérer les matricules"

### Absence non décomptée
- Vérifier que l'absence est bien synchronisée depuis PayFit
- Vérifier que le statut est "approved"
- Vérifier les dates de l'absence

### Erreur de génération
- Vérifier qu'au moins un employé a un matricule
- Vérifier les permissions utilisateur
- Consulter les logs d'erreur

## API Endpoints

Pour les intégrations, les endpoints suivants sont disponibles :

- `GET /api/v1/restaurant-tickets-extended/matricules` - Liste des matricules
- `POST /api/v1/restaurant-tickets-extended/preview` - Aperçu pour un mois
- `POST /api/v1/restaurant-tickets-extended/generate` - Génération du CSV
- `GET /api/v1/restaurant-tickets-extended/download/{log_id}` - Téléchargement

## Permissions

- **Consultation** : Tous les utilisateurs actifs
- **Génération** : Utilisateurs avec rôle RH ou Admin
- **Gestion matricules** : Administrateurs uniquement

## Support

Pour toute question ou problème :
1. Consultez d'abord cette documentation
2. Vérifiez les logs d'erreur dans la console
3. Contactez l'équipe support avec les détails de l'erreur