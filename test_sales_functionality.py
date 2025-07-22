#!/usr/bin/env python
"""
Test script to verify sales functionality is working correctly
"""
import os
import sys
import django
import json
import requests
from django.test import Client
from django.contrib.auth import authenticate

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser
from store.models import Store
from Inventory.models import Stock, Product
from transactions.models import Transaction, Receipt

def test_sales_functionality():
    """Test the complete sales workflow"""
    print("🧪 Testing EZM Trade Management Sales Functionality")
    print("=" * 60)
    
    # Get a cashier user
    try:
        cashier = CustomUser.objects.filter(username='test_cashier').first()
        if not cashier:
            print("❌ No test cashier user found")
            return False
        print(f"✅ Found cashier: {cashier.username}")
        print(f"   Store: {cashier.store}")
    except Exception as e:
        print(f"❌ Error finding cashier: {e}")
        return False
    
    # Get some stock items
    try:
        stock_items = Stock.objects.filter(
            store=cashier.store,
            quantity__gt=0
        )[:3]  # Get first 3 items
        
        if not stock_items:
            print("❌ No stock items found for cashier's store")
            return False
        
        print(f"✅ Found {len(stock_items)} stock items:")
        for stock in stock_items:
            print(f"   - {stock.product.name}: {stock.quantity} units @ ETB {stock.selling_price}")
    except Exception as e:
        print(f"❌ Error finding stock items: {e}")
        return False
    
    # Test Django client functionality
    client = Client()
    
    # Login as cashier
    try:
        login_success = client.login(username=cashier.username, password='testpass123')
        if not login_success:
            print("❌ Failed to login as cashier")
            return False
        print("✅ Successfully logged in as cashier")
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test cart functionality
    print("\n🛒 Testing Cart Functionality")
    print("-" * 30)
    
    # Test add to cart
    try:
        test_stock = stock_items[0]
        cart_data = {
            'product_id': test_stock.product.id,
            'quantity': 1
        }
        
        response = client.post(
            '/stores/cashier/add-to-cart/',
            data=json.dumps(cart_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                print("✅ Add to cart successful")
                print(f"   Message: {response_data.get('message')}")
                cart = response_data.get('cart', {})
                print(f"   Cart items: {len(cart.get('items', []))}")
                print(f"   Cart total: ETB {cart.get('total', 0)}")
            else:
                print(f"❌ Add to cart failed: {response_data.get('error')}")
                return False
        else:
            print(f"❌ Add to cart HTTP error: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Add to cart exception: {e}")
        return False
    
    # Test single sale processing
    print("\n💰 Testing Single Sale Processing")
    print("-" * 35)
    
    try:
        sale_data = {
            'product_id': test_stock.product.id,
            'quantity': 1,
            'customer_name': 'Test Customer',
            'customer_phone': '+251911234567',
            'payment_type': 'cash'
        }
        
        response = client.post(
            '/stores/process-single-sale/',
            data=sale_data
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                print("✅ Single sale processing successful")
                print(f"   Receipt ID: {response_data.get('receipt_id')}")
                print(f"   Total Amount: ETB {response_data.get('total_amount')}")
                print(f"   Message: {response_data.get('message')}")
                
                # Verify transaction was created
                receipt_id = response_data.get('receipt_id')
                receipt = Receipt.objects.get(id=receipt_id)
                transaction = receipt.transaction
                print(f"   Transaction ID: {transaction.id}")
                print(f"   Transaction Type: {transaction.transaction_type}")
                
            else:
                print(f"❌ Single sale failed: {response_data.get('error')}")
                return False
        else:
            print(f"❌ Single sale HTTP error: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Single sale exception: {e}")
        return False
    
    print("\n🎉 All tests passed successfully!")
    print("✅ Sales functionality is working correctly")
    return True

if __name__ == "__main__":
    success = test_sales_functionality()
    sys.exit(0 if success else 1)
