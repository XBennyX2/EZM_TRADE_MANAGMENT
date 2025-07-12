#!/usr/bin/env python
"""
Simple script to remove test products.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import Product, Stock, WarehouseProduct, RestockRequest, StoreStockTransferRequest

def main():
    print("🧹 Removing Test Products")
    print("=" * 30)
    
    # List of test product names to remove
    test_product_names = [
        'Test Cement',
        'Test Pipe', 
        'Test Wire'
    ]
    
    for product_name in test_product_names:
        try:
            # Find the product
            product = Product.objects.get(name=product_name)
            print(f"\n🗑️  Removing: {product.name}")
            
            # Remove related records first
            
            # Remove Stock records
            stock_count = Stock.objects.filter(product=product).count()
            if stock_count > 0:
                Stock.objects.filter(product=product).delete()
                print(f"   - Deleted {stock_count} stock records")
            
            # Remove RestockRequest records
            restock_count = RestockRequest.objects.filter(product=product).count()
            if restock_count > 0:
                RestockRequest.objects.filter(product=product).delete()
                print(f"   - Deleted {restock_count} restock requests")
            
            # Remove StoreStockTransferRequest records
            transfer_count = StoreStockTransferRequest.objects.filter(product=product).count()
            if transfer_count > 0:
                StoreStockTransferRequest.objects.filter(product=product).delete()
                print(f"   - Deleted {transfer_count} transfer requests")
            
            # Remove WarehouseProduct records (by name matching)
            warehouse_count = WarehouseProduct.objects.filter(product_name=product.name).count()
            if warehouse_count > 0:
                WarehouseProduct.objects.filter(product_name=product.name).delete()
                print(f"   - Deleted {warehouse_count} warehouse products")
            
            # Finally remove the product itself
            product.delete()
            print(f"   ✅ Successfully deleted: {product_name}")
            
        except Product.DoesNotExist:
            print(f"   ⚠️  Product '{product_name}' not found - already removed or doesn't exist")
        except Exception as e:
            print(f"   ❌ Error removing '{product_name}': {e}")
    
    # Show remaining products
    print("\n📋 Remaining Products:")
    remaining_products = Product.objects.all().order_by('name')
    for product in remaining_products:
        print(f"   - {product.name} ({product.category})")
    
    print(f"\n✅ Total remaining products: {remaining_products.count()}")
    print("🎉 Test product removal complete!")

if __name__ == "__main__":
    main()
