#!/usr/bin/env python
"""
Test script to verify the supplier inventory management system functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EZM_TRADE_MANAGMENT.settings')
sys.path.append('.')
django.setup()

from Inventory.models import SupplierProduct, Supplier
from Inventory.forms import SupplierStockAdjustmentForm

def test_stock_functionality():
    """Test the stock management functionality"""
    print("🧪 Testing Supplier Inventory Management System")
    print("=" * 50)
    
    # Test 1: Check if SupplierProduct model has stock management methods
    print("\n1. Testing SupplierProduct stock management methods...")
    
    # Get a sample supplier product (or create one for testing)
    try:
        supplier = Supplier.objects.first()
        if not supplier:
            print("❌ No suppliers found in database")
            return
            
        product = SupplierProduct.objects.filter(supplier=supplier).first()
        if not product:
            print("❌ No supplier products found in database")
            return
            
        print(f"✅ Testing with product: {product.product_name}")
        print(f"   Current stock: {product.stock_quantity}")
        
        # Test stock status methods
        print(f"   is_in_stock(): {product.is_in_stock()}")
        print(f"   is_low_stock(): {product.is_low_stock()}")
        print(f"   is_out_of_stock(): {product.is_out_of_stock()}")
        print(f"   can_fulfill_quantity(5): {product.can_fulfill_quantity(5)}")
        print(f"   get_stock_status_display(): {product.get_stock_status_display()}")
        print(f"   get_stock_status_class(): {product.get_stock_status_class()}")
        
    except Exception as e:
        print(f"❌ Error testing stock methods: {str(e)}")
        return
    
    # Test 2: Test stock adjustment form
    print("\n2. Testing SupplierStockAdjustmentForm...")
    
    try:
        form_data = {
            'stock_quantity': 50,
            'adjustment_reason': 'Test stock adjustment'
        }
        
        form = SupplierStockAdjustmentForm(data=form_data, instance=product)
        if form.is_valid():
            print("✅ Stock adjustment form validation passed")
            print(f"   New stock quantity: {form.cleaned_data['stock_quantity']}")
            print(f"   Adjustment reason: {form.cleaned_data['adjustment_reason']}")
        else:
            print(f"❌ Form validation failed: {form.errors}")
            
    except Exception as e:
        print(f"❌ Error testing stock adjustment form: {str(e)}")
    
    # Test 3: Test stock decrease functionality
    print("\n3. Testing stock decrease functionality...")
    
    try:
        original_stock = product.stock_quantity
        test_decrease = min(5, original_stock)  # Don't decrease more than available
        
        if test_decrease > 0:
            success = product.decrease_stock(test_decrease, "Test decrease")
            if success:
                print(f"✅ Stock decrease successful: {original_stock} → {product.stock_quantity}")
                
                # Restore original stock
                product.stock_quantity = original_stock
                product.save()
                print(f"✅ Stock restored to original value: {product.stock_quantity}")
            else:
                print("❌ Stock decrease failed")
        else:
            print("⚠️  Skipping stock decrease test (insufficient stock)")
            
    except Exception as e:
        print(f"❌ Error testing stock decrease: {str(e)}")
    
    # Test 4: Check if SupplierProductForm excludes stock_quantity
    print("\n4. Testing SupplierProductForm excludes stock_quantity...")
    
    try:
        from Inventory.forms import SupplierProductForm
        form = SupplierProductForm()
        
        if 'stock_quantity' not in form.fields:
            print("✅ SupplierProductForm correctly excludes stock_quantity field")
        else:
            print("❌ SupplierProductForm still includes stock_quantity field")
            
    except Exception as e:
        print(f"❌ Error testing SupplierProductForm: {str(e)}")
    
    # Test 5: Test stock notification service
    print("\n5. Testing stock notification service...")
    
    try:
        from Inventory.stock_notification_service import StockNotificationService
        
        # Get low stock summary
        summary = StockNotificationService.get_low_stock_summary()
        print(f"✅ Stock notification service working")
        print(f"   Total products: {summary['total_products']}")
        print(f"   Low stock products: {summary['low_stock_count']}")
        print(f"   Out of stock products: {summary['out_of_stock_count']}")
        
    except Exception as e:
        print(f"❌ Error testing stock notification service: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Stock functionality testing completed!")

if __name__ == "__main__":
    test_stock_functionality()
