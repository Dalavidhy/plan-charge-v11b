-- Script pour mettre à jour les matricules dans la table gryzzly_collaborators
-- Basé sur les données fournies

-- David Al Hyar
UPDATE gryzzly_collaborators
SET matricule = '1'
WHERE LOWER(email) = 'david.alhyar@nda-partners.com';

-- Malek Attia
UPDATE gryzzly_collaborators
SET matricule = '16'
WHERE LOWER(email) = 'malek.attia@nda-partners.com';

-- Sami Benouattaf
UPDATE gryzzly_collaborators
SET matricule = '11'
WHERE LOWER(email) = 'sami.benouattaf@nda-partners.com';

-- Thomas Deruy
UPDATE gryzzly_collaborators
SET matricule = '17'
WHERE LOWER(email) = 'thomas.deruy@nda-partners.com';

-- Soukaïna El Kourdi
UPDATE gryzzly_collaborators
SET matricule = '15'
WHERE LOWER(email) = 'soukaina.elkourdi@nda-partners.com';

-- Mohammed elmehdi Elouardi
UPDATE gryzzly_collaborators
SET matricule = '7'
WHERE LOWER(email) = 'elmehdi.elouardi@nda-partners.com'
   OR LOWER(email) = 'mohammed-elmehdi.elouardi@nda-partners.com';

-- Naïl Ferroukhi
UPDATE gryzzly_collaborators
SET matricule = '14'
WHERE LOWER(email) = 'nail.ferroukhi@nda-partners.com';

-- Bérenger Guillotou de Keréver
UPDATE gryzzly_collaborators
SET matricule = '112'
WHERE LOWER(email) = 'berenger.de-kerever@nda-partners.com';

-- Efflam Kervoas
UPDATE gryzzly_collaborators
SET matricule = '9'
WHERE LOWER(email) = 'efflam.kervoas@nda-partners.com';

-- Tristan Le Pennec
UPDATE gryzzly_collaborators
SET matricule = '5'
WHERE LOWER(email) = 'tristan.lepennec@nda-partners.com';

-- Alexandre Linck
UPDATE gryzzly_collaborators
SET matricule = '12'
WHERE LOWER(email) = 'alexandre.linck@nda-partners.com';

-- Vincent Mirzaian
UPDATE gryzzly_collaborators
SET matricule = '2'
WHERE LOWER(email) = 'vincent.mirzaian@nda-partners.com';

-- Valérie Patureau
UPDATE gryzzly_collaborators
SET matricule = '19'
WHERE LOWER(email) = 'valerie.patureau@nda-partners.com';

-- Maxime Rodrigues
UPDATE gryzzly_collaborators
SET matricule = '8'
WHERE LOWER(email) = 'maxime.rodrigues@nda-partners.com';

-- Maria Zavlyanova
UPDATE gryzzly_collaborators
SET matricule = '3'
WHERE LOWER(email) = 'maria.zavlyanova@nda-partners.com';

-- Afficher les résultats pour vérification
SELECT email, first_name, last_name, matricule
FROM gryzzly_collaborators
WHERE matricule IS NOT NULL
ORDER BY CAST(matricule AS INTEGER);
