#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from Inventory.models import PurchaseOrder, Supplier, WarehouseProduct, PurchaseOrderItem, DeliveryConfirmation
from Inventory.order_tracking_views import confirm_delivery
import json

User = get_user_model()

def test_delivery_confirmation_with_no_items():
    """Test delivery confirmation for orders with no items"""
    print("=== Testing Delivery Confirmation Fix ===")
    
    try:
        # Get or create a head manager user
        head_manager = User.objects.filter(role='head_manager').first()
        if not head_manager:
            print("❌ No head manager found. Creating one...")
            head_manager = User.objects.create_user(
                username='test_head_manager',
                email='head@test.com',
                password='testpass123',
                role='head_manager'
            )
            print(f"✅ Created head manager: {head_manager.username}")
        else:
            print(f"✅ Found head manager: {head_manager.username}")
        
        # Get or create a supplier
        supplier = Supplier.objects.first()
        if not supplier:
            print("❌ No supplier found. Creating one...")
            supplier = Supplier.objects.create(
                name='Test Supplier',
                email='supplier@test.com',
                phone='123456789',
                is_active=True
            )
            print(f"✅ Created supplier: {supplier.name}")
        else:
            print(f"✅ Found supplier: {supplier.name}")
        
        # Create a purchase order without items
        print("🔨 Creating purchase order without items...")
        order = PurchaseOrder.objects.create(
            order_number='TEST-NO-ITEMS-001',
            supplier=supplier,
            created_by=head_manager,
            status='in_transit',
            total_amount=0
        )
        print(f"✅ Created order: {order.order_number} (status: {order.status})")
        
        # Verify order has no items
        items_count = order.items.count()
        print(f"📦 Order items count: {items_count}")
        
        if items_count > 0:
            print("❌ Order has items, deleting them for test...")
            order.items.all().delete()
            print("✅ Deleted all items from order")
        
        # Create a request factory and simulate the delivery confirmation request
        factory = RequestFactory()
        
        # Prepare POST data
        post_data = {
            'delivery_condition': 'good',
            'all_items_received': 'true',
            'delivery_notes': 'Test delivery confirmation for order with no items',
            'received_items': '[]'
        }
        
        # Create the request
        request = factory.post(f'/confirm-delivery/{order.id}/', post_data)
        request.user = head_manager
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test Agent'
        
        print("🧪 Testing delivery confirmation...")
        
        # Call the confirm_delivery function
        response = confirm_delivery(request, order.id)
        
        # Check the response
        if isinstance(response, JsonResponse):
            response_data = json.loads(response.content.decode())
            print(f"📋 Response: {response_data}")
            
            if response_data.get('success'):
                print("✅ Delivery confirmation succeeded!")
                
                # Verify order status was updated
                order.refresh_from_db()
                print(f"📊 Order status after confirmation: {order.status}")
                
                # Check if delivery confirmation was created
                try:
                    delivery_confirmation = DeliveryConfirmation.objects.get(purchase_order=order)
                    print(f"✅ Delivery confirmation created: {delivery_confirmation}")
                except DeliveryConfirmation.DoesNotExist:
                    print("⚠️  No delivery confirmation record found")
                
            else:
                print(f"❌ Delivery confirmation failed: {response_data.get('message')}")
        else:
            print(f"❌ Unexpected response type: {type(response)}")
        
        # Test case 2: Order with items
        print("\n=== Testing Order With Items ===")
        
        # Create a warehouse product
        warehouse_product = WarehouseProduct.objects.create(
            product_id='TEST-PROD-001',
            product_name='Test Product',
            category='Hardware',
            quantity_in_stock=100,
            unit_price=10.00,
            sku='TEST-SKU-001',
            supplier=supplier
        )
        print(f"✅ Created warehouse product: {warehouse_product.product_name}")
        
        # Create another order with items
        order_with_items = PurchaseOrder.objects.create(
            order_number='TEST-WITH-ITEMS-001',
            supplier=supplier,
            created_by=head_manager,
            status='in_transit',
            total_amount=50.00
        )
        
        # Add an item to the order
        order_item = PurchaseOrderItem.objects.create(
            purchase_order=order_with_items,
            warehouse_product=warehouse_product,
            quantity_ordered=5,
            unit_price=10.00,
            total_price=50.00
        )
        print(f"✅ Created order with items: {order_with_items.order_number}")
        
        # Test delivery confirmation for order with items
        post_data_with_items = {
            'delivery_condition': 'excellent',
            'all_items_received': 'true',
            'delivery_notes': 'Test delivery confirmation for order with items',
            'received_items': f'["{order_item.id}"]'
        }
        
        request_with_items = factory.post(f'/confirm-delivery/{order_with_items.id}/', post_data_with_items)
        request_with_items.user = head_manager
        request_with_items.META['REMOTE_ADDR'] = '127.0.0.1'
        request_with_items.META['HTTP_USER_AGENT'] = 'Test Agent'
        
        print("🧪 Testing delivery confirmation for order with items...")
        response_with_items = confirm_delivery(request_with_items, order_with_items.id)
        
        if isinstance(response_with_items, JsonResponse):
            response_data_with_items = json.loads(response_with_items.content.decode())
            print(f"📋 Response: {response_data_with_items}")
            
            if response_data_with_items.get('success'):
                print("✅ Delivery confirmation with items succeeded!")
                
                # Verify order status
                order_with_items.refresh_from_db()
                print(f"📊 Order status after confirmation: {order_with_items.status}")
                
                # Check item status
                order_item.refresh_from_db()
                print(f"📦 Item confirmed received: {order_item.is_confirmed_received}")
                print(f"📦 Item quantity received: {order_item.quantity_received}")
                
            else:
                print(f"❌ Delivery confirmation with items failed: {response_data_with_items.get('message')}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"💥 Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delivery_confirmation_with_no_items()