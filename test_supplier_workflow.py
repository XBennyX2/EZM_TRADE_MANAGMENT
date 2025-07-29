#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from users.supplier_views import supplier_mark_in_transit
from Inventory.models import *
import json

User = get_user_model()

def test_supplier_shipping_workflow():
    print("=== Testing Supplier Shipping Workflow ===")
    
    try:
        # Get a supplier user
        supplier_user = User.objects.filter(role='supplier').first()
        if not supplier_user:
            print("❌ No supplier users found")
            return
            
        print(f"✅ Found supplier user: {supplier_user.email}")
        
        # Get a supplier
        supplier = Supplier.objects.filter(email=supplier_user.email).first()
        if not supplier:
            print("❌ No supplier found for this user")
            return
            
        print(f"✅ Found supplier: {supplier.name}")
        
        # Find or create a payment_confirmed order for testing
        order = PurchaseOrder.objects.filter(supplier=supplier, status='payment_confirmed').first()
        if not order:
            # Try to find any order and set it to payment_confirmed for testing
            order = PurchaseOrder.objects.filter(supplier=supplier).first()
            if order:
                order.status = 'payment_confirmed'
                order.save()
                print(f"✅ Set order {order.order_number} to payment_confirmed for testing")
            else:
                print("❌ No orders found for this supplier")
                return
        else:
            print(f"✅ Found payment_confirmed order: {order.order_number}")
        
        # Create a mock request to test the supplier_mark_in_transit view
        factory = RequestFactory()
        
        # Create POST data for shipping
        post_data = {
            'tracking_number': 'TRACK123456',
            'shipping_notes': 'Package shipped via express delivery',
            'shipping_carrier': 'DHL Express'
        }
        
        # Create the request
        request = factory.post(f'/supplier/orders/{order.id}/mark-in-transit/', post_data)
        request.user = supplier_user
        
        print("🚚 Testing supplier mark in transit functionality...")
        
        # Call the view function
        response = supplier_mark_in_transit(request, order.id)
        
        # Check the response
        if response.status_code == 200:
            response_data = json.loads(response.content)
            if response_data.get('success'):
                print("✅ Order marked as shipped successfully!")
                print(f"📦 Order Number: {response_data.get('order_number')}")
                print(f"📍 Tracking Number: {response_data.get('tracking_number')}")
                print(f"🚛 Shipping Carrier: {response_data.get('shipping_carrier')}")
                print(f"📊 New Status: {response_data.get('new_status')}")
                
                # Verify the order was updated in the database
                order.refresh_from_db()
                print(f"✅ Database updated - Order status: {order.status}")
                print(f"✅ Shipped at: {order.shipped_at}")
                print(f"✅ Tracking number: {order.tracking_number}")
                
            else:
                print(f"❌ Failed to mark order as shipped: {response_data.get('message')}")
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.content}")
            
    except Exception as e:
        print(f"💥 Error during workflow test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supplier_shipping_workflow()