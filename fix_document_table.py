"""
Script pour ajouter les colonnes manquantes à la table document
"""
import psycopg2
import os

# Récupérer l'URL de la base de données depuis les variables d'environnement
db_url = os.environ.get("DATABASE_URL")

try:
    # Connexion à la base de données
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Vérifier si la colonne updated_by existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='document' AND column_name='updated_by'
    """)
    
    if cursor.fetchone() is None:
        print("Ajout de la colonne updated_by à la table document...")
        cursor.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS updated_by INTEGER")
    
    # Vérifier si la colonne renewal_requested existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='document' AND column_name='renewal_requested'
    """)
    
    if cursor.fetchone() is None:
        print("Ajout de la colonne renewal_requested à la table document...")
        cursor.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS renewal_requested BOOLEAN DEFAULT FALSE")
    
    # Vérifier si la colonne renewal_message existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='document' AND column_name='renewal_message'
    """)
    
    if cursor.fetchone() is None:
        print("Ajout de la colonne renewal_message à la table document...")
        cursor.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS renewal_message TEXT")
    
    # Vérifier si la colonne renewal_requested_at existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='document' AND column_name='renewal_requested_at'
    """)
    
    if cursor.fetchone() is None:
        print("Ajout de la colonne renewal_requested_at à la table document...")
        cursor.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS renewal_requested_at TIMESTAMP")
    
    # Vérifier si la colonne renewal_requested_by existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='document' AND column_name='renewal_requested_by'
    """)
    
    if cursor.fetchone() is None:
        print("Ajout de la colonne renewal_requested_by à la table document...")
        cursor.execute("ALTER TABLE document ADD COLUMN IF NOT EXISTS renewal_requested_by INTEGER")
    
    # Valider les changements
    conn.commit()
    print("Colonnes ajoutées avec succès à la table document!")
    
except Exception as e:
    print(f"Erreur: {e}")
    
finally:
    # Fermer la connexion
    if 'conn' in locals():
        cursor.close()
        conn.close()