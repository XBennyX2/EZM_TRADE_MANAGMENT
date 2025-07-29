#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import PurchaseOrder

def test_api():
    print("Testing delivery confirmation API...")
    
    # Get head manager
    User = get_user_model()
    head_manager = User.objects.filter(role='head_manager').first()
    
    if not head_manager:
        print("No head manager found")
        return
    
    print(f"Head manager: {head_manager.email}")
    
    # Get an order
    order = PurchaseOrder.objects.first()
    if not order:
        print("No orders found")
        return
    
    print(f"Testing with order: {order.id} - {order.order_number}")
    
    # Test API
    client = Client()
    client.force_login(head_manager)
    
    response = client.get(f'/inventory/purchase-orders/{order.id}/details/')
    
    print(f"Status: {response.status_code}")
    print(f"Content: {response.content.decode()}")
    
    if response.status_code == 200:
        import json
        try:
            data = json.loads(response.content)
            print(f"JSON keys: {list(data.keys())}")
            print(f"Has ID: {'id' in data}")
            if 'id' in data:
                print(f"ID value: {data['id']}")
        except:
            print("Not valid JSON")

if __name__ == '__main__':
    test_api()
