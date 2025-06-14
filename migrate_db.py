"""
Script pour mettre à jour la base de données selon les modèles actuels
"""
import os
import sqlalchemy as sa
from flask import Flask
from sqlalchemy import text, inspect
from app import app, db
from models import *

def execute_sql(sql, params=None):
    """Execute raw SQL with parameters safely"""
    with app.app_context():
        try:
            if params:
                db.session.execute(text(sql), params)
            else:
                db.session.execute(text(sql))
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error executing SQL: {e}")
            return False

def column_exists(table, column):
    """Check if a column exists in a table"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [c["name"] for c in inspector.get_columns(table)]
        return column in columns

def add_column_if_not_exists(table, column, column_def):
    """Add a column to a table if it doesn't exist"""
    if not column_exists(table, column):
        print(f"Adding column {column} to table {table}")
        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {column_def}"
        return execute_sql(sql)
    return True

def run_migration():
    """
    Exécute les migrations de base de données pour ajouter les colonnes manquantes
    ou mettre à jour la structure de la base de données.
    """
    with app.app_context():
        # Création de toutes les tables qui n'existent pas encore
        db.create_all()
        
        # Ajout des colonnes manquantes
        add_column_if_not_exists('document', 'updated_by', 'INTEGER')
        add_column_if_not_exists('document', 'renewal_requested', 'BOOLEAN DEFAULT FALSE')
        add_column_if_not_exists('document', 'renewal_message', 'TEXT')
        add_column_if_not_exists('document', 'renewal_requested_at', 'TIMESTAMP')
        add_column_if_not_exists('document', 'renewal_requested_by', 'INTEGER')
        
        add_column_if_not_exists('candidate', 'info_renewal_requested', 'BOOLEAN DEFAULT FALSE')
        add_column_if_not_exists('candidate', 'info_renewal_message', 'TEXT')
        add_column_if_not_exists('candidate', 'info_renewal_requested_at', 'TIMESTAMP')
        add_column_if_not_exists('candidate', 'info_renewal_requested_by', 'INTEGER')
        
        add_column_if_not_exists('guardian', 'info_renewal_requested', 'BOOLEAN DEFAULT FALSE')
        add_column_if_not_exists('guardian', 'info_renewal_message', 'TEXT')
        add_column_if_not_exists('guardian', 'info_renewal_requested_at', 'TIMESTAMP')
        add_column_if_not_exists('guardian', 'info_renewal_requested_by', 'INTEGER')
        
        print("Migration de la base de données terminée avec succès.")

if __name__ == "__main__":
    run_migration()