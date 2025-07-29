#!/usr/bin/env python
"""
Test script to verify Neon PostgreSQL database connection
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

def test_database_connection():
    """Test the database connection"""
    try:
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database connection successful!")
            print(f"PostgreSQL version: {version[0]}")
            
        # Test Django's database check
        print("\n🔍 Running Django database check...")
        execute_from_command_line(['manage.py', 'check', '--database', 'default'])
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_migrations():
    """Test if migrations can be applied"""
    try:
        print("\n📋 Running migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity', '2'])
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Neon PostgreSQL Database Connection")
    print("=" * 50)
    
    # Test connection
    if test_database_connection():
        # Test migrations
        test_migrations()
    else:
        print("\n❌ Database setup failed. Please check your configuration.")
        sys.exit(1) 