#!/usr/bin/env python
"""
Test script to debug the delivery confirmation API
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import PurchaseOrder
import json

User = get_user_model()

def test_delivery_confirmation_api():
    print("=== Testing Delivery Confirmation API ===")
    
    try:
        # Get head manager user
        head_manager = User.objects.filter(role='head_manager').first()
        if not head_manager:
            print("❌ No head manager user found")
            return
        
        print(f"✅ Found head manager: {head_manager.email}")
        
        # Get an order
        order = PurchaseOrder.objects.first()
        if not order:
            print("❌ No purchase orders found")
            return
        
        print(f"✅ Found order: {order.order_number} (ID: {order.id})")
        
        # Test the API endpoint
        client = Client()
        client.force_login(head_manager)
        
        url = f'/inventory/purchase-orders/{order.id}/details/'
        print(f"Testing API endpoint: {url}")
        
        response = client.get(url)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.items())}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ API returned JSON data:")
                print(f"  - ID: {data.get('id')}")
                print(f"  - Order Number: {data.get('order_number')}")
                print(f"  - Supplier: {data.get('supplier', {}).get('name')}")
                print(f"  - Total Amount: {data.get('total_amount')}")
                print(f"  - Status: {data.get('status')}")
                print(f"  - Items count: {len(data.get('items', []))}")
                
                if not data.get('id'):
                    print("❌ API response missing 'id' field!")
                else:
                    print("✅ API response contains 'id' field")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Response content: {response.content.decode()}")
        else:
            print(f"❌ API returned error status: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_order_data_structure():
    print("\n=== Testing Order Data Structure ===")
    
    try:
        order = PurchaseOrder.objects.first()
        if not order:
            print("❌ No purchase orders found")
            return
        
        print(f"Order ID: {order.id}")
        print(f"Order Number: {order.order_number}")
        print(f"Supplier: {order.supplier}")
        print(f"Supplier Name: {order.supplier.name if order.supplier else 'None'}")
        print(f"Total Amount: {order.total_amount}")
        print(f"Status: {order.status}")
        print(f"Items count: {order.items.count()}")
        
    except Exception as e:
        print(f"❌ Error checking order structure: {str(e)}")

if __name__ == '__main__':
    test_order_data_structure()
    test_delivery_confirmation_api()
    print("\n" + "=" * 50)
    print("🎉 Debug Complete!")
