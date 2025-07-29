#!/usr/bin/env python
"""
Debug script to test the mark as shipped functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.supplier_views import supplier_mark_in_transit
from Inventory.models import *
import json

User = get_user_model()

def test_mark_shipped_functionality():
    print("=== Testing Mark as Shipped Functionality ===")
    
    try:
        # Get supplier user
        supplier_user = User.objects.filter(email="Aueed@gmail.com").first()
        if not supplier_user:
            print("❌ No supplier user found with email Aueed@gmail.com")
            return
        
        print(f"✅ Found supplier user: {supplier_user.email}")
        
        # Get supplier
        supplier = Supplier.objects.filter(email=supplier_user.email).first()
        if not supplier:
            print("❌ No supplier found")
            return
        
        print(f"✅ Found supplier: {supplier.name}")
        
        # Get any order and set it to payment_confirmed for testing
        order = PurchaseOrder.objects.filter(supplier=supplier).first()

        if not order:
            print("❌ No orders found for this supplier")
            return

        # Set order to payment_confirmed for testing
        if order.status != 'payment_confirmed':
            print(f"Setting order {order.order_number} status from {order.status} to payment_confirmed")
            order.status = 'payment_confirmed'
            order.save()
        
        print(f"✅ Found payment_confirmed order: {order.order_number}")
        
        # Test using Django test client
        client = Client()
        
        # Login the user
        client.force_login(supplier_user)
        
        # Prepare POST data
        post_data = {
            'tracking_number': 'TEST123456',
            'shipping_notes': 'Test shipping notes',
            'shipping_carrier': 'Test Carrier'
        }
        
        print("🚚 Testing mark in transit via Django client...")
        
        # Make the request
        url = f'/users/supplier/orders/{order.id}/mark-in-transit/'
        print(f"Request URL: {url}")
        print(f"POST data: {post_data}")
        
        response = client.post(url, post_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.items())}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Response JSON: {response_data}")
                
                if response_data.get('success'):
                    print("✅ Request successful!")
                else:
                    print(f"❌ Request failed: {response_data.get('message')}")
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                print(f"Response content: {response.content.decode()}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
        # Check if order status changed
        order.refresh_from_db()
        print(f"Order status after request: {order.status}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_url_resolution():
    print("\n=== Testing URL Resolution ===")
    
    try:
        # Test URL resolution
        from django.urls import resolve
        
        url = '/users/supplier/orders/1/mark-in-transit/'
        print(f"Testing URL: {url}")
        
        resolved = resolve(url)
        print(f"✅ URL resolves to: {resolved.func.__name__}")
        print(f"URL name: {resolved.url_name}")
        print(f"Args: {resolved.args}")
        print(f"Kwargs: {resolved.kwargs}")
        
    except Exception as e:
        print(f"❌ URL resolution failed: {str(e)}")

def test_csrf_token():
    print("\n=== Testing CSRF Token ===")
    
    try:
        client = Client()
        
        # Get supplier user
        supplier_user = User.objects.filter(email="Aueed@gmail.com").first()
        if supplier_user:
            client.force_login(supplier_user)
            
            # Get the supplier purchase orders page
            response = client.get('/users/supplier/purchase-orders/')
            print(f"Purchase orders page status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content.decode()
                if 'csrfmiddlewaretoken' in content:
                    print("✅ CSRF token found in page")
                else:
                    print("❌ CSRF token not found in page")
            else:
                print(f"❌ Could not load purchase orders page: {response.status_code}")
        
    except Exception as e:
        print(f"❌ CSRF test failed: {str(e)}")

if __name__ == '__main__':
    test_url_resolution()
    test_csrf_token()
    test_mark_shipped_functionality()
    print("\n" + "=" * 50)
    print("🎉 Debug Complete!")
