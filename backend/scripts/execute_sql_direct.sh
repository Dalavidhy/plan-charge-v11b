#!/bin/bash

# Récupérer le mot de passe depuis SSM
export PGPASSWORD=$(aws ssm get-parameter --name "/plan-charge/prod/db-password" --with-decryption --region eu-west-3 --query 'Parameter.Value' --output text)

if [ -z "$PGPASSWORD" ]; then
    echo "❌ Erreur: Impossible de récupérer le mot de passe"
    exit 1
fi

echo "✅ Mot de passe récupéré depuis SSM"

# Configuration
export PGHOST="plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com"
export PGPORT="5432"
export PGDATABASE="plancharge"
export PGUSER="plancharge"

echo "🔗 Connexion à la base de données..."

# Exécuter le script SQL
psql << 'EOF'
-- =============================================================================
-- Script de mise à jour des matricules - EXECUTION AUTOMATIQUE
-- =============================================================================

BEGIN;

-- Créer backup
CREATE TEMP TABLE gryzzly_collaborators_backup AS 
SELECT id, gryzzly_id, email, first_name, last_name, matricule, updated_at 
FROM gryzzly_collaborators;

-- Afficher état initial
SELECT 'ETAT INITIAL:' as info, 
       COUNT(*) as total, 
       COUNT(matricule) as avec_matricule 
FROM gryzzly_collaborators;

-- Mise à jour des matricules
UPDATE gryzzly_collaborators SET matricule = '1', updated_at = NOW() WHERE LOWER(email) = 'david.alhyar@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '16', updated_at = NOW() WHERE LOWER(email) = 'malek.attia@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '11', updated_at = NOW() WHERE LOWER(email) = 'sami.benouattaf@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '17', updated_at = NOW() WHERE LOWER(email) = 'thomas.deruy@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '15', updated_at = NOW() WHERE LOWER(email) = 'soukaina.elkourdi@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '7', updated_at = NOW() WHERE LOWER(email) = 'elmehdi.elouardi@nda-partners.com' OR LOWER(email) = 'mohammed-elmehdi.elouardi@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '14', updated_at = NOW() WHERE LOWER(email) = 'nail.ferroukhi@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '112', updated_at = NOW() WHERE LOWER(email) = 'berenger.de-kerever@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '9', updated_at = NOW() WHERE LOWER(email) = 'efflam.kervoas@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '5', updated_at = NOW() WHERE LOWER(email) = 'tristan.lepennec@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '12', updated_at = NOW() WHERE LOWER(email) = 'alexandre.linck@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '2', updated_at = NOW() WHERE LOWER(email) = 'vincent.mirzaian@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '19', updated_at = NOW() WHERE LOWER(email) = 'valerie.patureau@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '8', updated_at = NOW() WHERE LOWER(email) = 'maxime.rodrigues@nda-partners.com';
UPDATE gryzzly_collaborators SET matricule = '3', updated_at = NOW() WHERE LOWER(email) = 'maria.zavlyanova@nda-partners.com';

-- Afficher état final
SELECT 'ETAT FINAL:' as info, 
       COUNT(*) as total, 
       COUNT(matricule) as avec_matricule 
FROM gryzzly_collaborators;

-- Afficher les matricules mis à jour
SELECT 'MATRICULES MIS A JOUR:' as info;
SELECT matricule, email, first_name || ' ' || last_name as nom
FROM gryzzly_collaborators
WHERE matricule IS NOT NULL
ORDER BY CAST(matricule AS INTEGER);

-- Vérifier les doublons
SELECT 'VERIFICATION DOUBLONS:' as info;
SELECT CASE 
    WHEN COUNT(*) = 0 THEN 'OK - Pas de doublons'
    ELSE 'ERREUR - Doublons detectes'
END as resultat
FROM (
    SELECT matricule, COUNT(*) 
    FROM gryzzly_collaborators 
    WHERE matricule IS NOT NULL 
    GROUP BY matricule 
    HAVING COUNT(*) > 1
) as doublons;

-- COMMIT automatique si tout est OK
COMMIT;

SELECT 'INTERVENTION TERMINEE AVEC SUCCES!' as resultat;

EOF

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo "✅ Script SQL exécuté avec succès"
    echo "🎉 Les matricules ont été mis à jour en production!"
else
    echo "❌ Erreur lors de l'exécution du script SQL"
    exit 1
fi