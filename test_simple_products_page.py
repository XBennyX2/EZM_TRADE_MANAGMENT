#!/usr/bin/env python3
"""
Simple test to check if the products page loads and shows warehouse products.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import WarehouseProduct

User = get_user_model()

def test_products_page_basic():
    """Basic test to see if products page loads"""
    print("🧪 Testing basic products page functionality...")
    
    try:
        # Get an existing head manager
        head_manager = User.objects.filter(role='head_manager').first()
        
        if not head_manager:
            print("❌ No head manager found in database")
            return False
        
        print(f"👤 Using head manager: {head_manager.username}")
        
        # Check if there are any warehouse products
        warehouse_products = WarehouseProduct.objects.all()
        print(f"📦 Found {warehouse_products.count()} warehouse products")
        
        if warehouse_products.exists():
            for product in warehouse_products[:3]:  # Show first 3
                print(f"   - {product.product_name} (Stock: {product.quantity_in_stock})")
        
        # Test the products page
        client = Client()
        client.force_login(head_manager)
        
        print("🌐 Testing products page...")
        
        try:
            response = client.get('/inventory/products/')
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"🔄 Redirected to: {response.get('Location', 'Unknown')}")
                return False
            elif response.status_code == 200:
                print("✅ Products page loaded successfully!")
                
                # Check if the page contains expected content
                content = response.content.decode('utf-8')
                
                if 'Products' in content or 'Inventory' in content:
                    print("✅ Page contains expected content")
                else:
                    print("⚠️ Page loaded but may not contain expected content")
                
                # Check if warehouse products are displayed
                if warehouse_products.exists():
                    found_products = 0
                    for product in warehouse_products[:5]:  # Check first 5
                        if product.product_name in content:
                            found_products += 1
                    
                    print(f"📦 Found {found_products}/{min(5, warehouse_products.count())} products on page")
                    
                    if found_products > 0:
                        print("✅ Warehouse products are displayed on the page!")
                        return True
                    else:
                        print("❌ No warehouse products found on the page")
                        return False
                else:
                    print("⚠️ No warehouse products in database to display")
                    return True
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error accessing products page: {str(e)}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_warehouse_products_exist():
    """Check if warehouse products exist in the database"""
    print("\n🧪 Checking warehouse products in database...")
    
    try:
        warehouse_products = WarehouseProduct.objects.all()
        print(f"📦 Total warehouse products: {warehouse_products.count()}")
        
        if warehouse_products.exists():
            print("📋 Warehouse products found:")
            for product in warehouse_products[:10]:  # Show first 10
                print(f"   - ID: {product.id}, Name: {product.product_name}")
                print(f"     Stock: {product.quantity_in_stock}, Price: {product.unit_price}")
                print(f"     Supplier: {product.supplier.name if product.supplier else 'No supplier'}")
                print(f"     Active: {product.is_active}")
                print()
            return True
        else:
            print("❌ No warehouse products found in database")
            print("💡 This might be why the products page appears empty")
            return False
            
    except Exception as e:
        print(f"❌ Error checking warehouse products: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Starting simple products page test...\n")
    
    success1 = test_warehouse_products_exist()
    success2 = test_products_page_basic()
    
    if success1 and success2:
        print("\n🎉 Products page test completed successfully!")
        print("\n📋 Summary:")
        print("✅ Warehouse products exist in database")
        print("✅ Products page loads correctly")
        print("✅ Warehouse products are displayed on the page")
    else:
        print("\n⚠️ Some issues found:")
        if not success1:
            print("❌ No warehouse products in database")
        if not success2:
            print("❌ Products page not loading correctly")
        print("\n💡 The products page should now show warehouse products instead of catalog products")
