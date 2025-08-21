#!/usr/bin/env python3
"""
Script pour exécuter la mise à jour des matricules en production
"""
import os
import sys
import psycopg2
from datetime import datetime

# Configuration de la base de données
DB_CONFIG = {
    'host': 'plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com',
    'port': 5432,
    'database': 'plancharge',
    'user': 'plancharge',
    'password': os.environ.get('DB_PASSWORD', '')
}

# Matricules à mettre à jour
MATRICULES_DATA = [
    ('david.alhyar@nda-partners.com', '1'),
    ('malek.attia@nda-partners.com', '16'),
    ('sami.benouattaf@nda-partners.com', '11'),
    ('thomas.deruy@nda-partners.com', '17'),
    ('soukaina.elkourdi@nda-partners.com', '15'),
    ('elmehdi.elouardi@nda-partners.com', '7'),
    ('mohammed-elmehdi.elouardi@nda-partners.com', '7'),
    ('nail.ferroukhi@nda-partners.com', '14'),
    ('berenger.de-kerever@nda-partners.com', '112'),
    ('efflam.kervoas@nda-partners.com', '9'),
    ('tristan.lepennec@nda-partners.com', '5'),
    ('alexandre.linck@nda-partners.com', '12'),
    ('vincent.mirzaian@nda-partners.com', '2'),
    ('valerie.patureau@nda-partners.com', '19'),
    ('maxime.rodrigues@nda-partners.com', '8'),
    ('maria.zavlyanova@nda-partners.com', '3'),
]

def main():
    """Exécuter la mise à jour des matricules"""
    
    if not DB_CONFIG['password']:
        print("❌ Erreur: DB_PASSWORD n'est pas défini")
        print("Usage: DB_PASSWORD=your_password python execute_matricules_update.py")
        sys.exit(1)
    
    conn = None
    cur = None
    
    try:
        # Connexion à la base de données
        print(f"🔗 Connexion à {DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Démarrer la transaction
        print("🔒 Début de la transaction")
        
        # Créer une table de backup temporaire
        print("💾 Création du backup temporaire...")
        cur.execute("""
            CREATE TEMP TABLE gryzzly_collaborators_backup AS 
            SELECT id, gryzzly_id, email, first_name, last_name, matricule, updated_at 
            FROM gryzzly_collaborators
        """)
        
        # Afficher l'état initial
        cur.execute("""
            SELECT COUNT(*) as total, COUNT(matricule) as with_matricule 
            FROM gryzzly_collaborators
        """)
        total, with_matricule = cur.fetchone()
        print(f"\n📊 État initial:")
        print(f"  - Total collaborateurs: {total}")
        print(f"  - Avec matricule: {with_matricule}")
        print(f"  - Sans matricule: {total - with_matricule}")
        
        # Mettre à jour les matricules
        print(f"\n🔄 Mise à jour de {len(MATRICULES_DATA)} matricules...")
        updated_count = 0
        
        for email, matricule in MATRICULES_DATA:
            cur.execute("""
                UPDATE gryzzly_collaborators 
                SET matricule = %s, updated_at = NOW()
                WHERE LOWER(email) = LOWER(%s)
            """, (matricule, email))
            
            if cur.rowcount > 0:
                updated_count += cur.rowcount
                print(f"  ✅ {email} → matricule {matricule}")
        
        print(f"\n📝 Total mis à jour: {updated_count} lignes")
        
        # Vérifier les résultats
        cur.execute("""
            SELECT COUNT(*) as total, COUNT(matricule) as with_matricule 
            FROM gryzzly_collaborators
        """)
        total_after, with_matricule_after = cur.fetchone()
        
        print(f"\n📊 État final:")
        print(f"  - Total collaborateurs: {total_after}")
        print(f"  - Avec matricule: {with_matricule_after}")
        print(f"  - Sans matricule: {total_after - with_matricule_after}")
        print(f"  - Nouveaux matricules ajoutés: {with_matricule_after - with_matricule}")
        
        # Vérifier les doublons
        cur.execute("""
            SELECT matricule, COUNT(*) as cnt
            FROM gryzzly_collaborators
            WHERE matricule IS NOT NULL
            GROUP BY matricule
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        
        if duplicates:
            print("\n⚠️  ATTENTION: Matricules en double détectés!")
            for mat, cnt in duplicates:
                print(f"  - Matricule {mat}: {cnt} fois")
            print("\n❌ ROLLBACK effectué à cause des doublons")
            conn.rollback()
            sys.exit(1)
        else:
            print("\n✅ Pas de matricules en double")
        
        # Afficher les collaborateurs avec matricules
        print("\n📋 Collaborateurs avec matricules:")
        cur.execute("""
            SELECT matricule, email, first_name || ' ' || last_name as nom
            FROM gryzzly_collaborators
            WHERE matricule IS NOT NULL
            ORDER BY CAST(matricule AS INTEGER)
        """)
        
        for mat, email, nom in cur.fetchall():
            print(f"  {mat:>3} - {nom} ({email})")
        
        # Demander confirmation
        print("\n" + "="*60)
        print("🎯 Résumé de l'intervention:")
        print(f"  - {updated_count} matricules mis à jour")
        print(f"  - Aucun doublon détecté")
        print(f"  - Backup créé dans la table temporaire")
        print("="*60)
        
        # Auto-commit si tout est OK
        if updated_count == 15:
            print("\n✅ COMMIT - Toutes les mises à jour sont validées")
            conn.commit()
            print("🎉 Intervention terminée avec succès!")
        else:
            print(f"\n⚠️  Attention: {updated_count} mises à jour au lieu de 15 attendues")
            print("🔄 ROLLBACK effectué par sécurité")
            conn.rollback()
            sys.exit(1)
            
    except psycopg2.Error as e:
        print(f"\n❌ Erreur PostgreSQL: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("\n🔒 Connexion fermée")

if __name__ == '__main__':
    main()