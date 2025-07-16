#!/usr/bin/env python
"""
Targeted Head Manager functionality testing
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_head_manager_login():
    """Test Head Manager login and dashboard access"""
    print("=== Testing Head Manager Login ===")
    
    client = Client()
    
    # Get Head Manager user
    try:
        head_manager = User.objects.get(username='HeadManager')
        print(f"Found Head Manager: {head_manager.username}, Role: {head_manager.role}")
        
        # Test login
        login_data = {
            'username': 'HeadManager',
            'password': 'password123'
        }
        
        response = client.post('/users/login/', login_data, follow=True)
        print(f"Login response: {response.status_code}")
        print(f"Final URL: {response.request['PATH_INFO']}")
        
        # Check if we're logged in by accessing the dashboard
        response = client.get('/users/head-manager/')
        print(f"Head Manager dashboard: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Head Manager login successful")
            return client
        else:
            print("✗ Head Manager login failed")
            return None
            
    except User.DoesNotExist:
        print("Head Manager user not found")
        return None

def test_head_manager_navigation(client):
    """Test Head Manager navigation and page access"""
    print("\n=== Testing Head Manager Navigation ===")
    
    if not client:
        print("No authenticated client")
        return
    
    # Test various Head Manager pages
    pages = [
        ('/users/head-manager/', 'Main Dashboard'),
        ('/users/head-manager/restock-requests/', 'Restock Requests'),
        ('/users/head-manager/analytics/', 'Analytics Dashboard'),
        ('/inventory/suppliers/', 'Supplier Management'),
        ('/inventory/warehouses/', 'Warehouse Management'),
        ('/inventory/purchase-orders/', 'Purchase Orders'),
        ('/cart/', 'Shopping Cart'),
    ]
    
    for url, name in pages:
        response = client.get(url)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name}: {response.status_code}")

def test_form_submissions(client):
    """Test Head Manager form submissions"""
    print("\n=== Testing Form Submissions ===")
    
    if not client:
        print("No authenticated client")
        return
    
    # Test cart functionality
    response = client.get('/cart/count/')
    print(f"Cart count API: {response.status_code}")
    
    # Test adding item to cart (if products exist)
    try:
        from Inventory.models import Product
        product = Product.objects.first()
        if product:
            cart_data = {
                'product_id': product.id,
                'quantity': 1
            }
            response = client.post('/cart/add/', cart_data)
            print(f"Add to cart: {response.status_code}")
    except Exception as e:
        print(f"Cart test error: {e}")

if __name__ == "__main__":
    print("Testing Head Manager Functionality...")
    
    # Test login
    client = test_head_manager_login()
    
    # Test navigation
    test_head_manager_navigation(client)
    
    # Test forms
    test_form_submissions(client)
    
    print("\nHead Manager testing completed!")
