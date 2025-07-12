#!/usr/bin/env python
"""
Test script to verify the API endpoints are working correctly.
This script tests the actual HTTP endpoints for product dropdowns.
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from store.models import Store

def test_api_endpoints():
    """Test the API endpoints for product dropdowns."""
    print("🔍 Testing API Endpoints")
    print("=" * 50)
    
    # Create a test client
    client = Client()
    
    try:
        # Try to get the test store manager
        User = get_user_model()
        store_manager = User.objects.get(username='test_store_manager1')
        
        # Login the store manager
        login_success = client.login(username='test_store_manager1', password='testpass123')
        
        if not login_success:
            print("❌ Failed to login test store manager")
            return False
        
        print("✅ Successfully logged in as test_store_manager1")
        
        # Test restock products API
        print("\n🔍 Testing restock products API...")
        response = client.get('/users/api/restock-products/')
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            product_names = [p['name'] for p in products]
            
            print(f"✅ Restock API returned {len(products)} products")
            print(f"   Products: {product_names}")
            
            # Check if expected products are present
            expected = {'Test Pipe', 'Test Wire', 'Test Cement'}
            actual = set(product_names)
            
            if expected.issubset(actual):
                print("✅ All expected products found in restock API")
            else:
                print(f"❌ Missing products: {expected - actual}")
                return False
        else:
            print(f"❌ Restock API failed with status {response.status_code}")
            print(f"   Response: {response.content}")
            return False
        
        # Test transfer products API
        print("\n🔍 Testing transfer products API...")
        response = client.get('/users/api/transfer-products/')
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            product_names = [p['name'] for p in products]
            
            print(f"✅ Transfer API returned {len(products)} products")
            print(f"   Products: {product_names}")
            
            # Check if only expected products are present
            expected = {'Test Pipe'}  # Only product with stock in Store 1
            actual = set(product_names)
            
            if expected == actual:
                print("✅ Correct products found in transfer API")
            else:
                print(f"❌ Expected: {expected}, Actual: {actual}")
                return False
        else:
            print(f"❌ Transfer API failed with status {response.status_code}")
            print(f"   Response: {response.content}")
            return False
        
        # Test unauthorized access
        print("\n🔍 Testing unauthorized access...")
        client.logout()
        
        response = client.get('/users/api/restock-products/')
        if response.status_code == 302:  # Redirect to login
            print("✅ Unauthorized access properly redirected")
        else:
            print(f"❌ Expected redirect (302), got {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during API testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_form_submission():
    """Test actual form submission."""
    print("\n🔍 Testing form submission...")
    
    client = Client()
    
    try:
        # Login
        client.login(username='test_store_manager1', password='testpass123')
        
        # Get a product ID for testing
        from Inventory.models import Product
        test_product = Product.objects.filter(name='Test Pipe').first()
        
        if not test_product:
            print("❌ Test product not found")
            return False
        
        # Test restock request submission
        response = client.post('/users/store-manager/submit-restock-request/', {
            'product_id': test_product.id,
            'requested_quantity': 10,
            'priority': 'medium',
            'reason': 'Testing restock request functionality'
        })
        
        if response.status_code == 302:  # Redirect after successful submission
            print("✅ Restock request submitted successfully")
        else:
            print(f"❌ Restock request failed with status {response.status_code}")
            return False
        
        # Verify the request was created
        from Inventory.models import RestockRequest
        restock_request = RestockRequest.objects.filter(
            product=test_product,
            requested_quantity=10
        ).first()
        
        if restock_request:
            print(f"✅ Restock request created: {restock_request.request_number}")
        else:
            print("❌ Restock request not found in database")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during form submission testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 Testing Product Dropdown API Endpoints")
    print("=" * 60)
    
    # First ensure test data exists
    print("📋 Ensuring test data exists...")
    os.system("python test_dropdown_fix.py > /dev/null 2>&1")
    
    api_test = test_api_endpoints()
    form_test = test_form_submission()
    
    print("\n" + "=" * 60)
    if api_test and form_test:
        print("🎉 All API and form tests passed!")
        print("\n✅ Summary:")
        print("   - Restock API returns warehouse + other store products")
        print("   - Transfer API returns only current store products with stock")
        print("   - Unauthorized access is properly blocked")
        print("   - Form submissions work correctly")
        print("   - Database records are created successfully")
        print("\n🌐 Server is running at: http://127.0.0.1:8000/")
        print("   Login: test_store_manager1 / testpass123")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
