#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.supplier_views import *
from Inventory.models import *
from django.contrib.auth import get_user_model
from payments.notification_service import supplier_notification_service

User = get_user_model()

def test_shipping_notification():
    print("=== Testing Shipping Notification ===")
    
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
        
        # Get any purchase order for testing
        order = PurchaseOrder.objects.filter(supplier=supplier).first()
        if not order:
            print("❌ No orders found for this supplier")
            return
            
        print(f"✅ Found order: {order.order_number} (status: {order.status})")
        
        # Test the notification service directly
        print("🧪 Testing notification service...")
        
        result = supplier_notification_service.send_order_shipped_notification(
            order=order,
            tracking_number='TEST123',
            shipping_carrier='Test Carrier',
            shipping_notes='Test shipping notes',
            shipped_by=supplier_user
        )
        
        print(f"📧 Notification result: {result}")
        
        if result:
            print("✅ Notification sent successfully!")
        else:
            print("❌ Notification failed!")
            
    except Exception as e:
        print(f"💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shipping_notification()