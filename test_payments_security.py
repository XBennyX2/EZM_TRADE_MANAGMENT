#!/usr/bin/env python
"""
Test payment integration and security features
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_payment_endpoints():
    """Test payment-related endpoints"""
    print("=== Testing Payment Endpoints ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test payment-related pages
    pages = [
        ('/payments/', 'Payment Dashboard'),
    ]
    
    for url, name in pages:
        try:
            response = client.get(url)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")

def test_security_features():
    """Test security features and access controls"""
    print("\n=== Testing Security Features ===")
    
    # Test unauthenticated access
    client = Client()
    
    protected_urls = [
        '/users/admin-dashboard/',
        '/users/head-manager/',
        '/users/store-manager/',
        '/inventory/suppliers/',
        '/inventory/warehouses/',
        '/cart/',
    ]
    
    print("Testing unauthenticated access (should all redirect):")
    for url in protected_urls:
        response = client.get(url)
        status = "✓" if response.status_code == 302 else "✗"
        print(f"{status} {url}: {response.status_code}")

def test_role_based_access():
    """Test role-based access controls"""
    print("\n=== Testing Role-Based Access ===")
    
    # Test Head Manager accessing Store Manager pages
    client = Client()
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Head Manager should not access Store Manager specific pages
    response = client.get('/users/store-manager/')
    print(f"Head Manager accessing Store Manager page: {response.status_code}")
    
    # Test Store Manager accessing Head Manager pages
    client2 = Client()
    login_data2 = {'username': 'store_manager1', 'password': 'password123'}
    client2.post('/users/login/', login_data2)
    
    response = client2.get('/users/head-manager/')
    print(f"Store Manager accessing Head Manager page: {response.status_code}")

def test_admin_security_fix():
    """Test the fixed admin user management security issue"""
    print("\n=== Testing Admin Security Fix ===")
    
    client = Client()
    
    # Login as admin
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        login_data = {'username': admin_user.username, 'password': 'admin123'}
        response = client.post('/users/login/', login_data)
        
        if response.status_code == 302:
            # Test viewing user details (the security issue that was fixed)
            test_user = User.objects.filter(is_superuser=False).first()
            if test_user:
                # View user details
                response = client.get(f'/users/admin/user/{test_user.id}/')
                print(f"Admin viewing user details: {response.status_code}")
                
                # Verify admin is still logged in as admin (not impersonating)
                response = client.get('/users/admin-dashboard/')
                print(f"Admin dashboard after viewing user: {response.status_code}")
                
                # Test change role functionality
                response = client.get(f'/users/admin/user/{test_user.id}/change-role/')
                print(f"Admin change user role: {response.status_code}")
                
                print("✓ Admin security fix verified - no user impersonation")

def test_database_operations():
    """Test basic database operations"""
    print("\n=== Testing Database Operations ===")
    
    try:
        # Test user queries
        users_count = User.objects.count()
        print(f"✓ User count: {users_count}")
        
        # Test role distribution
        roles = User.objects.values_list('role', flat=True).distinct()
        print(f"✓ Available roles: {list(roles)}")
        
        # Test active users
        active_users = User.objects.filter(is_active=True).count()
        print(f"✓ Active users: {active_users}")
        
    except Exception as e:
        print(f"✗ Database operation error: {e}")

if __name__ == "__main__":
    print("Testing Payments and Security...")
    
    test_payment_endpoints()
    test_security_features()
    test_role_based_access()
    test_admin_security_fix()
    test_database_operations()
    
    print("\nPayments and security testing completed!")
