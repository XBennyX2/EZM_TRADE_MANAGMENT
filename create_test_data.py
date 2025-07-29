#!/usr/bin/env python3
"""
Create test data for delivery confirmation testing
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from Inventory.models import (
    Supplier, SupplierProduct, Product, PurchaseOrder, 
    PurchaseOrderItem, Warehouse, WarehouseProduct
)
from store.models import Store
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

def create_test_users():
    """Create test users including head manager"""
    print("Creating test users...")
    
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
    supplier_user, created = User.objects.get_or_create(
        username='test_supplier',
        defaults={
            'email': 'supplier@test.com',
            'first_name': 'Test',
            'last_name': 'Supplier',
            'role': 'supplier',
        }
    )
    if created:
        supplier_user.set_password('testpass123')
        supplier_user.save()
        print(f"✅ Created supplier user: {supplier_user.username}")
    else:
        print(f"✅ Supplier user already exists: {supplier_user.username}")
    
    return head_manager, supplier_user

def create_test_store_and_warehouse():
    """Create test store and warehouse"""
    print("Creating test store and warehouse...")
    
    # Create store
    store, created = Store.objects.get_or_create(
        name='Test Store',
        defaults={
            'address': 'Test Location',
            'phone_number': '+1234567890',
        }
    )
    if created:
        print(f"✅ Created store: {store.name}")
    else:
        print(f"✅ Store already exists: {store.name}")
    
    # Create warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        name='Main Warehouse',
        defaults={
            'address': 'Main Location',
            'capacity': 10000,
        }
    )
    if created:
        print(f"✅ Created warehouse: {warehouse.name}")
    else:
        print(f"✅ Warehouse already exists: {warehouse.name}")
    
    return store, warehouse

def create_test_suppliers_and_products(supplier_user, warehouse):
    """Create test suppliers and products"""
    print("Creating test suppliers and products...")
    
    # Create supplier
    supplier, created = Supplier.objects.get_or_create(
        name='Test Supplier Co.',
        defaults={
            'email': 'supplier@testcompany.com',
            'phone': '+1234567890',
            'address': '123 Supplier St',
            'contact_person': 'John Supplier',
        }
    )
    if created:
        print(f"✅ Created supplier: {supplier.name}")
    else:
        print(f"✅ Supplier already exists: {supplier.name}")
    
    # Create products
    products_data = [
        {'name': 'Test Product 1', 'description': 'First test product', 'price': Decimal('100.00')},
        {'name': 'Test Product 2', 'description': 'Second test product', 'price': Decimal('200.00')},
        {'name': 'Test Product 3', 'description': 'Third test product', 'price': Decimal('150.00')},
    ]
    
    products = []
    supplier_products = []
    
    for product_data in products_data:
        # Create base product
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults={
                'description': product_data['description'],
                'category': 'electronics',
                'price': product_data['price'],
                'material': 'Test Material',
            }
        )
        if created:
            print(f"✅ Created product: {product.name}")
        else:
            print(f"✅ Product already exists: {product.name}")
        
        products.append(product)
        
        # Create warehouse product
        warehouse_product, created = WarehouseProduct.objects.get_or_create(
            warehouse=warehouse,
            product_name=product.name,
            defaults={
                'product_description': product.description,
                'quantity_in_stock': 0,
                'unit_price': product_data['price'],
                'reorder_level': 10,
            }
        )
        if created:
            print(f"✅ Created warehouse product: {warehouse_product.product_name}")
        
        # Create supplier product
        supplier_product, created = SupplierProduct.objects.get_or_create(
            supplier=supplier,
            product_name=product.name,
            defaults={
                'product_description': product.description,
                'unit_price': product_data['price'],
                'stock_quantity': 100,
                'minimum_order_quantity': 1,
                'warehouse_product': warehouse_product,
            }
        )
        if created:
            print(f"✅ Created supplier product: {supplier_product.product_name}")
        
        supplier_products.append(supplier_product)
    
    return supplier, supplier_products

def create_test_orders(head_manager, supplier, supplier_products):
    """Create test purchase orders"""
    print("Creating test purchase orders...")
    
    orders_data = [
        {'status': 'in_transit', 'note': 'Test order ready for delivery confirmation'},
        {'status': 'payment_confirmed', 'note': 'Another test order for delivery'},
    ]
    
    orders = []
    
    for i, order_data in enumerate(orders_data, 1):
        # Create purchase order
        order, created = PurchaseOrder.objects.get_or_create(
            order_number=f'PO-TEST-{i:03d}',
            defaults={
                'supplier': supplier,
                'status': order_data['status'],
                'total_amount': Decimal('450.00'),
                'notes': order_data['note'],
                'created_by': head_manager,
                'ordered_at': timezone.now(),
            }
        )
        if created:
            print(f"✅ Created purchase order: {order.order_number} (status: {order.status})")
        else:
            print(f"✅ Purchase order already exists: {order.order_number}")
        
        # Create order items
        for j, supplier_product in enumerate(supplier_products[:2]):  # Use first 2 products
            item, created = PurchaseOrderItem.objects.get_or_create(
                purchase_order=order,
                supplier_product=supplier_product,
                defaults={
                    'warehouse_product': supplier_product.warehouse_product,
                    'quantity_ordered': 5,
                    'unit_price': supplier_product.unit_price,
                    'total_price': supplier_product.unit_price * 5,
                    'quantity_received': 0,
                    'is_confirmed_received': False,
                }
            )
            if created:
                print(f"✅ Created order item: {item.supplier_product.product_name} (qty: {item.quantity_ordered})")
        
        orders.append(order)
    
    return orders

def main():
    """Main function to create all test data"""
    print("🚀 Creating Test Data for Delivery Confirmation")
    print("=" * 50)
    
    try:
        # Create users
        head_manager, supplier_user = create_test_users()
        
        # Create store and warehouse
        store, warehouse = create_test_store_and_warehouse()
        
        # Create suppliers and products
        supplier, supplier_products = create_test_suppliers_and_products(supplier_user, warehouse)
        
        # Create test orders
        orders = create_test_orders(head_manager, supplier, supplier_products)
        
        print("\n" + "=" * 50)
        print("🎉 Test Data Creation Complete!")
        print(f"✅ Created {len(orders)} test orders ready for delivery confirmation")
        print("\nTest Credentials:")
        print(f"Head Manager - Username: head_manager, Password: testpass123")
        print(f"Supplier - Username: test_supplier, Password: testpass123")
        
        print("\nTest Orders:")
        for order in orders:
            print(f"- {order.order_number}: {order.status} ({order.items.count()} items)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🟢 Test data created successfully!")
        print("You can now test the delivery confirmation functionality.")
    else:
        print("\n🔴 Test data creation failed.")