#!/usr/bin/env python
"""
Verification script for Neon PostgreSQL setup
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
from django.apps import apps

def check_database_connection():
    """Check if database connection is working"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connection: {version[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def check_django_tables():
    """Check if Django tables are created"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
                ORDER BY table_name;
            """)
            django_tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'django_admin_log',
                'django_content_type',
                'django_migrations',
                'django_session'
            ]
            
            missing_tables = [table for table in expected_tables if table not in django_tables]
            
            if missing_tables:
                print(f"⚠️  Missing Django tables: {missing_tables}")
                return False
            else:
                print(f"✅ Django tables: {len(django_tables)} found")
                return True
    except Exception as e:
        print(f"❌ Django tables check failed: {str(e)}")
        return False

def check_app_tables():
    """Check if application tables are created"""
    try:
        app_tables = []
        for app_config in apps.get_app_configs():
            if app_config.name in ['users', 'store', 'Inventory', 'transactions', 'payments', 'webfront']:
                for model in app_config.get_models():
                    app_tables.append(model._meta.db_table)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name NOT LIKE 'django_%'
                ORDER BY table_name;
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in app_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"⚠️  Missing app tables: {missing_tables}")
                return False
            else:
                print(f"✅ App tables: {len(existing_tables)} found")
                return True
    except Exception as e:
        print(f"❌ App tables check failed: {str(e)}")
        return False

def check_migrations():
    """Check if migrations are applied"""
    try:
        print("🔍 Checking migrations...")
        execute_from_command_line(['manage.py', 'showmigrations'])
        return True
    except Exception as e:
        print(f"❌ Migration check failed: {str(e)}")
        return False

def check_superuser():
    """Check if superuser exists"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        superusers = User.objects.filter(is_superuser=True).count()
        if superusers > 0:
            print(f"✅ Superusers found: {superusers}")
            return True
        else:
            print("⚠️  No superusers found")
            return False
    except Exception as e:
        print(f"❌ Superuser check failed: {str(e)}")
        return False

def main():
    """Main verification process"""
    print("🔍 EZM Trade Management - Neon PostgreSQL Verification")
    print("=" * 60)
    
    checks = [
        ("Database Connection", check_database_connection),
        ("Django Tables", check_django_tables),
        ("App Tables", check_app_tables),
        ("Migrations", check_migrations),
        ("Superuser", check_superuser),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {check_name} failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Neon PostgreSQL is working correctly.")
        print("\nNext steps:")
        print("1. Start the server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/")
        print("3. Test your application features")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\nTroubleshooting:")
        print("1. Run: python manage.py migrate")
        print("2. Run: python manage.py createsuperuser")
        print("3. Check your Neon connection string")
        print("4. Verify psycopg2-binary is installed")

if __name__ == "__main__":
    main() 