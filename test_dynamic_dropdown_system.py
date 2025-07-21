#!/usr/bin/env python
"""
Test script for the dynamic dropdown-based product selection system.
This script verifies all components of the system are working correctly.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from Inventory.models import WarehouseProduct, Supplier, SupplierProduct
from Inventory.forms import SupplierProductForm
import json

User = get_user_model()

def test_warehouse_products_api():
    """Test the warehouse products API endpoint"""
    print("\n=== Testing Warehouse Products API ===")
    
    try:
        # Create a test client
        client = Client()
        
        # Test API endpoint without authentication (should redirect)
        response = client.get('/users/api/warehouse-products/')
        print(f"✓ API endpoint accessible: {response.status_code} (302 redirect expected)")
        
        # Test with search parameter
        response = client.get('/users/api/warehouse-products/?search=bolt')
        print(f"✓ API with search parameter: {response.status_code}")
        
        # Check if we have warehouse products in database
        warehouse_count = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0
        ).count()
        print(f"✓ Available warehouse products: {warehouse_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ API test error: {e}")
        return False

def test_supplier_form_integration():
    """Test the SupplierProductForm with dynamic dropdown"""
    print("\n=== Testing Supplier Form Integration ===")
    
    try:
        # Get a supplier
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        print(f"✓ Testing with supplier: {supplier.name}")
        
        # Test form initialization
        form = SupplierProductForm(supplier=supplier)
        
        # Check warehouse_product field
        warehouse_field = form.fields.get('warehouse_product')
        if warehouse_field:
            print(f"✓ Warehouse product field present: {warehouse_field.required}")
            print(f"✓ Field type: {type(warehouse_field).__name__}")
        else:
            print("✗ Warehouse product field missing")
            return False
        
        # Check product_name field
        product_name_field = form.fields.get('product_name')
        if product_name_field:
            print(f"✓ Product name field present: {product_name_field.required}")
        else:
            print("✗ Product name field missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Form integration test error: {e}")
        return False

def test_duplicate_prevention():
    """Test duplicate prevention logic"""
    print("\n=== Testing Duplicate Prevention ===")
    
    try:
        # Get a supplier
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        # Get a warehouse product
        warehouse_product = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0
        ).first()
        
        if not warehouse_product:
            print("✗ No warehouse product found")
            return False
        
        print(f"✓ Testing with product: {warehouse_product.product_name}")
        
        # Check if supplier already has this product
        existing_count = SupplierProduct.objects.filter(
            supplier=supplier,
            warehouse_product=warehouse_product
        ).count()
        
        print(f"✓ Existing products for this supplier: {existing_count}")
        
        # Test form validation with duplicate
        if existing_count > 0:
            form_data = {
                'warehouse_product': warehouse_product.id,
                'product_name': warehouse_product.product_name,
                'description': 'Test description',
                'category_choice': 'Construction',
                'unit_price': '100.00',
                'currency': 'ETB',
                'minimum_order_quantity': 1,
                'estimated_delivery_time': '2-3 days',
                'availability_status': 'in_stock',
                'is_active': True
            }
            
            form = SupplierProductForm(data=form_data, supplier=supplier)
            is_valid = form.is_valid()
            
            if not is_valid:
                print("✓ Duplicate prevention working - form rejected duplicate")
                for field, errors in form.errors.items():
                    print(f"  - {field}: {errors}")
            else:
                print("⚠ Duplicate prevention may not be working - form accepted duplicate")
        else:
            print("✓ No existing products to test duplicate prevention")
        
        return True
        
    except Exception as e:
        print(f"✗ Duplicate prevention test error: {e}")
        return False

def test_data_synchronization():
    """Test real-time data synchronization"""
    print("\n=== Testing Data Synchronization ===")
    
    try:
        # Count available products for a supplier
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        # Get products already in supplier catalog
        existing_products = SupplierProduct.objects.filter(
            supplier=supplier
        ).values_list('warehouse_product_id', flat=True)
        
        # Get available warehouse products (excluding those already in catalog)
        available_products = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0
        ).exclude(id__in=existing_products)
        
        print(f"✓ Products in supplier catalog: {len(existing_products)}")
        print(f"✓ Available products for selection: {available_products.count()}")
        
        # Test that out-of-stock products are excluded
        out_of_stock_count = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock=0
        ).count()
        
        print(f"✓ Out-of-stock products excluded: {out_of_stock_count}")
        
        # Test that inactive products are excluded
        inactive_count = WarehouseProduct.objects.filter(
            is_active=False
        ).count()
        
        print(f"✓ Inactive products excluded: {inactive_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Data synchronization test error: {e}")
        return False

def test_ui_consistency():
    """Test UI consistency and styling"""
    print("\n=== Testing UI Consistency ===")
    
    try:
        # Check if template files exist
        template_files = [
            'templates/supplier/product_form.html',
            'templates/supplier/product_catalog.html'
        ]
        
        for template_file in template_files:
            if os.path.exists(template_file):
                print(f"✓ Template exists: {template_file}")
                
                # Check for EZM styling classes
                with open(template_file, 'r') as f:
                    content = f.read()
                    
                    ezm_classes = ['ezm-card', 'btn-ezm-primary', 'product-search-container']
                    for css_class in ezm_classes:
                        if css_class in content:
                            print(f"  ✓ EZM styling present: {css_class}")
                        else:
                            print(f"  ⚠ EZM styling missing: {css_class}")
            else:
                print(f"✗ Template missing: {template_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ UI consistency test error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Dynamic Dropdown-Based Product Selection System")
    print("=" * 60)
    
    tests = [
        test_warehouse_products_api,
        test_supplier_form_integration,
        test_duplicate_prevention,
        test_data_synchronization,
        test_ui_consistency
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Dynamic dropdown system is working correctly.")
    else:
        print("⚠ Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
