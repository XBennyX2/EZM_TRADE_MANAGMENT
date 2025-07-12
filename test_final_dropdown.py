#!/usr/bin/env python
"""
Test script to verify the final dropdown shows only real products.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import Product

def test_final_dropdown():
    """Test that dropdown now shows only real products."""
    print("🔍 Testing Final Product Dropdown")
    print("=" * 40)
    
    # Check what products are in the database
    print("📋 Products in Database:")
    products = Product.objects.all().order_by('name')
    for product in products:
        print(f"   - {product.name} ({product.category})")
    
    print(f"\nTotal products: {products.count()}")
    
    # Test the API endpoint
    print("\n🔍 Testing API Endpoint:")
    client = Client()
    
    try:
        # Login with test user
        User = get_user_model()
        user = User.objects.get(username='test_store_manager1')
        login_success = client.login(username='test_store_manager1', password='testpass123')
        
        if login_success:
            print("✅ Login successful")
            
            # Test restock products API
            response = client.get('/users/api/restock-products/')
            if response.status_code == 200:
                data = response.json()
                api_products = data.get('products', [])
                
                print(f"✅ API returned {len(api_products)} products:")
                for product in api_products:
                    print(f"   - {product['name']} ({product['category']})")
                
                # Verify no test products
                test_keywords = ['test', 'cement', 'wire']
                has_test_products = False
                
                for product in api_products:
                    for keyword in test_keywords:
                        if keyword.lower() in product['name'].lower():
                            print(f"❌ Found test product: {product['name']}")
                            has_test_products = True
                
                if not has_test_products:
                    print("✅ No test products found in API response!")
                    
                    # Check for real products
                    real_products = ['Galvanized Pipe', 'HDPE Pipe', 'Wall Tile']
                    found_real = []
                    
                    for product in api_products:
                        if product['name'] in real_products:
                            found_real.append(product['name'])
                    
                    print(f"✅ Real products found: {found_real}")
                    
                    if len(found_real) == len(real_products):
                        print("🎉 SUCCESS: Dropdown shows only real products!")
                        return True
                    else:
                        print(f"⚠️  Expected {len(real_products)} real products, found {len(found_real)}")
                        return False
                else:
                    print("❌ Test products still present in dropdown")
                    return False
            else:
                print(f"❌ API failed with status {response.status_code}")
                return False
        else:
            print("❌ Login failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Final Dropdown Test")
    print("=" * 50)
    
    success = test_final_dropdown()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FINAL RESULT: SUCCESS!")
        print("\n✅ The dropdown now shows only real products:")
        print("   - Galvanized Pipe")
        print("   - HDPE Pipe")
        print("   - Wall Tile")
        print("\n✅ Test products removed:")
        print("   - Test Cement ❌")
        print("   - Test Pipe ❌")
        print("   - Test Wire ❌")
        print("\n🌐 Ready for testing in browser!")
    else:
        print("❌ Some issues remain. Please check the output above.")

if __name__ == "__main__":
    main()
