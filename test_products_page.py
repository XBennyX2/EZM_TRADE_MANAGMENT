#!/usr/bin/env python3
"""
Test script to verify that products bought from suppliers appear in the head manager's products page.
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

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import (
    Warehouse, WarehouseProduct, Supplier, PurchaseOrder, 
    PurchaseOrderItem
)

User = get_user_model()

def test_products_page_shows_warehouse_products():
    """Test that the products page shows warehouse products bought from suppliers"""
    print("🧪 Testing products page displays warehouse products...")
    
    try:
        # Create test data
        print("📦 Setting up test data...")
        
        # Get or create head manager
        head_manager, created = User.objects.get_or_create(
            username='test_head_manager_products',
            defaults={
                'email': 'head_products@test.com',
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
            name='Test Warehouse Products',
            defaults={
                'address': 'Test Location Products',
                'manager_name': head_manager.get_full_name(),
                'capacity': 1000,
                'current_utilization': 0
            }
        )
        
        # Create supplier
        supplier, created = Supplier.objects.get_or_create(
            name='Test Supplier Products',
            defaults={
                'email': 'supplier_products@test.com',
                'phone': '1234567890',
                'address': 'Test Address Products'
            }
        )
        
        # Create warehouse products (products bought from suppliers)
        product1, created = WarehouseProduct.objects.get_or_create(
            product_id='TPP001',
            defaults={
                'product_name': 'Test Warehouse Product 1',
                'sku': 'TPP001-SKU',
                'quantity_in_stock': 150,
                'unit_price': Decimal('35.00'),
                'category': 'construction',
                'supplier': supplier,
                'warehouse': warehouse,
                'minimum_stock_level': 20,
                'maximum_stock_level': 500
            }
        )
        
        product2, created = WarehouseProduct.objects.get_or_create(
            product_id='TPP002',
            defaults={
                'product_name': 'Test Warehouse Product 2',
                'sku': 'TPP002-SKU',
                'quantity_in_stock': 75,
                'unit_price': Decimal('45.00'),
                'category': 'electrical',
                'supplier': supplier,
                'warehouse': warehouse,
                'minimum_stock_level': 15,
                'maximum_stock_level': 300
            }
        )
        
        # Create a purchase order to simulate buying these products
        purchase_order = PurchaseOrder.objects.create(
            order_number='TEST-PRODUCTS-PO-001',
            supplier=supplier,
            created_by=head_manager,
            order_date=timezone.now().date(),
            status='delivered',
            total_amount=Decimal('1200.00'),
            delivery_address='Test Delivery Address Products'
        )
        
        # Create purchase order items
        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product1,
            quantity_ordered=100,
            quantity_received=100,
            unit_price=Decimal('35.00'),
            is_confirmed_received=True
        )
        
        PurchaseOrderItem.objects.create(
            purchase_order=purchase_order,
            warehouse_product=product2,
            quantity_ordered=50,
            quantity_received=50,
            unit_price=Decimal('45.00'),
            is_confirmed_received=True
        )
        
        print(f"📊 Created warehouse products:")
        print(f"   Product 1: {product1.product_name} - Stock: {product1.quantity_in_stock}")
        print(f"   Product 2: {product2.product_name} - Stock: {product2.quantity_in_stock}")
        
        # Test the products page
        client = Client()
        client.force_login(head_manager)
        
        print("🌐 Testing products page...")
        
        response = client.get('/inventory/products/')
        
        if response.status_code != 200:
            print(f"❌ Products page failed with status {response.status_code}")
            return False
        
        # Check if the products appear in the response
        content = response.content.decode('utf-8')
        
        if product1.product_name not in content:
            print(f"❌ Product 1 '{product1.product_name}' not found on products page")
            return False
        
        if product2.product_name not in content:
            print(f"❌ Product 2 '{product2.product_name}' not found on products page")
            return False
        
        # Check if supplier information is displayed
        if supplier.name not in content:
            print(f"❌ Supplier '{supplier.name}' not found on products page")
            return False
        
        # Check if stock information is displayed
        if str(product1.quantity_in_stock) not in content:
            print(f"❌ Stock quantity '{product1.quantity_in_stock}' not found on products page")
            return False
        
        # Check if SKU information is displayed
        if product1.sku not in content:
            print(f"❌ SKU '{product1.sku}' not found on products page")
            return False
        
        # Check if price information is displayed
        if str(product1.unit_price) not in content:
            print(f"❌ Price '{product1.unit_price}' not found on products page")
            return False
        
        print("✅ Products page correctly displays warehouse products!")
        
        # Test search functionality
        print("🔍 Testing search functionality...")
        
        search_response = client.get('/inventory/products/?search=Test Warehouse Product 1')
        
        if search_response.status_code != 200:
            print(f"❌ Search failed with status {search_response.status_code}")
            return False
        
        search_content = search_response.content.decode('utf-8')
        
        if product1.product_name not in search_content:
            print(f"❌ Search did not find product 1")
            return False
        
        if product2.product_name in search_content:
            print(f"❌ Search incorrectly included product 2")
            return False
        
        print("✅ Search functionality works correctly!")
        
        # Test category filter
        print("🏷️ Testing category filter...")
        
        category_response = client.get('/inventory/products/?category=construction')
        
        if category_response.status_code != 200:
            print(f"❌ Category filter failed with status {category_response.status_code}")
            return False
        
        category_content = category_response.content.decode('utf-8')
        
        if product1.product_name not in category_content:
            print(f"❌ Category filter did not find construction product")
            return False
        
        print("✅ Category filter works correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_products_page_head_manager_controls():
    """Test that head manager has appropriate controls on the products page"""
    print("\n🧪 Testing head manager controls on products page...")
    
    try:
        # Get existing test data
        head_manager = User.objects.get(username='test_head_manager_products')
        product = WarehouseProduct.objects.get(product_id='TPP001')
        
        # Test the products page with head manager
        client = Client()
        client.force_login(head_manager)
        
        response = client.get('/inventory/products/')
        content = response.content.decode('utf-8')
        
        # Check for head manager specific controls
        if 'warehouse_product_stock_edit' not in content:
            print("❌ Stock edit control not found for head manager")
            return False
        
        if 'warehouse_product_update' not in content:
            print("❌ Product update control not found for head manager")
            return False
        
        if 'warehouse_product_toggle_status' not in content:
            print("❌ Status toggle control not found for head manager")
            return False
        
        # Check for minimum/maximum stock level display
        if str(product.minimum_stock_level) not in content:
            print("❌ Minimum stock level not displayed")
            return False
        
        if str(product.maximum_stock_level) not in content:
            print("❌ Maximum stock level not displayed")
            return False
        
        print("✅ Head manager controls are correctly displayed!")
        return True
        
    except Exception as e:
        print(f"❌ Head manager controls test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting products page tests...\n")
    
    success1 = test_products_page_shows_warehouse_products()
    success2 = test_products_page_head_manager_controls()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Products page correctly shows warehouse products.")
        print("\n📋 Summary:")
        print("✅ Warehouse products (bought from suppliers) appear on products page")
        print("✅ Product information includes stock levels, supplier, SKU, and price")
        print("✅ Search functionality works with warehouse products")
        print("✅ Category filtering works correctly")
        print("✅ Head manager has appropriate controls for warehouse products")
        print("✅ Stock level information is properly displayed")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)
