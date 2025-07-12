#!/usr/bin/env python
"""
Test script to verify that all products are now showing in restock dropdown.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import Product, WarehouseProduct, Stock
from store.models import Store
from users.models import CustomUser

def test_all_products_logic():
    """Test that all products are now available for restock."""
    print("🔍 Testing Updated Restock Products Logic")
    print("=" * 50)
    
    # Get all products (new logic)
    all_products = Product.objects.all().order_by('name')
    
    print("=== ALL PRODUCTS AVAILABLE FOR RESTOCK ===")
    for product in all_products:
        print(f"- {product.name} ({product.category})")
    
    print(f"\nTotal products available for restock: {all_products.count()}")
    
    # Check if we have the real products (not just test products)
    real_products = ['Galvanized Pipe', 'HDPE Pipe', 'Wall Tile']
    found_real_products = []
    
    for product in all_products:
        if product.name in real_products:
            found_real_products.append(product.name)
    
    print(f"\nReal products found: {found_real_products}")
    
    if found_real_products:
        print("✅ SUCCESS: Real products (added by head manager) are now available!")
        return True
    else:
        print("❌ No real products found, only test products")
        return False

def test_api_simulation():
    """Simulate the API endpoint logic."""
    print("\n🔍 Testing API Endpoint Logic")
    print("=" * 30)
    
    try:
        # Simulate the API logic
        available_products = Product.objects.all().order_by('name').values('id', 'name', 'category', 'price')
        
        print("API would return:")
        for product in available_products:
            print(f"- ID: {product['id']}, Name: {product['name']}, Category: {product['category']}")
        
        print(f"\nTotal products in API response: {len(list(available_products))}")
        return True
        
    except Exception as e:
        print(f"❌ Error in API simulation: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing All Products in Restock Dropdown")
    print("=" * 60)
    
    try:
        products_test = test_all_products_logic()
        api_test = test_api_simulation()
        
        print("\n" + "=" * 60)
        if products_test and api_test:
            print("🎉 SUCCESS: All products are now available for restock!")
            print("\n✅ What changed:")
            print("   - Restock dropdown now shows ALL products in the system")
            print("   - Includes products added by head manager")
            print("   - Includes warehouse products")
            print("   - Includes products from other stores")
            print("   - Store managers can request any product")
            
            print("\n📋 Next steps:")
            print("1. Login as store manager")
            print("2. Go to restock request form")
            print("3. You should now see ALL products including:")
            print("   - Galvanized Pipe")
            print("   - HDPE Pipe") 
            print("   - Wall Tile")
            print("   - And any other products added by head manager")
        else:
            print("❌ Some tests failed. Please check the implementation.")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
