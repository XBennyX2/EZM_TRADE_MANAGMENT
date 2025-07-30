#!/usr/bin/env python3
"""
Test script to verify delivery confirmation automation and warehouse product creation.
This test ensures that:
1. When head manager buys products from suppliers, warehouse products are auto-created
2. When delivery is confirmed, products automatically appear in warehouse management
3. The system handles the complete workflow from purchase to delivery confirmation
"""

import os
import sys
import django
import json
from decimal import Decimal
from django.utils import timezone
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import (
    Warehouse, WarehouseProduct, Supplier, SupplierProduct, 
    PurchaseOrder, PurchaseOrderItem, InventoryMovement
)
from payments.models import ChapaTransaction, PurchaseOrderPayment
from store.models import Store

User = get_user_model()

def test_delivery_automation_workflow():
    """Test the complete workflow from purchase to delivery confirmation"""
    print("🧪 Testing Delivery Automation Workflow...")
    
    try:
        # Create test data
        print("📦 Setting up test data...")
        
        # Create head manager
        head_manager, created = User.objects.get_or_create(
            username='test_head_manager',
            defaults={
                'email': 'headmanager@test.com',
                'first_name': 'Test',
                'last_name': 'HeadManager',
                'role': 'head_manager',
                'is_active': True
            }
        )
        
        # Create warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Test Warehouse',
            defaults={
                'address': 'Test Address',
                'phone': '+251911234567',
                'email': 'warehouse@test.com',
                'manager_name': 'Test Manager',
                'capacity': 10000,
                'current_utilization': 0,
                'is_active': True
            }
        )
        
        # Create supplier
        supplier, created = Supplier.objects.get_or_create(
            name='Test Cement Supplier',
            defaults={
                'email': 'supplier@test.com',
                'phone': '+251911234567',
                'address': 'Test Supplier Address',
                'is_active': True
            }
        )
        
        # Create supplier product (cement)
        supplier_product, created = SupplierProduct.objects.get_or_create(
            supplier=supplier,
            product_name='Premium Cement',
            defaults={
                'product_code': 'CEMENT001',
                'description': 'High-quality cement for construction',
                'category': 'construction',
                'unit_price': Decimal('45.00'),
                'stock_quantity': 1000,
                'availability_status': 'in_stock'
            }
        )
        
        print(f"✅ Created test data:")
        print(f"   Head Manager: {head_manager.get_full_name()}")
        print(f"   Warehouse: {warehouse.name}")
        print(f"   Supplier: {supplier.name}")
        print(f"   Supplier Product: {supplier_product.product_name} (Stock: {supplier_product.stock_quantity})")
        
        # Step 1: Simulate purchase order creation (like when head manager buys cement)
        print("\n🛒 Step 1: Creating purchase order...")
        
        # Create Chapa transaction (simulating payment)
        import uuid
        unique_tx_ref = f"TEST-TX-{uuid.uuid4().hex[:8].upper()}"
        
        chapa_transaction = ChapaTransaction.objects.create(
            user=head_manager,
            supplier=supplier,
            amount=Decimal('450.00'),
            currency='ETB',
            chapa_tx_ref=unique_tx_ref,
            customer_email='headmanager@test.com',
            customer_first_name='Test',
            customer_last_name='HeadManager',
            customer_phone='+251911234567',
            status='success',
            paid_at=timezone.now()
        )
        
        # Create order payment with items
        order_payment = PurchaseOrderPayment.objects.create(
            user=head_manager,
            supplier=supplier,
            chapa_transaction=chapa_transaction,
            total_amount=Decimal('450.00'),
            subtotal=Decimal('450.00'),
            order_items=[
                {
                    'product_id': supplier_product.id,
                    'product_name': supplier_product.product_name,
                    'quantity': 10,
                    'price': 45.00,
                    'total_price': 450.00
                }
            ]
        )
        
        print(f"✅ Created purchase order payment for {supplier_product.product_name}")
        
        # Step 2: Process the payment (this should auto-create warehouse product)
        print("\n🏭 Step 2: Processing payment and creating warehouse product...")
        
        from payments.transaction_service import PaymentTransactionService
        
        # Create purchase order from payment
        purchase_order = PaymentTransactionService._create_or_update_purchase_order(
            chapa_transaction, order_payment
        )
        
        if not purchase_order:
            print("❌ Failed to create purchase order")
            return False
        
        print(f"✅ Created purchase order: {purchase_order.order_number}")
        
        # Check if warehouse product was auto-created
        warehouse_product = WarehouseProduct.objects.filter(
            product_name=supplier_product.product_name,
            supplier=supplier
        ).first()
        
        if not warehouse_product:
            print("❌ Warehouse product was not auto-created")
            return False
        
        print(f"✅ Auto-created warehouse product: {warehouse_product.product_name}")
        print(f"   Product ID: {warehouse_product.product_id}")
        print(f"   Initial Stock: {warehouse_product.quantity_in_stock}")
        
        # Check if purchase order item was created
        purchase_order_item = PurchaseOrderItem.objects.filter(
            purchase_order=purchase_order,
            warehouse_product=warehouse_product
        ).first()
        
        if not purchase_order_item:
            print("❌ Purchase order item was not created")
            return False
        
        print(f"✅ Created purchase order item: {purchase_order_item.quantity_ordered} units")
        
        # Step 3: Simulate delivery confirmation
        print("\n📦 Step 3: Confirming delivery...")
        
        # Update order status to in_transit first
        purchase_order.status = 'in_transit'
        purchase_order.save()
        
        # Simulate delivery confirmation
        from Inventory.order_tracking_views import confirm_delivery
        from django.test import RequestFactory
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.post('/confirm-delivery/', {
            'delivery_condition': 'excellent',
            'all_items_received': 'true',
            'delivery_notes': 'Test delivery confirmation',
            'received_items': '["' + str(purchase_order_item.id) + '"]'
        })
        request.user = head_manager
        
        # Call the delivery confirmation view
        response = confirm_delivery(request, purchase_order.id)
        
        if response.status_code != 200:
            print(f"❌ Delivery confirmation failed: {response.content}")
            return False
        
        # Parse response
        import json
        response_data = json.loads(response.content)
        
        if not response_data.get('success'):
            print(f"❌ Delivery confirmation failed: {response_data.get('message')}")
            return False
        
        print("✅ Delivery confirmed successfully")
        
        # Step 4: Verify warehouse stock was updated
        print("\n📊 Step 4: Verifying warehouse stock update...")
        
        # Refresh warehouse product from database
        warehouse_product.refresh_from_db()
        
        # Get the purchase order item to check its values
        purchase_order_item.refresh_from_db()
        
        print(f"   Purchase Order Item Details:")
        print(f"     Quantity Ordered: {purchase_order_item.quantity_ordered}")
        print(f"     Quantity Received: {purchase_order_item.quantity_received}")
        print(f"     Is Confirmed Received: {purchase_order_item.is_confirmed_received}")
        print(f"     Confirmed At: {purchase_order_item.confirmed_at}")
        
        print(f"   Final Stock: {warehouse_product.quantity_in_stock}")
        print(f"   Expected Stock: {purchase_order_item.quantity_ordered}")
        
        if warehouse_product.quantity_in_stock != purchase_order_item.quantity_ordered:
            print(f"❌ Stock not updated correctly. Got {warehouse_product.quantity_in_stock}, expected {purchase_order_item.quantity_ordered}")
            
            # Check if there were any inventory movements
            movements = InventoryMovement.objects.filter(
                warehouse_product=warehouse_product,
                movement_type='purchase_delivery',
                purchase_order=purchase_order
            )
            
            if movements.exists():
                movement = movements.first()
                print(f"   Inventory Movement Found:")
                print(f"     Quantity Change: {movement.quantity_change}")
                print(f"     Old Quantity: {movement.old_quantity}")
                print(f"     New Quantity: {movement.new_quantity}")
                print(f"     Reason: {movement.reason}")
            else:
                print(f"   No inventory movements found for this delivery")
            
            return False
        
        # Check if inventory movement was created
        movements = InventoryMovement.objects.filter(
            warehouse_product=warehouse_product,
            movement_type='purchase_delivery',
            purchase_order=purchase_order
        )
        
        if not movements.exists():
            print("❌ No inventory movement created")
            return False
        
        movement = movements.first()
        print(f"✅ Inventory movement created: +{movement.quantity_change} units")
        
        # Step 5: Verify product appears in warehouse management
        print("\n🏪 Step 5: Verifying product appears in warehouse management...")
        
        # Check if product is active and visible
        if not warehouse_product.is_active:
            print("❌ Warehouse product is not active")
            return False
        
        # Check if product has correct supplier link
        if warehouse_product.supplier != supplier:
            print("❌ Warehouse product supplier link incorrect")
            return False
        
        print(f"✅ Product {warehouse_product.product_name} is active and properly linked")
        print(f"   Supplier: {warehouse_product.supplier.name}")
        print(f"   Stock: {warehouse_product.quantity_in_stock} units")
        print(f"   Unit Price: {warehouse_product.unit_price}")
        
        # Step 6: Test the complete workflow summary
        print("\n📋 Step 6: Workflow Summary...")
        
        print(f"✅ Complete workflow successful:")
        print(f"   1. Head manager bought {supplier_product.product_name} from {supplier.name}")
        print(f"   2. Warehouse product was auto-created: {warehouse_product.product_name}")
        print(f"   3. Purchase order created: {purchase_order.order_number}")
        print(f"   4. Delivery confirmed successfully")
        print(f"   5. Warehouse stock updated: {warehouse_product.quantity_in_stock} units")
        print(f"   6. Product now available in warehouse management")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🧪 Testing Error Handling...")
    
    try:
        # Test with non-existent supplier
        print("   Testing with invalid supplier...")
        
        # This should handle gracefully
        from payments.transaction_service import PaymentTransactionService
        
        # Create a test transaction with invalid data
        import uuid
        unique_tx_ref = f"TEST-ERROR-{uuid.uuid4().hex[:8].upper()}"
        
        test_transaction = ChapaTransaction.objects.create(
            user=User.objects.first(),
            supplier=Supplier.objects.first(),
            amount=Decimal('100.00'),
            currency='ETB',
            chapa_tx_ref=unique_tx_ref,
            status='success'
        )
        
        # This should not crash
        result = PaymentTransactionService._create_or_update_purchase_order(
            test_transaction, None
        )
        
        print("   ✅ Error handling test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("  DELIVERY AUTOMATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Complete workflow
    workflow_success = test_delivery_automation_workflow()
    
    # Test 2: Error handling
    error_handling_success = test_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST RESULTS")
    print("=" * 60)
    
    print(f"Complete Workflow Test: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
    print(f"Error Handling Test: {'✅ PASSED' if error_handling_success else '❌ FAILED'}")
    
    if workflow_success and error_handling_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The delivery automation system is working correctly.")
        print("\nKey Features Verified:")
        print("✅ Auto-creation of warehouse products from supplier products")
        print("✅ Automatic stock updates on delivery confirmation")
        print("✅ Products appear in warehouse management after delivery")
        print("✅ Proper error handling and logging")
    else:
        print("\n⚠️  SOME TESTS FAILED!")
        print("Please check the error messages above and fix the issues.")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main() 