#!/usr/bin/env python
"""
Quick test to verify the stock workflow functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EZM_TRADE_MANAGMENT.settings')
sys.path.append('.')
django.setup()

from Inventory.models import SupplierProduct, Supplier
from Inventory.forms import SupplierProductForm

def test_workflow():
    """Test the stock workflow"""
    print("🧪 Testing Stock Workflow")
    print("=" * 40)
    
    # Test 1: Check if form includes stock_quantity
    print("\n1. Testing SupplierProductForm...")
    
    try:
        form = SupplierProductForm()
        if 'stock_quantity' in form.fields:
            print("✅ Form includes stock_quantity field")
        else:
            print("❌ Form missing stock_quantity field")
            
        # Check form meta
        if 'stock_quantity' not in form._meta.exclude:
            print("✅ stock_quantity not excluded from form")
        else:
            print("❌ stock_quantity excluded from form")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Check existing products
    print("\n2. Testing existing products...")
    
    try:
        products = SupplierProduct.objects.all()[:3]
        for product in products:
            print(f"✅ Product: {product.product_name}")
            print(f"   Stock: {product.stock_quantity}")
            print(f"   Status: {product.get_stock_status_display()}")
            print(f"   Available: {product.is_available()}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 40)
    print("🎉 Test completed!")

if __name__ == "__main__":
    test_workflow()
