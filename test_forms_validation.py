#!/usr/bin/env python
"""
Test form validation and submission workflows
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def get_authenticated_client():
    """Get authenticated Head Manager client"""
    client = Client()
    login_data = {
        'username': 'HeadManager',
        'password': 'password123'
    }
    response = client.post('/users/login/', login_data)
    if response.status_code == 302:
        return client
    return None

def test_supplier_forms(client):
    """Test supplier management forms"""
    print("=== Testing Supplier Forms ===")
    
    # Test supplier creation form access
    response = client.get('/inventory/suppliers/new/')
    print(f"Supplier creation form: {response.status_code}")
    
    # Test supplier list with search/filter
    response = client.get('/inventory/suppliers/')
    print(f"Supplier list: {response.status_code}")

def test_warehouse_forms(client):
    """Test warehouse management forms"""
    print("\n=== Testing Warehouse Forms ===")
    
    # Test warehouse creation form
    response = client.get('/inventory/warehouses/new/')
    print(f"Warehouse creation form: {response.status_code}")
    
    # Test warehouse list
    response = client.get('/inventory/warehouses/')
    print(f"Warehouse list: {response.status_code}")

def test_purchase_order_forms(client):
    """Test purchase order forms"""
    print("\n=== Testing Purchase Order Forms ===")
    
    # Test purchase order creation
    response = client.get('/inventory/purchase-orders/new/')
    print(f"Purchase order creation form: {response.status_code}")
    
    # Test purchase order list
    response = client.get('/inventory/purchase-orders/')
    print(f"Purchase order list: {response.status_code}")

def test_cart_functionality(client):
    """Test shopping cart functionality"""
    print("\n=== Testing Cart Functionality ===")
    
    # Test cart view
    response = client.get('/cart/')
    print(f"Cart view: {response.status_code}")
    
    # Test cart count
    response = client.get('/cart/count/')
    print(f"Cart count: {response.status_code}")
    
    # Test cart clear
    response = client.post('/cart/clear/')
    print(f"Cart clear: {response.status_code}")

def test_restock_management(client):
    """Test restock request management"""
    print("\n=== Testing Restock Management ===")
    
    # Test restock requests list
    response = client.get('/users/head-manager/restock-requests/')
    print(f"Restock requests list: {response.status_code}")

def test_analytics_functionality(client):
    """Test analytics and reporting"""
    print("\n=== Testing Analytics ===")
    
    # Test analytics dashboard
    response = client.get('/users/head-manager/analytics/')
    print(f"Analytics dashboard: {response.status_code}")
    
    # Test analytics API
    response = client.get('/users/api/analytics/')
    print(f"Analytics API: {response.status_code}")

def test_error_handling(client):
    """Test error handling and validation"""
    print("\n=== Testing Error Handling ===")
    
    # Test accessing non-existent resources
    response = client.get('/inventory/suppliers/99999/')
    print(f"Non-existent supplier: {response.status_code}")
    
    response = client.get('/inventory/warehouses/99999/')
    print(f"Non-existent warehouse: {response.status_code}")
    
    response = client.get('/inventory/purchase-orders/99999/')
    print(f"Non-existent purchase order: {response.status_code}")

if __name__ == "__main__":
    print("Testing Forms and Validation...")
    
    client = get_authenticated_client()
    if not client:
        print("Failed to authenticate")
        exit(1)
    
    test_supplier_forms(client)
    test_warehouse_forms(client)
    test_purchase_order_forms(client)
    test_cart_functionality(client)
    test_restock_management(client)
    test_analytics_functionality(client)
    test_error_handling(client)
    
    print("\nForms and validation testing completed!")
