import os
import urllib.parse as urlparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash

# Helper to automatically create PostgreSQL database if it does not exist
def create_postgres_db_if_not_exists(uri):
    result = urlparse.urlparse(uri)
    username = result.username
    password = result.password
    database = result.path[1:]  # strip leading slash
    hostname = result.hostname
    port = result.port or 5432

    try:
        # Connect to default 'postgres' database to check/create the target database
        con = psycopg2.connect(
            dbname='postgres',
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Check if target database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{database}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{database}' does not exist on PostgreSQL server. Creating database '{database}'...")
            cursor.execute(f"CREATE DATABASE {database}")
            print(f"Database '{database}' created successfully.")
        else:
            print(f"Database '{database}' already exists.")
            
        cursor.close()
        con.close()
    except Exception as e:
        print(f"Note: Could not check/create database '{database}' automatically ({e}).")
        print("Please ensure your PostgreSQL server is running and the database exists.")

def init_db():
    # We must import inside the function so app context is set up after config is parsed
    from application import create_app, db
    from application.models import User, Trek, Booking

    app = create_app()
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    # 1. Pre-create the database if using PostgreSQL
    if db_uri.startswith('postgresql'):
        create_postgres_db_if_not_exists(db_uri)

    print("Initializing database tables...")
    with app.app_context():
        # Drop all tables to start fresh
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # 2. Check and seed ONLY the pre-existing Admin user (required for initial log in)
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            print("Seeding pre-existing admin user...")
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                name='System Administrator',
                contact_details='admin@trekout.com',
                role='admin',
                status='active'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
            print("Credentials -> Username: admin, Password: admin123")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    init_db()
    print("Database schema initialization complete!")
