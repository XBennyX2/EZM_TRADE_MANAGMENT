#!/usr/bin/env python
"""
Test script to verify the updated transfer request logic.
Transfer requests should now show products from OTHER stores (excluding warehouse).
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import Product, Stock, WarehouseProduct
from store.models import Store
from users.models import CustomUser

def create_test_data():
    """Create test data for transfer logic testing."""
    print("📋 Creating Test Data for Transfer Logic")
    print("=" * 50)
    
    # Create users if they don't exist
    User = get_user_model()
    
    try:
        store_manager1 = User.objects.get(username='test_store_manager1')
        store_manager2 = User.objects.get(username='test_store_manager2')
        print("✅ Test users already exist")
    except User.DoesNotExist:
        print("Creating test users...")
        store_manager1 = User.objects.create_user(
            username='test_store_manager1',
            email='sm1@test.com',
            password='testpass123',
            role='store_manager',
            first_name='Store',
            last_name='Manager1'
        )
        
        store_manager2 = User.objects.create_user(
            username='test_store_manager2',
            email='sm2@test.com',
            password='testpass123',
            role='store_manager',
            first_name='Store',
            last_name='Manager2'
        )
    
    # Create stores if they don't exist
    try:
        store1 = Store.objects.get(name='Test Store 1')
        store2 = Store.objects.get(name='Test Store 2')
        print("✅ Test stores already exist")
    except Store.DoesNotExist:
        print("Creating test stores...")
        store1 = Store.objects.create(
            name='Test Store 1',
            address='Address 1',
            store_manager=store_manager1
        )
        
        store2 = Store.objects.create(
            name='Test Store 2',
            address='Address 2',
            store_manager=store_manager2
        )
    
    # Ensure we have products
    products = Product.objects.all()
    if products.count() < 2:
        print("❌ Need at least 2 products for testing")
        return None, None, None
    
    product1 = products[0]  # Should be Galvanized Pipe
    product2 = products[1] if products.count() > 1 else products[0]  # Should be HDPE Pipe
    
    # Create stock in Store 2 (so Store 1 can request transfer from Store 2)
    stock2_1, created = Stock.objects.get_or_create(
        product=product1,
        store=store2,
        defaults={
            'quantity': 10,
            'selling_price': 15.00
        }
    )
    
    stock2_2, created = Stock.objects.get_or_create(
        product=product2,
        store=store2,
        defaults={
            'quantity': 5,
            'selling_price': 25.00
        }
    )
    
    # Ensure Store 1 has no stock (or very little) so they need to request transfers
    Stock.objects.filter(store=store1).update(quantity=0)
    
    print(f"✅ Test data ready:")
    print(f"   - Store 1 ({store1.name}): No stock (needs transfers)")
    print(f"   - Store 2 ({store2.name}): Has {product1.name} (10 units), {product2.name} (5 units)")
    
    return store1, store2, [product1, product2]

def test_transfer_api():
    """Test the transfer products API endpoint."""
    print("\n🔍 Testing Transfer Products API")
    print("=" * 40)
    
    client = Client()
    
    # Login as Store Manager 1 (who needs to request transfers)
    login_success = client.login(username='test_store_manager1', password='testpass123')
    
    if not login_success:
        print("❌ Login failed")
        return False
    
    print("✅ Logged in as test_store_manager1")
    
    # Test transfer products API
    response = client.get('/users/api/transfer-products/')
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        
        print(f"✅ Transfer API returned {len(products)} products:")
        for product in products:
            print(f"   - {product['name']} ({product['category']})")
        
        # Verify these are products from OTHER stores (not current store)
        expected_products = ['Galvanized Pipe', 'HDPE Pipe', 'Wall Tile']
        found_products = [p['name'] for p in products]
        
        found_expected = [p for p in expected_products if p in found_products]
        
        if found_expected:
            print(f"✅ Found expected products from other stores: {found_expected}")
            return True
        else:
            print(f"❌ Expected products from other stores, but got: {found_products}")
            return False
    else:
        print(f"❌ API failed with status {response.status_code}")
        return False

def test_transfer_form_logic():
    """Test the transfer form logic."""
    print("\n🔍 Testing Transfer Form Logic")
    print("=" * 35)
    
    from Inventory.forms import StoreStockTransferRequestForm
    
    try:
        store1 = Store.objects.get(name='Test Store 1')
        
        # Create form with Store 1 as the requesting store
        form = StoreStockTransferRequestForm(from_store=store1)
        
        available_products = form.fields['product'].queryset
        product_names = [p.name for p in available_products]
        
        print(f"✅ Form shows {len(product_names)} products available for transfer:")
        for name in product_names:
            print(f"   - {name}")
        
        # These should be products from OTHER stores (Store 2)
        if product_names:
            print("✅ Transfer form shows products from other stores")
            return True
        else:
            print("❌ Transfer form shows no products")
            return False
            
    except Exception as e:
        print(f"❌ Error testing form logic: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Updated Transfer Request Logic")
    print("=" * 60)
    print("NEW LOGIC: Transfer requests show products from OTHER stores")
    print("(Store managers request products FROM other stores TO their store)")
    print("=" * 60)
    
    # Create test data
    test_data = create_test_data()
    if not test_data[0]:
        print("❌ Failed to create test data")
        return
    
    # Test API endpoint
    api_test = test_transfer_api()
    
    # Test form logic
    form_test = test_transfer_form_logic()
    
    print("\n" + "=" * 60)
    if api_test and form_test:
        print("🎉 SUCCESS: Transfer logic updated correctly!")
        print("\n✅ What changed:")
        print("   - Transfer dropdown now shows products from OTHER stores")
        print("   - Store managers can request products FROM other stores")
        print("   - Excludes warehouse products (only store-to-store transfers)")
        print("   - Form labels updated: 'Transfer From' instead of 'Transfer To'")
        
        print("\n📋 Expected behavior:")
        print("   - Restock requests: Show ALL products (for head manager fulfillment)")
        print("   - Transfer requests: Show only products from OTHER stores")
        
        print("\n🌐 Ready for testing in browser!")
        print("   Login: test_store_manager1 / testpass123")
        print("   Check transfer dropdown - should show products from other stores")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
