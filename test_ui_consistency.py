#!/usr/bin/env python
"""
Test UI consistency and responsive design
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
    """Test specific payment endpoints"""
    print("=== Testing Payment Endpoints ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test specific payment endpoints
    payment_endpoints = [
        ('/payments/history/', 'Payment History'),
        ('/payments/methods/', 'Payment Methods'),
        ('/payments/selection/', 'Payment Selection'),
    ]
    
    for url, name in payment_endpoints:
        try:
            response = client.get(url)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")

def test_ui_consistency():
    """Test UI consistency across different pages"""
    print("\n=== Testing UI Consistency ===")
    
    client = Client()
    
    # Test different role dashboards for UI consistency
    test_cases = [
        ('HeadManager', 'password123', '/users/head-manager/', 'Head Manager Dashboard'),
        ('store_manager1', 'password123', '/users/store-manager/', 'Store Manager Dashboard'),
    ]
    
    for username, password, url, name in test_cases:
        client_test = Client()
        login_data = {'username': username, 'password': password}
        response = client_test.post('/users/login/', login_data)
        
        if response.status_code == 302:
            response = client_test.get(url)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
            
            # Test if the page contains EZM styling elements
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                has_ezm_card = 'ezm-card' in content
                has_sidebar = 'base_sidebar.html' in content or 'sidebar' in content
                has_ezm_theme = 'ezm-theme.css' in content or 'ezm' in content
                
                print(f"  - EZM Card styling: {'✓' if has_ezm_card else '✗'}")
                print(f"  - Sidebar navigation: {'✓' if has_sidebar else '✗'}")
                print(f"  - EZM theme: {'✓' if has_ezm_theme else '✗'}")

def test_error_pages():
    """Test error page handling"""
    print("\n=== Testing Error Pages ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test 404 errors
    error_urls = [
        '/inventory/suppliers/99999/',
        '/inventory/warehouses/99999/',
        '/inventory/purchase-orders/99999/',
        '/users/admin/user/99999/',
    ]
    
    for url in error_urls:
        response = client.get(url)
        print(f"404 test {url}: {response.status_code}")

def test_form_validation():
    """Test form validation and error handling"""
    print("\n=== Testing Form Validation ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test empty form submissions
    form_tests = [
        ('/cart/add/', {'product_id': '', 'quantity': ''}, 'Cart Add Form'),
        ('/cart/update/', {'product_id': '', 'quantity': ''}, 'Cart Update Form'),
    ]
    
    for url, data, name in form_tests:
        try:
            response = client.post(url, data)
            print(f"{name}: {response.status_code}")
        except Exception as e:
            print(f"{name}: Error - {e}")

def test_api_endpoints():
    """Test API endpoints functionality"""
    print("\n=== Testing API Endpoints ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test API endpoints
    api_endpoints = [
        ('/cart/count/', 'Cart Count API'),
        ('/users/api/analytics/', 'Analytics API'),
        ('/users/api/restock-products/', 'Restock Products API'),
        ('/users/api/transfer-products/', 'Transfer Products API'),
    ]
    
    for url, name in api_endpoints:
        try:
            response = client.get(url)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")

def test_navigation_links():
    """Test navigation links and redirects"""
    print("\n=== Testing Navigation Links ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    client.post('/users/login/', login_data)
    
    # Test navigation between pages
    navigation_flow = [
        '/users/head-manager/',
        '/inventory/suppliers/',
        '/inventory/warehouses/',
        '/inventory/purchase-orders/',
        '/cart/',
        '/users/head-manager/restock-requests/',
        '/users/head-manager/analytics/',
    ]
    
    for url in navigation_flow:
        response = client.get(url)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {url}: {response.status_code}")

if __name__ == "__main__":
    print("Testing UI Consistency and Functionality...")
    
    test_payment_endpoints()
    test_ui_consistency()
    test_error_pages()
    test_form_validation()
    test_api_endpoints()
    test_navigation_links()
    
    print("\nUI consistency testing completed!")
