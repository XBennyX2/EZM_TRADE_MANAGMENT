#!/usr/bin/env python
"""
Test Store Manager functionality
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_store_manager_login():
    """Test Store Manager login"""
    print("=== Testing Store Manager Login ===")
    
    client = Client()
    
    # Get Store Manager user
    try:
        store_manager = User.objects.get(username='store_manager1')
        print(f"Found Store Manager: {store_manager.username}, Role: {store_manager.role}")
        
        # Set password and first_login flag
        store_manager.set_password('password123')
        store_manager.is_first_login = False
        store_manager.save()
        
        # Test login
        login_data = {
            'username': 'store_manager1',
            'password': 'password123'
        }
        
        response = client.post('/users/login/', login_data, follow=True)
        print(f"Login response: {response.status_code}")
        
        # Check if we can access the dashboard
        response = client.get('/users/store-manager/')
        print(f"Store Manager dashboard: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Store Manager login successful")
            return client
        else:
            print("✗ Store Manager login failed")
            return None
            
    except User.DoesNotExist:
        print("Store Manager user not found")
        return None

def test_store_manager_functionality(client):
    """Test Store Manager specific functionality"""
    print("\n=== Testing Store Manager Functionality ===")
    
    if not client:
        print("No authenticated client")
        return
    
    # Test various Store Manager pages
    pages = [
        ('/users/store-manager/', 'Main Dashboard'),
        ('/users/store-manager/restock-requests/', 'Restock Requests'),
        ('/users/store-manager/transfer-requests/', 'Transfer Requests'),
        ('/users/store-manager/stock-management/', 'Stock Management'),
    ]
    
    for url, name in pages:
        response = client.get(url)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name}: {response.status_code}")

def test_admin_functionality():
    """Test Admin functionality"""
    print("\n=== Testing Admin Functionality ===")
    
    client = Client()
    
    # Get admin user
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            admin_user.set_password('admin123')
            admin_user.save()
            
            login_data = {
                'username': admin_user.username,
                'password': 'admin123'
            }
            
            response = client.post('/users/login/', login_data)
            print(f"Admin login: {response.status_code}")
            
            # Test admin pages
            pages = [
                ('/users/admin-dashboard/', 'Admin Dashboard'),
                ('/users/admin/manage-users/', 'User Management'),
            ]
            
            for url, name in pages:
                response = client.get(url)
                status = "✓" if response.status_code == 200 else "✗"
                print(f"{status} {name}: {response.status_code}")
                
    except Exception as e:
        print(f"Admin test error: {e}")

if __name__ == "__main__":
    print("Testing Store Manager and Admin Functionality...")
    
    # Test Store Manager
    client = test_store_manager_login()
    test_store_manager_functionality(client)
    
    # Test Admin
    test_admin_functionality()
    
    print("\nStore Manager and Admin testing completed!")
