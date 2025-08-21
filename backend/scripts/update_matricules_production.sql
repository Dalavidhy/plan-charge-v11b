-- =============================================================================
-- Script de mise à jour des matricules dans gryzzly_collaborators
-- Base de données : Production AWS RDS
-- Date : 2025-01-21
-- Auteur : NDA Partners
-- =============================================================================
--
-- IMPORTANT : Ce script doit être exécuté dans une transaction
-- En cas de problème, faire ROLLBACK au lieu de COMMIT
-- =============================================================================

-- Démarrer la transaction
BEGIN;

-- =============================================================================
-- 1. BACKUP - Créer une table temporaire de sauvegarde
-- =============================================================================
CREATE TEMP TABLE gryzzly_collaborators_backup_20250121 AS
SELECT id, gryzzly_id, email, first_name, last_name, matricule, updated_at
FROM gryzzly_collaborators;

RAISE NOTICE 'Backup créé dans gryzzly_collaborators_backup_20250121';

-- =============================================================================
-- 2. ÉTAT INITIAL - Afficher les statistiques avant modification
-- =============================================================================
DO $$
DECLARE
    total_count INTEGER;
    with_matricule_count INTEGER;
BEGIN
    SELECT COUNT(*), COUNT(matricule)
    INTO total_count, with_matricule_count
    FROM gryzzly_collaborators;

    RAISE NOTICE '';
    RAISE NOTICE '=== ÉTAT INITIAL ===';
    RAISE NOTICE 'Total collaborateurs: %', total_count;
    RAISE NOTICE 'Avec matricule: %', with_matricule_count;
    RAISE NOTICE 'Sans matricule: %', total_count - with_matricule_count;
    RAISE NOTICE '';
END $$;

-- Afficher les collaborateurs qui vont être mis à jour
SELECT 'À METTRE À JOUR:' as status, email,
       COALESCE(matricule, 'NULL') as matricule_actuel
FROM gryzzly_collaborators
WHERE LOWER(email) IN (
    'david.alhyar@nda-partners.com',
    'malek.attia@nda-partners.com',
    'sami.benouattaf@nda-partners.com',
    'thomas.deruy@nda-partners.com',
    'soukaina.elkourdi@nda-partners.com',
    'elmehdi.elouardi@nda-partners.com',
    'mohammed-elmehdi.elouardi@nda-partners.com',
    'nail.ferroukhi@nda-partners.com',
    'berenger.de-kerever@nda-partners.com',
    'efflam.kervoas@nda-partners.com',
    'tristan.lepennec@nda-partners.com',
    'alexandre.linck@nda-partners.com',
    'vincent.mirzaian@nda-partners.com',
    'valerie.patureau@nda-partners.com',
    'maxime.rodrigues@nda-partners.com',
    'maria.zavlyanova@nda-partners.com'
)
ORDER BY email;

-- =============================================================================
-- 3. MISE À JOUR DES MATRICULES
-- =============================================================================

-- David Al Hyar
UPDATE gryzzly_collaborators
SET matricule = '1',
    updated_at = NOW()
WHERE LOWER(email) = 'david.alhyar@nda-partners.com';

-- Malek Attia
UPDATE gryzzly_collaborators
SET matricule = '16',
    updated_at = NOW()
WHERE LOWER(email) = 'malek.attia@nda-partners.com';

-- Sami Benouattaf
UPDATE gryzzly_collaborators
SET matricule = '11',
    updated_at = NOW()
WHERE LOWER(email) = 'sami.benouattaf@nda-partners.com';

-- Thomas Deruy
UPDATE gryzzly_collaborators
SET matricule = '17',
    updated_at = NOW()
WHERE LOWER(email) = 'thomas.deruy@nda-partners.com';

-- Soukaïna El Kourdi
UPDATE gryzzly_collaborators
SET matricule = '15',
    updated_at = NOW()
WHERE LOWER(email) = 'soukaina.elkourdi@nda-partners.com';

-- Mohammed elmehdi Elouardi (2 emails possibles)
UPDATE gryzzly_collaborators
SET matricule = '7',
    updated_at = NOW()
WHERE LOWER(email) = 'elmehdi.elouardi@nda-partners.com'
   OR LOWER(email) = 'mohammed-elmehdi.elouardi@nda-partners.com';

-- Naïl Ferroukhi
UPDATE gryzzly_collaborators
SET matricule = '14',
    updated_at = NOW()
WHERE LOWER(email) = 'nail.ferroukhi@nda-partners.com';

-- Bérenger Guillotou de Keréver
UPDATE gryzzly_collaborators
SET matricule = '112',
    updated_at = NOW()
WHERE LOWER(email) = 'berenger.de-kerever@nda-partners.com';

-- Efflam Kervoas
UPDATE gryzzly_collaborators
SET matricule = '9',
    updated_at = NOW()
WHERE LOWER(email) = 'efflam.kervoas@nda-partners.com';

-- Tristan Le Pennec
UPDATE gryzzly_collaborators
SET matricule = '5',
    updated_at = NOW()
WHERE LOWER(email) = 'tristan.lepennec@nda-partners.com';

-- Alexandre Linck
UPDATE gryzzly_collaborators
SET matricule = '12',
    updated_at = NOW()
WHERE LOWER(email) = 'alexandre.linck@nda-partners.com';

-- Vincent Mirzaian
UPDATE gryzzly_collaborators
SET matricule = '2',
    updated_at = NOW()
WHERE LOWER(email) = 'vincent.mirzaian@nda-partners.com';

-- Valérie Patureau
UPDATE gryzzly_collaborators
SET matricule = '19',
    updated_at = NOW()
WHERE LOWER(email) = 'valerie.patureau@nda-partners.com';

-- Maxime Rodrigues
UPDATE gryzzly_collaborators
SET matricule = '8',
    updated_at = NOW()
WHERE LOWER(email) = 'maxime.rodrigues@nda-partners.com';

-- Maria Zavlyanova
UPDATE gryzzly_collaborators
SET matricule = '3',
    updated_at = NOW()
WHERE LOWER(email) = 'maria.zavlyanova@nda-partners.com';

-- =============================================================================
-- 4. VÉRIFICATIONS APRÈS MISE À JOUR
-- =============================================================================

-- Compter les modifications effectuées
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO updated_count
    FROM gryzzly_collaborators gc
    JOIN gryzzly_collaborators_backup_20250121 gcb ON gc.id = gcb.id
    WHERE (gcb.matricule IS NULL OR gcb.matricule = '')
      AND gc.matricule IS NOT NULL;

    RAISE NOTICE '';
    RAISE NOTICE '=== RÉSULTAT ===';
    RAISE NOTICE 'Nombre de lignes mises à jour: %', updated_count;
    RAISE NOTICE '';
END $$;

-- Afficher l'état final
DO $$
DECLARE
    total_count INTEGER;
    with_matricule_count INTEGER;
BEGIN
    SELECT COUNT(*), COUNT(matricule)
    INTO total_count, with_matricule_count
    FROM gryzzly_collaborators;

    RAISE NOTICE '=== ÉTAT FINAL ===';
    RAISE NOTICE 'Total collaborateurs: %', total_count;
    RAISE NOTICE 'Avec matricule: %', with_matricule_count;
    RAISE NOTICE 'Sans matricule: %', total_count - with_matricule_count;
    RAISE NOTICE '';
END $$;

-- Afficher les collaborateurs avec leurs nouveaux matricules
SELECT
    matricule,
    email,
    first_name || ' ' || last_name as nom_complet,
    CASE
        WHEN gcb.matricule IS NULL OR gcb.matricule = '' THEN 'NOUVEAU'
        WHEN gcb.matricule != gc.matricule THEN 'MODIFIÉ'
        ELSE 'INCHANGÉ'
    END as statut
FROM gryzzly_collaborators gc
LEFT JOIN gryzzly_collaborators_backup_20250121 gcb ON gc.id = gcb.id
WHERE gc.matricule IS NOT NULL
ORDER BY CAST(gc.matricule AS INTEGER);

-- =============================================================================
-- 5. VALIDATION FINALE
-- =============================================================================

-- Vérifier qu'il n'y a pas de doublons de matricules
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO duplicate_count
    FROM (
        SELECT matricule, COUNT(*) as cnt
        FROM gryzzly_collaborators
        WHERE matricule IS NOT NULL
        GROUP BY matricule
        HAVING COUNT(*) > 1
    ) duplicates;

    IF duplicate_count > 0 THEN
        RAISE EXCEPTION 'ERREUR: Des matricules en double ont été détectés!';
    ELSE
        RAISE NOTICE '✓ Pas de matricules en double';
    END IF;
END $$;

-- Vérifier que tous les matricules attendus sont présents
DO $$
DECLARE
    expected_matricules TEXT[] := ARRAY['1','2','3','5','7','8','9','11','12','14','15','16','17','19','112'];
    missing_matricules TEXT[];
BEGIN
    SELECT ARRAY_AGG(mat)
    INTO missing_matricules
    FROM UNNEST(expected_matricules) mat
    WHERE mat NOT IN (
        SELECT matricule
        FROM gryzzly_collaborators
        WHERE matricule IS NOT NULL
    );

    IF array_length(missing_matricules, 1) > 0 THEN
        RAISE WARNING 'Matricules manquants: %', array_to_string(missing_matricules, ', ');
    ELSE
        RAISE NOTICE '✓ Tous les matricules attendus sont présents';
    END IF;
END $$;

-- =============================================================================
-- 6. DÉCISION FINALE
-- =============================================================================
--
-- IMPORTANT: Examinez les résultats ci-dessus avant de valider
--
-- Si tout est correct, exécutez : COMMIT;
-- En cas de problème, exécutez : ROLLBACK;
--
-- =============================================================================

-- Pour voir les différences détaillées (optionnel)
-- SELECT
--     gc.email,
--     gcb.matricule as ancien_matricule,
--     gc.matricule as nouveau_matricule
-- FROM gryzzly_collaborators gc
-- JOIN gryzzly_collaborators_backup_20250121 gcb ON gc.id = gcb.id
-- WHERE gcb.matricule IS DISTINCT FROM gc.matricule
-- ORDER BY gc.email;
