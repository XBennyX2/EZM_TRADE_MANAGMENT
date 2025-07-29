#!/usr/bin/env python3
"""
Create minimal test data for delivery confirmation testing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from Inventory.models import Supplier, PurchaseOrder, PurchaseOrderItem, Warehouse, WarehouseProduct
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

def create_minimal_test_data():
    """Create minimal test data for delivery confirmation"""
    print("Creating minimal test data...")
    
    # Create head manager
    head_manager, created = User.objects.get_or_create(
        username='head_manager',
        defaults={
            'email': 'head.manager@test.com',
            'first_name': 'Head',
            'last_name': 'Manager',
            'role': 'head_manager',
            'is_staff': True,
        }
    )
    if created:
        head_manager.set_password('testpass123')
        head_manager.save()
        print(f"✅ Created head manager: {head_manager.username}")
    else:
        print(f"✅ Head manager already exists: {head_manager.username}")
    
    # Create supplier
    supplier, created = Supplier.objects.get_or_create(
        name='Test Supplier',
        defaults={
            'email': 'supplier@test.com',
            'phone': '+1234567890',
            'address': '123 Test St',
            'contact_person': 'John Doe',
        }
    )
    if created:
        print(f"✅ Created supplier: {supplier.name}")
    else:
        print(f"✅ Supplier already exists: {supplier.name}")
    
    # Create warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        name='Test Warehouse',
        defaults={
            'address': 'Test Address',
            'capacity': 1000,
        }
    )
    if created:
        print(f"✅ Created warehouse: {warehouse.name}")
    else:
        print(f"✅ Warehouse already exists: {warehouse.name}")
    
    # Create warehouse product with minimal required fields
    warehouse_product, created = WarehouseProduct.objects.get_or_create(
        product_id='TEST-001',
        defaults={
            'product_name': 'Test Product',
            'category': 'electronics',
            'quantity_in_stock': 0,
            'unit_price': Decimal('100.00'),
            'sku': 'TEST-SKU-001',
        }
    )
    if created:
        print(f"✅ Created warehouse product: {warehouse_product.product_name}")
    else:
        print(f"✅ Warehouse product already exists: {warehouse_product.product_name}")
    
    # Create test orders
    orders = []
    for i, status in enumerate(['in_transit', 'payment_confirmed'], 1):
        order, created = PurchaseOrder.objects.get_or_create(
            order_number=f'TEST-PO-{i:03d}',
            defaults={
                'supplier': supplier,
                'status': status,
                'total_amount': Decimal('500.00'),
                'notes': f'Test order for delivery confirmation - {status}',
                'created_by': head_manager,
                'ordered_at': timezone.now(),
            }
        )
        if created:
            print(f"✅ Created order: {order.order_number} (status: {order.status})")
            
            # Create order item
            item, created = PurchaseOrderItem.objects.get_or_create(
                purchase_order=order,
                warehouse_product=warehouse_product,
                defaults={
                    'quantity_ordered': 10,
                    'unit_price': Decimal('50.00'),
                    'total_price': Decimal('500.00'),
                    'quantity_received': 0,
                    'is_confirmed_received': False,
                }
            )
            if created:
                print(f"✅ Created order item: {item.warehouse_product.product_name} (qty: {item.quantity_ordered})")
        else:
            print(f"✅ Order already exists: {order.order_number}")
        
        orders.append(order)
    
    return head_manager, orders

def main():
    """Main function"""
    print("🚀 Creating Minimal Test Data for Delivery Confirmation")
    print("=" * 60)
    
    try:
        head_manager, orders = create_minimal_test_data()
        
        print("\n" + "=" * 60)
        print("🎉 Test Data Creation Complete!")
        print(f"\nTest Credentials:")
        print(f"Username: {head_manager.username}")
        print(f"Password: testpass123")
        print(f"Role: {head_manager.role}")
        
        print(f"\nTest Orders Available for Delivery Confirmation:")
        for order in orders:
            print(f"- Order ID: {order.id}")
            print(f"  Order Number: {order.order_number}")
            print(f"  Status: {order.status}")
            print(f"  Items: {order.items.count()}")
            print(f"  API Endpoint: POST /inventory/purchase-orders/{order.id}/confirm-delivery/")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("🟢 Test data created successfully!")
        print("\nYou can now test the delivery confirmation functionality using:")
        print("python delivery_diagnosis_tool.py")
    else:
        print("🔴 Test data creation failed.")