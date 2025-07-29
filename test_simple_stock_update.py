#!/usr/bin/env python3
"""
Simple test to verify warehouse stock updates on delivery confirmation.
This test directly calls the confirm_delivery function to test the core logic.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import (
    Warehouse, WarehouseProduct, Supplier, PurchaseOrder, 
    PurchaseOrderItem, InventoryMovement
)
from Inventory.order_tracking_views import confirm_delivery

User = get_user_model()

def test_stock_update_logic():
    """Test the core stock update logic in delivery confirmation"""
    print("🧪 Testing warehouse stock update logic...")
    
    try:
        # Create test data
        print("📦 Setting up test data...")
        
        # Get or create head manager
        head_manager, created = User.objects.get_or_create(
            username='test_head_manager_simple',
            defaults={
                'email': 'head_simple@test.com',
                'role': 'head_manager',
                'first_name': 'Test',
                'last_name': 'Manager'
            }
        )
        if created:
            head_manager.set_password('testpass123')
            head_manager.save()
        
        # Create warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Test Warehouse Simple',
            defaults={
                'address': 'Test Location Simple',
                'manager_name': head_manager.get_full_name(),
                'capacity': 1000,
                'current_utilization': 0
            }
        )
        
        # Create supplier
        supplier, created = Supplier.objects.get_or_create(
            name='Test Supplier Simple',
            defaults={
                'email': 'supplier_simple@test.com',
                'phone': '1234567890',
                'address': 'Test Address Simple'
            }
        )
        
        # Create warehouse product with initial stock
        product, created = WarehouseProduct.objects.get_or_create(
            product_id='TSP001',
            defaults={
                'product_name': 'Test Simple Product',
                'sku': 'TSP001-SKU',
                'quantity_in_stock': 100,
                'unit_price': Decimal('25.00'),
                'category': 'construction',
                'supplier': supplier,
                'warehouse': warehouse
            }
        )
        
        # Record initial stock
        initial_stock = product.quantity_in_stock
        print(f"📊 Initial stock: {initial_stock}")
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            order_number='TEST-SIMPLE-PO-001',
            supplier=supplier,
            created_by=head_manager,
            order_date=timezone.now().date(),
            status='in_transit',
            total_amount=Decimal('750.00'),
            delivery_address='Test Delivery Address Simple'
        )
        
        # Create purchase order item
        order_quantity = 30
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product,
            quantity_ordered=order_quantity,
            unit_price=Decimal('25.00')
        )
        
        print(f"📦 Order quantity: {order_quantity}")
        
        # Create a mock request for the confirm_delivery function
        factory = RequestFactory()
        request = factory.post(
            f'/inventory/purchase-orders/{purchase_order.id}/confirm-delivery/',
            {
                'delivery_condition': 'good',
                'all_items_received': 'true',
                'delivery_notes': 'All items received in good condition',
                'received_items': f'["{item.id}"]'
            }
        )
        request.user = head_manager
        
        # Call the confirm_delivery function directly
        print("🚚 Confirming delivery...")
        response = confirm_delivery(request, purchase_order.id)
        
        # Check if the response indicates success
        if hasattr(response, 'status_code') and response.status_code != 200:
            print(f"❌ Delivery confirmation failed with status {response.status_code}")
            return False
        
        # Refresh objects from database
        product.refresh_from_db()
        item.refresh_from_db()
        purchase_order.refresh_from_db()
        
        # Calculate expected stock
        expected_stock = initial_stock + order_quantity
        
        print(f"📊 Final stock: {product.quantity_in_stock} (expected: {expected_stock})")
        
        # Verify stock was updated correctly
        if product.quantity_in_stock != expected_stock:
            print(f"❌ Stock update failed: got {product.quantity_in_stock}, expected {expected_stock}")
            return False
        
        # Verify item is marked as received
        if not item.is_confirmed_received:
            print("❌ Item not marked as received")
            return False
        
        if item.quantity_received != order_quantity:
            print(f"❌ Item quantity_received incorrect: got {item.quantity_received}, expected {order_quantity}")
            return False
        
        # Verify inventory movement was created
        movements = InventoryMovement.objects.filter(
            warehouse_product=product,
            movement_type='purchase_delivery',
            purchase_order=purchase_order
        )
        
        if not movements.exists():
            print("❌ No inventory movement created")
            return False
        
        movement = movements.first()
        if movement.quantity_change != order_quantity:
            print(f"❌ Movement quantity incorrect: got {movement.quantity_change}, expected {order_quantity}")
            return False
        
        # Verify order status
        if purchase_order.status != 'delivered':
            print(f"❌ Order status incorrect: got {purchase_order.status}, expected 'delivered'")
            return False
        
        print("✅ Stock update logic test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_partial_delivery_logic():
    """Test partial delivery where only some items are received"""
    print("\n🧪 Testing partial delivery logic...")
    
    try:
        # Get existing test data
        head_manager = User.objects.get(username='test_head_manager_simple')
        supplier = Supplier.objects.get(name='Test Supplier Simple')
        warehouse = Warehouse.objects.get(name='Test Warehouse Simple')
        
        # Create another product for partial delivery test
        product2, created = WarehouseProduct.objects.get_or_create(
            product_id='TSP002',
            defaults={
                'product_name': 'Test Partial Product',
                'sku': 'TSP002-SKU',
                'quantity_in_stock': 50,
                'unit_price': Decimal('15.00'),
                'category': 'construction',
                'supplier': supplier,
                'warehouse': warehouse
            }
        )
        
        initial_stock = product2.quantity_in_stock
        print(f"📊 Initial stock: {initial_stock}")
        
        # Create purchase order for partial delivery
        purchase_order2 = PurchaseOrder.objects.create(
            order_number='TEST-PARTIAL-PO-002',
            supplier=supplier,
            created_by=head_manager,
            order_date=timezone.now().date(),
            status='in_transit',
            total_amount=Decimal('300.00'),
            delivery_address='Test Delivery Address Partial'
        )
        
        # Create purchase order item
        order_quantity = 20
        item2 = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order2,
            warehouse_product=product2,
            quantity_ordered=order_quantity,
            unit_price=Decimal('15.00')
        )
        
        # Create mock request for partial delivery (no items received)
        factory = RequestFactory()
        request = factory.post(
            f'/inventory/purchase-orders/{purchase_order2.id}/confirm-delivery/',
            {
                'delivery_condition': 'damaged',
                'all_items_received': 'false',
                'delivery_notes': 'Items were damaged during delivery',
                'received_items': '[]'  # No items received
            }
        )
        request.user = head_manager
        
        # Call the confirm_delivery function
        print("🚚 Confirming partial delivery (no items received)...")
        response = confirm_delivery(request, purchase_order2.id)
        
        # Refresh objects
        product2.refresh_from_db()
        item2.refresh_from_db()
        
        # Verify stock was NOT updated (no items received)
        if product2.quantity_in_stock != initial_stock:
            print(f"❌ Stock should not have changed: got {product2.quantity_in_stock}, expected {initial_stock}")
            return False
        
        # Verify item is marked as having issues
        if not item2.has_issues:
            print("❌ Item should be marked as having issues")
            return False
        
        # Verify no inventory movement was created for this item
        movements = InventoryMovement.objects.filter(
            warehouse_product=product2,
            movement_type='purchase_delivery',
            purchase_order=purchase_order2
        )
        
        if movements.exists():
            print("❌ No inventory movement should have been created for undelivered items")
            return False
        
        print("✅ Partial delivery logic test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Partial delivery test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting simple warehouse stock update tests...\n")
    
    success1 = test_stock_update_logic()
    success2 = test_partial_delivery_logic()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Warehouse stock updates are working correctly.")
        print("\n📋 Summary:")
        print("✅ Stock is updated accurately when items are delivered")
        print("✅ Stock is NOT updated when items are not received")
        print("✅ Inventory movements are tracked correctly")
        print("✅ Order and item statuses are updated properly")
        print("✅ Partial deliveries are handled correctly")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)
