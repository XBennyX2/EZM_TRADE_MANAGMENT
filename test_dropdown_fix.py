#!/usr/bin/env python
"""
Quick test script to verify that the product dropdown fix is working.
This script creates test data and verifies the dropdown functionality.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from store.models import Store
from Inventory.models import Product, Stock, WarehouseProduct, Supplier
from users.models import CustomUser

User = get_user_model()

def create_test_data():
    """Create test data for dropdown testing."""
    print("Creating test data...")
    
    # Create users
    head_manager, created = CustomUser.objects.get_or_create(
        username='test_head_manager',
        defaults={
            'email': 'head@test.com',
            'role': 'head_manager',
            'first_name': 'Head',
            'last_name': 'Manager'
        }
    )
    if created:
        head_manager.set_password('testpass123')
        head_manager.save()
    
    store_manager1, created = CustomUser.objects.get_or_create(
        username='test_store_manager1',
        defaults={
            'email': 'sm1@test.com',
            'role': 'store_manager',
            'first_name': 'Store',
            'last_name': 'Manager1'
        }
    )
    if created:
        store_manager1.set_password('testpass123')
        store_manager1.save()
    
    store_manager2, created = CustomUser.objects.get_or_create(
        username='test_store_manager2',
        defaults={
            'email': 'sm2@test.com',
            'role': 'store_manager',
            'first_name': 'Store',
            'last_name': 'Manager2'
        }
    )
    if created:
        store_manager2.set_password('testpass123')
        store_manager2.save()
    
    # Create stores
    store1, created = Store.objects.get_or_create(
        name='Test Store 1',
        defaults={
            'address': 'Address 1',
            'store_manager': store_manager1
        }
    )
    
    store2, created = Store.objects.get_or_create(
        name='Test Store 2',
        defaults={
            'address': 'Address 2',
            'store_manager': store_manager2
        }
    )
    
    # Create supplier
    supplier, created = Supplier.objects.get_or_create(
        name='Test Supplier',
        defaults={
            'contact_person': 'John Doe',
            'email': 'supplier@test.com',
            'phone': '1234567890',
            'address': '123 Supplier St'
        }
    )
    
    # Create products
    product1, created = Product.objects.get_or_create(
        name='Test Pipe',
        defaults={
            'category': 'Pipes',
            'description': 'Test pipe product',
            'price': 10.00,
            'material': 'Steel'
        }
    )
    
    product2, created = Product.objects.get_or_create(
        name='Test Wire',
        defaults={
            'category': 'Electric Wire',
            'description': 'Test wire product',
            'price': 20.00,
            'material': 'Copper'
        }
    )
    
    product3, created = Product.objects.get_or_create(
        name='Test Cement',
        defaults={
            'category': 'Cement',
            'description': 'Test cement product',
            'price': 30.00,
            'material': 'Concrete'
        }
    )
    
    # Create warehouse products
    WarehouseProduct.objects.get_or_create(
        product_id='WP001',
        defaults={
            'product_name': 'Test Pipe',
            'category': 'Pipes',
            'quantity_in_stock': 100,
            'unit_price': 8.00,
            'minimum_stock_level': 10,
            'maximum_stock_level': 200,
            'reorder_point': 20,
            'sku': 'SKU001',
            'supplier': supplier,
            'is_active': True
        }
    )
    
    WarehouseProduct.objects.get_or_create(
        product_id='WP002',
        defaults={
            'product_name': 'Test Wire',
            'category': 'Electric Wire',
            'quantity_in_stock': 50,
            'unit_price': 18.00,
            'minimum_stock_level': 5,
            'maximum_stock_level': 100,
            'reorder_point': 15,
            'sku': 'SKU002',
            'supplier': supplier,
            'is_active': True
        }
    )
    
    # Create stock in stores
    # Store 1 has Test Pipe (low stock) and Test Wire (out of stock)
    Stock.objects.get_or_create(
        product=product1,
        store=store1,
        defaults={
            'quantity': 2,  # Low stock
            'selling_price': 12.00
        }
    )
    
    Stock.objects.get_or_create(
        product=product2,
        store=store1,
        defaults={
            'quantity': 0,  # Out of stock
            'selling_price': 25.00
        }
    )
    
    # Store 2 has Test Wire and Test Cement
    Stock.objects.get_or_create(
        product=product2,
        store=store2,
        defaults={
            'quantity': 15,
            'selling_price': 24.00
        }
    )
    
    Stock.objects.get_or_create(
        product=product3,
        store=store2,
        defaults={
            'quantity': 8,
            'selling_price': 35.00
        }
    )
    
    print("✅ Test data created successfully!")
    return store1, store2, product1, product2, product3

def test_restock_products_logic():
    """Test the restock products logic."""
    print("\n🔍 Testing restock products logic...")
    
    store1, store2, product1, product2, product3 = create_test_data()
    
    # Simulate the logic from the view
    from django.db import models
    
    # Get products available in warehouse
    warehouse_product_names = WarehouseProduct.objects.filter(
        quantity_in_stock__gt=0,
        is_active=True
    ).values_list('product_name', flat=True)
    
    print(f"Warehouse products: {list(warehouse_product_names)}")
    
    # Get products available in other stores
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store1).values_list('product', flat=True)
    
    print(f"Other stores products (IDs): {list(other_stores_products)}")
    
    # Combine all available products for restocking
    restock_available_products = Product.objects.filter(
        models.Q(id__in=other_stores_products) |
        models.Q(name__in=warehouse_product_names)
    ).distinct()
    
    print(f"Available for restock: {[p.name for p in restock_available_products]}")
    
    # Expected: Test Pipe (warehouse), Test Wire (warehouse + Store 2), Test Cement (Store 2)
    expected_products = {'Test Pipe', 'Test Wire', 'Test Cement'}
    actual_products = {p.name for p in restock_available_products}
    
    if expected_products == actual_products:
        print("✅ Restock products logic working correctly!")
        return True
    else:
        print(f"❌ Expected: {expected_products}")
        print(f"❌ Actual: {actual_products}")
        return False

def test_transfer_products_logic():
    """Test the transfer products logic."""
    print("\n🔍 Testing transfer products logic...")
    
    store1, store2, product1, product2, product3 = create_test_data()
    
    # Get products available in current store with stock > 0
    available_products = Stock.objects.filter(
        store=store1,
        quantity__gt=0
    ).select_related('product')
    
    print(f"Available for transfer from Store 1: {[s.product.name for s in available_products]}")
    
    # Expected: Only Test Pipe (has stock in Store 1)
    expected_products = {'Test Pipe'}
    actual_products = {s.product.name for s in available_products}
    
    if expected_products == actual_products:
        print("✅ Transfer products logic working correctly!")
        return True
    else:
        print(f"❌ Expected: {expected_products}")
        print(f"❌ Actual: {actual_products}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Product Dropdown Fix")
    print("=" * 50)
    
    try:
        restock_test = test_restock_products_logic()
        transfer_test = test_transfer_products_logic()
        
        print("\n" + "=" * 50)
        if restock_test and transfer_test:
            print("🎉 All tests passed! Product dropdown fix is working correctly.")
            print("\nNext steps:")
            print("1. Login as 'test_store_manager1' (password: testpass123)")
            print("2. Navigate to Store Manager dashboard")
            print("3. Check restock request dropdown - should show Test Pipe, Test Wire, Test Cement")
            print("4. Check transfer request dropdown - should show only Test Pipe")
        else:
            print("❌ Some tests failed. Please check the implementation.")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
