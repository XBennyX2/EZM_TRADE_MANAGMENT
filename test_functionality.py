#!/usr/bin/env python
"""
Comprehensive functionality testing script for EZM Trade Management System
"""

import os
import sys
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_authentication():
    """Test user authentication and session management"""
    print("=== Testing Authentication ===")
    
    client = Client()
    
    # Test login page access
    response = client.get('/users/login/')
    print(f"Login page access: {response.status_code}")
    
    # Test login with Head Manager credentials
    try:
        head_manager = User.objects.get(username='head_manager_test')
        login_data = {
            'username': 'head_manager_test',
            'password': 'testpass123'
        }
        response = client.post('/users/login/', login_data)
        print(f"Head Manager login: {response.status_code} -> {response.url if hasattr(response, 'url') else 'No redirect'}")
        
        # Test Head Manager dashboard access
        response = client.get('/users/head-manager/')
        print(f"Head Manager dashboard: {response.status_code}")
        
        return client
    except User.DoesNotExist:
        print("Head Manager test user not found")
        return None

def test_head_manager_forms(client):
    """Test Head Manager form submissions and validation"""
    print("\n=== Testing Head Manager Forms ===")
    
    if not client:
        print("No authenticated client available")
        return
    
    # Test supplier list access
    response = client.get('/inventory/suppliers/')
    print(f"Supplier list: {response.status_code}")
    
    # Test warehouse list access
    response = client.get('/inventory/warehouses/')
    print(f"Warehouse list: {response.status_code}")
    
    # Test purchase order list access
    response = client.get('/inventory/purchase-orders/')
    print(f"Purchase order list: {response.status_code}")
    
    # Test cart access
    response = client.get('/cart/')
    print(f"Shopping cart: {response.status_code}")

def test_head_manager_dashboard(client):
    """Test Head Manager dashboard functionality"""
    print("\n=== Testing Head Manager Dashboard ===")
    
    if not client:
        print("No authenticated client available")
        return
    
    # Test main dashboard
    response = client.get('/users/head-manager/')
    print(f"Main dashboard: {response.status_code}")
    
    # Test restock requests management
    response = client.get('/users/head-manager/restock-requests/')
    print(f"Restock requests: {response.status_code}")
    
    # Test analytics dashboard
    response = client.get('/users/head-manager/analytics/')
    print(f"Analytics dashboard: {response.status_code}")

def test_api_endpoints(client):
    """Test API endpoints and AJAX functionality"""
    print("\n=== Testing API Endpoints ===")
    
    if not client:
        print("No authenticated client available")
        return
    
    # Test cart count API
    response = client.get('/cart/count/')
    print(f"Cart count API: {response.status_code}")
    
    # Test analytics API
    response = client.get('/users/api/analytics/')
    print(f"Analytics API: {response.status_code}")

def test_security_fixes():
    """Test the recently fixed admin user management security issue"""
    print("\n=== Testing Security Fixes ===")
    
    client = Client()
    
    # Test admin login
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            login_data = {
                'username': admin_user.username,
                'password': 'admin123'  # Default admin password
            }
            response = client.post('/users/login/', login_data)
            print(f"Admin login: {response.status_code}")
            
            # Test user detail view (the fixed security issue)
            test_user = User.objects.filter(is_superuser=False).first()
            if test_user:
                response = client.get(f'/users/admin/user/{test_user.id}/')
                print(f"User detail view: {response.status_code}")
                
                # Verify admin is still logged in as admin
                response = client.get('/users/admin-dashboard/')
                print(f"Admin dashboard after viewing user: {response.status_code}")
    except Exception as e:
        print(f"Security test error: {e}")

if __name__ == "__main__":
    print("Starting EZM Trade Management System Testing...")
    
    # Test authentication
    client = test_authentication()
    
    # Test Head Manager functionality
    test_head_manager_forms(client)
    test_head_manager_dashboard(client)
    test_api_endpoints(client)
    
    # Test security fixes
    test_security_fixes()
    
    print("\nTesting completed!")
