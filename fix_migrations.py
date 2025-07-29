#!/usr/bin/env python
"""
Script to fix migration dependency issues with Neon PostgreSQL
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def clear_migration_history():
    """Clear the migration history table"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations;")
            print("✅ Cleared migration history")
        return True
    except Exception as e:
        print(f"❌ Failed to clear migration history: {str(e)}")
        return False

def run_migrations_fresh():
    """Run migrations on a fresh database"""
    try:
        print("🔄 Running migrations on fresh database...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity', '2'])
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def create_superuser():
    """Create a superuser"""
    try:
        print("👤 Creating superuser...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("✅ Superuser already exists")
            return True
        
        # Create superuser
        User.objects.create_superuser(
            username='admin',
            email='admin@ezmtrade.com',
            password='admin123'
        )
        print("✅ Superuser created: admin/admin123")
        return True
    except Exception as e:
        print(f"❌ Superuser creation failed: {str(e)}")
        return False

def verify_setup():
    """Verify the setup is working"""
    try:
        print("🔍 Verifying setup...")
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            migration_count = cursor.fetchone()[0]
            print(f"✅ Migration count: {migration_count}")
        
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            table_count = cursor.fetchone()[0]
            print(f"✅ Table count: {table_count}")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main migration fix process"""
    print("🔧 Fixing Migration Issues for Neon PostgreSQL")
    print("=" * 60)
    
    # Step 1: Clear migration history
    if not clear_migration_history():
        print("❌ Failed to clear migration history")
        return
    
    # Step 2: Run migrations fresh
    if not run_migrations_fresh():
        print("❌ Failed to run migrations")
        return
    
    # Step 3: Create superuser
    create_superuser()
    
    # Step 4: Verify setup
    if verify_setup():
        print("\n🎉 Migration fix completed successfully!")
        print("=" * 60)
        print("Your Neon PostgreSQL database is now ready!")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/")
        print("3. Login with: admin/admin123")
        print("4. Test your application features")
    else:
        print("\n⚠️  Setup verification failed. Please check the issues above.")

if __name__ == "__main__":
    main() 