import os
from flask import Flask
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define database connection
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL not set. Cannot proceed with database migration.")
    exit(1)

# Create engine and session
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def execute_sql(sql, params=None):
    """Execute raw SQL with parameters safely"""
    with engine.connect() as connection:
        try:
            if params:
                result = connection.execute(text(sql), params)
            else:
                result = connection.execute(text(sql))
            connection.commit()
            return result
        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            connection.rollback()
            raise

def column_exists(table, column):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns(table)]
    return column in columns

def add_column_if_not_exists(table, column, column_def):
    """Add a column to a table if it doesn't exist"""
    # Scape table name with quotes for PostgreSQL
    quoted_table = f'"{table}"'
    if not column_exists(table, column):
        logger.info(f"Adding column {column} to table {table}")
        sql = f'ALTER TABLE {quoted_table} ADD COLUMN {column} {column_def}'
        execute_sql(sql)
        return True
    else:
        logger.info(f"Column {column} already exists in table {table}")
        return False
        
def main():
    """Main migration function"""
    try:
        # Add updated_at and last_login columns to user table
        add_column_if_not_exists("user", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_not_exists("user", "last_login", "TIMESTAMP")
        
        # Add promotion_year and info_renewal fields to candidate table
        add_column_if_not_exists("candidate", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_not_exists("candidate", "promotion_year", "INTEGER")
        add_column_if_not_exists("candidate", "info_renewal_requested", "BOOLEAN DEFAULT FALSE")
        add_column_if_not_exists("candidate", "info_renewal_message", "TEXT")
        add_column_if_not_exists("candidate", "info_renewal_requested_at", "TIMESTAMP")
        add_column_if_not_exists("candidate", "info_renewal_requested_by", "INTEGER REFERENCES \"user\" (id)")
        
        # Add updated_at and info_renewal fields to guardian table
        add_column_if_not_exists("guardian", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_not_exists("guardian", "info_renewal_requested", "BOOLEAN DEFAULT FALSE")
        add_column_if_not_exists("guardian", "info_renewal_message", "TEXT")
        add_column_if_not_exists("guardian", "info_renewal_requested_at", "TIMESTAMP")
        add_column_if_not_exists("guardian", "info_renewal_requested_by", "INTEGER REFERENCES \"user\" (id)")
        
        # Add promotion_year and updated_at to application table
        add_column_if_not_exists("application", "promotion_year", "INTEGER")
        add_column_if_not_exists("application", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        # Add renewal fields to document table
        add_column_if_not_exists("document", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_not_exists("document", "updated_by", "INTEGER REFERENCES \"user\" (id)")
        add_column_if_not_exists("document", "renewal_requested", "BOOLEAN DEFAULT FALSE")
        add_column_if_not_exists("document", "renewal_message", "TEXT")
        add_column_if_not_exists("document", "renewal_requested_at", "TIMESTAMP")
        add_column_if_not_exists("document", "renewal_requested_by", "INTEGER REFERENCES \"user\" (id)")
        
        # Create new ApplicationPeriod table if it doesn't exist
        inspector = inspect(engine)
        if 'application_period' not in inspector.get_table_names():
            logger.info("Creating application_period table")
            sql = """
            CREATE TABLE application_period (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                promotion_year INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES "user" (id),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            execute_sql(sql)
            
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        

if __name__ == "__main__":
    main()