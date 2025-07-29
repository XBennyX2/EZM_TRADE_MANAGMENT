#!/usr/bin/env python3
"""
Test script to verify warehouse stock updates on delivery confirmation.
This test ensures that warehouse stock is updated accurately and efficiently.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from Inventory.models import (
    Warehouse, WarehouseProduct, Supplier, PurchaseOrder, 
    PurchaseOrderItem, InventoryMovement
)

User = get_user_model()

def test_delivery_confirmation_stock_update():
    """Test that warehouse stock is updated correctly on delivery confirmation"""
    print("🧪 Testing delivery confirmation stock updates...")
    
    try:
        # Create test data
        print("📦 Setting up test data...")
        
        # Create head manager
        head_manager, created = User.objects.get_or_create(
            username='test_head_manager',
            defaults={
                'email': 'head@test.com',
                'password': 'testpass123',
                'role': 'head_manager',
                'first_name': 'Test',
                'last_name': 'Manager'
            }
        )
        if created:
            head_manager.set_password('testpass123')
            head_manager.save()
        
        # Create warehouse
        warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            address='Test Location',
            manager_name=head_manager.get_full_name(),
            capacity=1000,
            current_utilization=0
        )
        
        # Create supplier first
        supplier, created = Supplier.objects.get_or_create(
            name='Test Supplier',
            defaults={
                'email': 'supplier@test.com',
                'phone': '1234567890',
                'address': 'Test Address'
            }
        )

        # Create warehouse products with initial stock
        product1 = WarehouseProduct.objects.create(
            product_id='TP001',
            product_name='Test Product 1',
            sku='TP001-SKU',
            quantity_in_stock=50,
            unit_price=Decimal('10.00'),
            category='construction',
            supplier=supplier,
            warehouse=warehouse
        )

        product2 = WarehouseProduct.objects.create(
            product_id='TP002',
            product_name='Test Product 2',
            sku='TP002-SKU',
            quantity_in_stock=30,
            unit_price=Decimal('15.00'),
            category='construction',
            supplier=supplier,
            warehouse=warehouse
        )
        

        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            order_number='TEST-PO-001',
            supplier=supplier,
            created_by=head_manager,
            order_date=timezone.now().date(),
            status='in_transit',
            total_amount=Decimal('500.00'),
            delivery_address='Test Delivery Address'
        )
        
        # Create purchase order items
        item1 = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product1,
            quantity_ordered=20,
            unit_price=Decimal('10.00')
        )
        
        item2 = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product2,
            quantity_ordered=15,
            unit_price=Decimal('15.00')
        )
        
        # Record initial stock levels
        initial_stock_1 = product1.quantity_in_stock
        initial_stock_2 = product2.quantity_in_stock
        
        print(f"📊 Initial stock levels:")
        print(f"   Product 1: {initial_stock_1}")
        print(f"   Product 2: {initial_stock_2}")
        
        # Test delivery confirmation via API
        client = Client()
        client.force_login(head_manager)
        
        print("🚚 Confirming delivery...")
        
        response = client.post(
            f'/inventory/purchase-orders/{purchase_order.id}/confirm-delivery/',
            {
                'delivery_condition': 'good',
                'all_items_received': 'true',
                'delivery_notes': 'All items received in good condition',
                'received_items': f'["{item1.id}", "{item2.id}"]'
            }
        )
        
        if response.status_code != 200:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.content}")
            return False
        
        # Refresh objects from database
        product1.refresh_from_db()
        product2.refresh_from_db()
        item1.refresh_from_db()
        item2.refresh_from_db()
        purchase_order.refresh_from_db()
        
        # Verify stock updates
        expected_stock_1 = initial_stock_1 + item1.quantity_ordered
        expected_stock_2 = initial_stock_2 + item2.quantity_ordered
        
        print(f"📊 Final stock levels:")
        print(f"   Product 1: {product1.quantity_in_stock} (expected: {expected_stock_1})")
        print(f"   Product 2: {product2.quantity_in_stock} (expected: {expected_stock_2})")
        
        # Verify stock levels
        if product1.quantity_in_stock != expected_stock_1:
            print(f"❌ Product 1 stock incorrect: got {product1.quantity_in_stock}, expected {expected_stock_1}")
            return False
            
        if product2.quantity_in_stock != expected_stock_2:
            print(f"❌ Product 2 stock incorrect: got {product2.quantity_in_stock}, expected {expected_stock_2}")
            return False
        
        # Verify items are marked as received
        if not item1.is_confirmed_received:
            print("❌ Item 1 not marked as received")
            return False
            
        if not item2.is_confirmed_received:
            print("❌ Item 2 not marked as received")
            return False
        
        # Verify inventory movements were created
        movements_1 = InventoryMovement.objects.filter(
            warehouse_product=product1,
            movement_type='purchase_delivery',
            purchase_order=purchase_order
        )
        
        movements_2 = InventoryMovement.objects.filter(
            warehouse_product=product2,
            movement_type='purchase_delivery',
            purchase_order=purchase_order
        )
        
        if not movements_1.exists():
            print("❌ No inventory movement created for product 1")
            return False
            
        if not movements_2.exists():
            print("❌ No inventory movement created for product 2")
            return False
        
        # Verify movement quantities
        movement_1 = movements_1.first()
        movement_2 = movements_2.first()
        
        if movement_1.quantity_change != item1.quantity_ordered:
            print(f"❌ Movement 1 quantity incorrect: got {movement_1.quantity_change}, expected {item1.quantity_ordered}")
            return False
            
        if movement_2.quantity_change != item2.quantity_ordered:
            print(f"❌ Movement 2 quantity incorrect: got {movement_2.quantity_change}, expected {item2.quantity_ordered}")
            return False
        
        # Verify order status
        if purchase_order.status != 'delivered':
            print(f"❌ Order status incorrect: got {purchase_order.status}, expected 'delivered'")
            return False
        
        print("✅ All delivery confirmation stock update tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_partial_delivery_confirmation():
    """Test partial delivery confirmation where only some items are received"""
    print("\n🧪 Testing partial delivery confirmation...")
    
    try:
        # Create test data (similar to above but simpler)
        head_manager = User.objects.get_or_create(
            username='test_head_manager2',
            defaults={
                'email': 'head2@test.com',
                'password': 'testpass123',
                'role': 'head_manager',
                'first_name': 'Test',
                'last_name': 'Manager2'
            }
        )[0]
        
        warehouse = Warehouse.objects.get_or_create(
            name='Test Warehouse 2',
            defaults={
                'address': 'Test Location 2',
                'manager_name': head_manager.get_full_name(),
                'capacity': 1000,
                'current_utilization': 0
            }
        )[0]
        
        product = WarehouseProduct.objects.create(
            product_id='PTP001',
            product_name='Partial Test Product',
            sku='PTP001-SKU',
            quantity_in_stock=100,
            unit_price=Decimal('20.00'),
            category='construction',
            supplier=supplier,
            warehouse=warehouse
        )
        
        supplier = Supplier.objects.get_or_create(
            name='Test Supplier 2',
            defaults={
                'email': 'supplier2@test.com',
                'phone': '1234567891',
                'address': 'Test Address 2'
            }
        )[0]
        
        purchase_order = PurchaseOrder.objects.create(
            order_number='TEST-PO-002',
            supplier=supplier,
            created_by=head_manager,
            order_date=timezone.now().date(),
            status='in_transit',
            total_amount=Decimal('400.00'),
            delivery_address='Test Delivery Address 2'
        )
        
        item = PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product,
            quantity_ordered=25,
            unit_price=Decimal('20.00')
        )
        
        initial_stock = product.quantity_in_stock
        print(f"📊 Initial stock: {initial_stock}")
        
        # Confirm delivery with only partial items received (empty received_items list)
        client = Client()
        client.force_login(head_manager)
        
        response = client.post(
            f'/inventory/purchase-orders/{purchase_order.id}/confirm-delivery/',
            {
                'delivery_condition': 'damaged',
                'all_items_received': 'false',
                'delivery_notes': 'Some items were damaged',
                'received_items': '[]'  # No items received
            }
        )
        
        if response.status_code != 200:
            print(f"❌ API call failed with status {response.status_code}")
            return False
        
        # Refresh objects
        product.refresh_from_db()
        item.refresh_from_db()
        
        # Verify stock was NOT updated (no items received)
        if product.quantity_in_stock != initial_stock:
            print(f"❌ Stock should not have changed: got {product.quantity_in_stock}, expected {initial_stock}")
            return False
        
        # Verify item is marked as having issues
        if not item.has_issues:
            print("❌ Item should be marked as having issues")
            return False
        
        print("✅ Partial delivery confirmation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Partial delivery test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting delivery confirmation stock update tests...\n")
    
    success1 = test_delivery_confirmation_stock_update()
    success2 = test_partial_delivery_confirmation()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Warehouse stock updates are working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)
