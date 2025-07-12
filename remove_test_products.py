#!/usr/bin/env python
"""
Script to identify and remove test products from the database.
This will remove test products like ceramics, cement, wire, and any products with 'test' in the name.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import Product, Stock, WarehouseProduct, RestockRequest, StoreStockTransferRequest
from django.db import transaction

def identify_test_products():
    """Identify test products that should be removed."""
    print("🔍 Identifying Test Products to Remove")
    print("=" * 50)

    # Find products that contain test-related keywords
    test_keywords = ['test', 'cement', 'wire', 'ceramic']

    test_products = []

    # Get all products and filter manually to avoid union query issues
    all_products = Product.objects.all()

    for product in all_products:
        for keyword in test_keywords:
            if keyword.lower() in product.name.lower():
                if product not in test_products:
                    test_products.append(product)
                break

    print("Found the following test products:")
    for i, product in enumerate(test_products, 1):
        print(f"{i}. ID: {product.id}, Name: '{product.name}', Category: '{product.category}'")

    return test_products

def check_dependencies(test_products):
    """Check if test products have any dependencies that need to be cleaned up."""
    print("\n🔍 Checking Dependencies")
    print("=" * 30)
    
    dependencies = {}
    
    for product in test_products:
        deps = []
        
        # Check Stock records
        stock_count = Stock.objects.filter(product=product).count()
        if stock_count > 0:
            deps.append(f"Stock records: {stock_count}")
        
        # Check RestockRequest records
        restock_count = RestockRequest.objects.filter(product=product).count()
        if restock_count > 0:
            deps.append(f"Restock requests: {restock_count}")
        
        # Check StoreStockTransferRequest records
        transfer_count = StoreStockTransferRequest.objects.filter(product=product).count()
        if transfer_count > 0:
            deps.append(f"Transfer requests: {transfer_count}")
        
        # Check WarehouseProduct records (by name matching)
        warehouse_count = WarehouseProduct.objects.filter(product_name=product.name).count()
        if warehouse_count > 0:
            deps.append(f"Warehouse products: {warehouse_count}")
        
        if deps:
            dependencies[product] = deps
    
    if dependencies:
        print("Dependencies found:")
        for product, deps in dependencies.items():
            print(f"- {product.name}: {', '.join(deps)}")
    else:
        print("✅ No dependencies found - safe to delete")
    
    return dependencies

def remove_test_products(test_products, dependencies):
    """Remove test products and their dependencies."""
    print("\n🗑️  Removing Test Products")
    print("=" * 30)
    
    try:
        with transaction.atomic():
            for product in test_products:
                print(f"\nRemoving: {product.name}")
                
                # Remove dependencies first
                
                # Remove Stock records
                stock_deleted = Stock.objects.filter(product=product).delete()
                if stock_deleted[0] > 0:
                    print(f"  - Deleted {stock_deleted[0]} stock records")
                
                # Remove RestockRequest records
                restock_deleted = RestockRequest.objects.filter(product=product).delete()
                if restock_deleted[0] > 0:
                    print(f"  - Deleted {restock_deleted[0]} restock requests")
                
                # Remove StoreStockTransferRequest records
                transfer_deleted = StoreStockTransferRequest.objects.filter(product=product).delete()
                if transfer_deleted[0] > 0:
                    print(f"  - Deleted {transfer_deleted[0]} transfer requests")
                
                # Remove WarehouseProduct records (by name matching)
                warehouse_deleted = WarehouseProduct.objects.filter(product_name=product.name).delete()
                if warehouse_deleted[0] > 0:
                    print(f"  - Deleted {warehouse_deleted[0]} warehouse products")
                
                # Finally remove the product itself
                product.delete()
                print(f"  ✅ Deleted product: {product.name}")
        
        print("\n✅ All test products removed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error removing test products: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_removal():
    """Verify that test products have been removed."""
    print("\n✅ Verifying Removal")
    print("=" * 20)

    # Check for remaining test products
    test_keywords = ['test', 'cement', 'wire', 'ceramic']

    remaining_products = []
    all_products = Product.objects.all()

    for product in all_products:
        for keyword in test_keywords:
            if keyword.lower() in product.name.lower():
                remaining_products.append(product)
                break

    if remaining_products:
        print("❌ Some test products still remain:")
        for product in remaining_products:
            print(f"  - {product.name}")
        return False
    else:
        print("✅ All test products successfully removed!")

        # Show remaining products
        print("\n📋 Remaining Products (Real Products):")
        real_products = Product.objects.all().order_by('name')
        for product in real_products:
            print(f"  - {product.name} ({product.category})")

        print(f"\nTotal remaining products: {real_products.count()}")
        return True

def main():
    """Main function to remove test products."""
    print("🧹 Test Product Removal Script")
    print("=" * 60)
    
    # Step 1: Identify test products
    test_products = identify_test_products()
    
    if not test_products:
        print("✅ No test products found to remove!")
        return
    
    # Step 2: Check dependencies
    dependencies = check_dependencies(test_products)
    
    # Step 3: Confirm removal
    print(f"\n⚠️  About to remove {len(test_products)} test products")
    print("This will also remove all related stock, requests, and warehouse records.")
    
    # For automation, we'll proceed without user input
    print("Proceeding with removal...")
    
    # Step 4: Remove test products
    success = remove_test_products(test_products, dependencies)
    
    if success:
        # Step 5: Verify removal
        verify_removal()
        
        print("\n🎉 Test Product Removal Complete!")
        print("\nThe dropdown will now only show real products added by the head manager.")
    else:
        print("\n❌ Test product removal failed. Please check the errors above.")

if __name__ == "__main__":
    main()
