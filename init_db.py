#!/usr/bin/env python
"""Initialize the SQLite database with schema and sample data."""

import os
import sys
from app import app, db
from models import User

def init_database():
    """Initialize the database."""
    try:
        print("🔄 Initializing NaijaCipe database...\n")
        
        with app.app_context():
            # Drop all existing tables
            print("  Cleaning up old schema...")
            db.drop_all()
            
            # Create all tables fresh
            db.create_all()
            print("✓ Database schema created")
            
            # Create sample admin and demo user
            admin = User(
                username='admin',
                email='admin@naijacipe.app',
                full_name='Admin User'
            )
            admin.set_password('admin1234')
            
            demo_user = User(
                username='adaeze_cooks',
                email='adaeze@naijacipe.app',
                full_name='Adaeze Cooks'
            )
            demo_user.set_password('demo1234')
            
            db.session.add(admin)
            db.session.add(demo_user)
            db.session.commit()
            
            print("✓ Sample users created")
            print("\n✅ Database initialized successfully!")
            print("\n📝 Test credentials:")
            print("   Admin: admin / admin1234")
            print("   User:  adaeze_cooks / demo1234")
            print(f"\n📁 Database file: naija_cipe.db")
            
            return True
            
    except Exception as err:
        print(f"\n✗ Error initializing database: {err}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)


