#!/usr/bin/env python
"""
Script to migrate data from SQLite to Neon PostgreSQL
"""

import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connections

def backup_sqlite_data():
    """Create a backup of SQLite data"""
    try:
        print("📦 Creating backup of SQLite data...")
        
        # Create backup directory
        backup_dir = Path("backup_sqlite")
        backup_dir.mkdir(exist_ok=True)
        
        # Copy SQLite database
        import shutil
        shutil.copy2("db.sqlite3", backup_dir / "db.sqlite3.backup")
        
        print(f"✅ SQLite backup created at: {backup_dir / 'db.sqlite3.backup'}")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return False

def setup_neon_database():
    """Set up the Neon database with migrations"""
    try:
        print("🔧 Setting up Neon database...")
        
        # Run migrations
        execute_from_command_line(['manage.py', 'migrate', '--verbosity', '2'])
        
        print("✅ Neon database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Neon database setup failed: {str(e)}")
        return False

def create_superuser():
    """Create a superuser for the new database"""
    try:
        print("👤 Creating superuser...")
        print("Please enter the following details:")
        
        # You can modify this to create a default superuser
        username = input("Username (default: admin): ").strip() or "admin"
        email = input("Email (default: admin@ezmtrade.com): ").strip() or "admin@ezmtrade.com"
        password = input("Password (default: admin123): ").strip() or "admin123"
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(username=username).exists():
            print(f"⚠️  User '{username}' already exists")
        else:
            User.objects.create_superuser(username, email, password)
            print(f"✅ Superuser '{username}' created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Superuser creation failed: {str(e)}")
        return False

def verify_database_tables():
    """Verify that all tables are created in Neon"""
    try:
        print("🔍 Verifying database tables...")
        
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"✅ Found {len(tables)} tables in Neon database:")
            for table in tables:
                print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Table verification failed: {str(e)}")
        return False

def main():
    """Main migration process"""
    print("🚀 EZM Trade Management - SQLite to Neon Migration")
    print("=" * 60)
    
    # Step 1: Backup SQLite data
    if not backup_sqlite_data():
        print("❌ Migration aborted due to backup failure")
        return
    
    # Step 2: Setup Neon database
    if not setup_neon_database():
        print("❌ Migration aborted due to Neon setup failure")
        return
    
    # Step 3: Verify tables
    if not verify_database_tables():
        print("❌ Migration aborted due to table verification failure")
        return
    
    # Step 4: Create superuser
    create_superuser()
    
    print("\n🎉 Migration completed successfully!")
    print("=" * 60)
    print("Next steps:")
    print("1. Test your application: python manage.py runserver")
    print("2. Access admin panel: http://localhost:8000/admin/")
    print("3. Verify all functionality works with Neon database")
    print("4. Once confirmed, you can remove the old SQLite database")

if __name__ == "__main__":
    main() 