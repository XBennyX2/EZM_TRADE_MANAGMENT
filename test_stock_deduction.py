#!/usr/bin/env python
"""
Test script to verify stock deduction functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EZM_TRADE_MANAGMENT.settings')
sys.path.append('.')
django.setup()

from Inventory.models import SupplierProduct, Supplier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stock_deduction():
    """Test the stock deduction functionality"""
    print("🧪 Testing Stock Deduction Functionality")
    print("=" * 50)
    
    # Get a supplier product with stock
    try:
        product = SupplierProduct.objects.filter(stock_quantity__gt=0).first()
        if not product:
            print("❌ No products with stock found in database")
            return False
            
        print(f"✅ Testing with product: {product.product_name}")
        print(f"   Supplier: {product.supplier.name}")
        print(f"   Initial stock: {product.stock_quantity}")
        
        # Test stock deduction
        original_stock = product.stock_quantity
        test_quantity = min(5, original_stock)
        
        print(f"\n🔄 Testing stock deduction of {test_quantity} units...")
        
        success = product.decrease_stock(test_quantity, "Test deduction")
        
        if success:
            print(f"✅ Stock deduction successful!")
            print(f"   Original stock: {original_stock}")
            print(f"   Deducted: {test_quantity}")
            print(f"   New stock: {product.stock_quantity}")
            print(f"   Expected: {original_stock - test_quantity}")
            
            if product.stock_quantity == original_stock - test_quantity:
                print("✅ Stock calculation is correct!")
            else:
                print("❌ Stock calculation is incorrect!")
                
            # Restore original stock
            product.stock_quantity = original_stock
            product.save()
            print(f"✅ Stock restored to: {product.stock_quantity}")
            
        else:
            print("❌ Stock deduction failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Stock deduction test completed successfully!")
    return True

def test_payment_flow_simulation():
    """Simulate the payment flow to test stock deduction"""
    print("\n🧪 Testing Payment Flow Simulation")
    print("=" * 50)
    
    try:
        # Get a supplier product with stock
        product = SupplierProduct.objects.filter(stock_quantity__gt=0).first()
        if not product:
            print("❌ No products with stock found")
            return False
            
        print(f"✅ Simulating payment for: {product.product_name}")
        print(f"   Initial stock: {product.stock_quantity}")
        
        # Simulate order items structure like in payment confirmation
        order_items = [{
            'product_id': product.id,
            'quantity': 2,
            'price': str(product.unit_price),
            'total_price': str(product.unit_price * 2),
            'product_name': product.product_name
        }]
        
        print(f"\n🔄 Simulating payment confirmation with order items:")
        for item in order_items:
            print(f"   - {item['product_name']}: {item['quantity']} units")
        
        # Simulate the payment confirmation logic
        original_stock = product.stock_quantity
        
        for item_data in order_items:
            try:
                # Get the supplier product (like in payment confirmation)
                supplier_product = SupplierProduct.objects.get(
                    id=item_data.get('product_id'),
                    supplier=product.supplier
                )
                
                quantity_ordered = item_data.get('quantity', 1)
                
                print(f"\n🔄 Processing item: {supplier_product.product_name}")
                print(f"   Quantity to deduct: {quantity_ordered}")
                print(f"   Current stock: {supplier_product.stock_quantity}")
                
                # Check if supplier has sufficient stock
                if not supplier_product.can_fulfill_quantity(quantity_ordered):
                    print(f"⚠️  Insufficient stock warning!")
                    print(f"   Requested: {quantity_ordered}, Available: {supplier_product.stock_quantity}")
                
                # Decrease supplier stock (like in payment confirmation)
                success = supplier_product.decrease_stock(
                    quantity_ordered,
                    f"Test purchase order - Payment confirmed"
                )
                
                if success:
                    print(f"✅ Stock decreased successfully!")
                    print(f"   New stock: {supplier_product.stock_quantity}")
                else:
                    print(f"❌ Failed to decrease stock!")
                    
            except SupplierProduct.DoesNotExist:
                print(f"❌ SupplierProduct not found for ID: {item_data.get('product_id')}")
                continue
        
        # Restore original stock
        product.refresh_from_db()
        print(f"\n📊 Final Results:")
        print(f"   Original stock: {original_stock}")
        print(f"   Final stock: {product.stock_quantity}")
        print(f"   Expected stock: {original_stock - 2}")
        
        if product.stock_quantity == original_stock - 2:
            print("✅ Payment flow simulation successful!")
            
            # Restore stock
            product.stock_quantity = original_stock
            product.save()
            print(f"✅ Stock restored to: {product.stock_quantity}")
            return True
        else:
            print("❌ Payment flow simulation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during payment flow simulation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Stock Deduction Tests")
    
    test1_success = test_stock_deduction()
    test2_success = test_payment_flow_simulation()
    
    if test1_success and test2_success:
        print("\n🟢 All tests passed! Stock deduction is working correctly.")
    else:
        print("\n🔴 Some tests failed. Stock deduction needs investigation.")
