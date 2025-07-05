#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EZM_TRADE_MANAGMENT.settings')
django.setup()

from Inventory.models import Warehouse, WarehouseProduct, Supplier
from decimal import Decimal
from django.db import models

def setup_warehouse_data():
    print("Setting up warehouse test data...")
    
    # Get or create warehouse
    warehouse, created = Warehouse.objects.get_or_create(
        name="Main Warehouse",
        defaults={
            'address': "123 Industrial Ave, Business District",
            'phone': "+1-555-0123",
            'email': "warehouse@company.com",
            'manager_name': "John Smith",
            'capacity': 10000,
            'current_utilization': 0,
            'is_active': True
        }
    )
    if created:
        print(f"Created warehouse: {warehouse.name}")
    else:
        print(f"Using existing warehouse: {warehouse.name}")
    
    # Get or create supplier
    supplier, created = Supplier.objects.get_or_create(
        name="Tech Supplies Inc",
        defaults={
            'contact_person': "Jane Doe",
            'email': "jane@techsupplies.com",
            'phone': "+1-555-0456",
            'address': "456 Tech Street"
        }
    )
    if created:
        print(f"Created supplier: {supplier.name}")
    else:
        print(f"Using existing supplier: {supplier.name}")
    
    # Create sample warehouse products
    products_data = [
        {
            'product_id': 'LAPTOP001',
            'product_name': 'Dell Laptop XPS 13',
            'category': 'electronics',
            'quantity_in_stock': 25,
            'unit_price': Decimal('999.99'),
            'minimum_stock_level': 10,
            'maximum_stock_level': 50,
            'reorder_point': 15,
            'sku': 'DLL-XPS13-001',
            'barcode': '1234567890123',
            'warehouse_location': 'A1-B2',
            'supplier': supplier,
            'warehouse': warehouse
        },
        {
            'product_id': 'MOUSE001',
            'product_name': 'Wireless Mouse Pro',
            'category': 'electronics',
            'quantity_in_stock': 5,  # Low stock
            'unit_price': Decimal('29.99'),
            'minimum_stock_level': 20,
            'maximum_stock_level': 100,
            'reorder_point': 25,
            'sku': 'MSE-WRL-001',
            'barcode': '1234567890124',
            'warehouse_location': 'A2-C1',
            'supplier': supplier,
            'warehouse': warehouse
        },
        {
            'product_id': 'KEYBOARD001',
            'product_name': 'Mechanical Keyboard RGB',
            'category': 'electronics',
            'quantity_in_stock': 0,  # Out of stock
            'unit_price': Decimal('89.99'),
            'minimum_stock_level': 15,
            'maximum_stock_level': 75,
            'reorder_point': 20,
            'sku': 'KBD-MCH-001',
            'barcode': '1234567890125',
            'warehouse_location': 'A3-D1',
            'supplier': supplier,
            'warehouse': warehouse
        },
        {
            'product_id': 'MONITOR001',
            'product_name': '27" 4K Monitor',
            'category': 'electronics',
            'quantity_in_stock': 35,
            'unit_price': Decimal('299.99'),
            'minimum_stock_level': 8,
            'maximum_stock_level': 40,
            'reorder_point': 12,
            'sku': 'MON-4K-001',
            'barcode': '1234567890126',
            'warehouse_location': 'B1-A1',
            'supplier': supplier,
            'warehouse': warehouse
        },
        {
            'product_id': 'CHAIR001',
            'product_name': 'Ergonomic Office Chair',
            'category': 'furniture',
            'quantity_in_stock': 12,
            'unit_price': Decimal('199.99'),
            'minimum_stock_level': 5,
            'maximum_stock_level': 30,
            'reorder_point': 8,
            'sku': 'CHR-ERG-001',
            'barcode': '1234567890127',
            'warehouse_location': 'C1-B2',
            'supplier': supplier,
            'warehouse': warehouse
        },
        {
            'product_id': 'DESK001',
            'product_name': 'Standing Desk Adjustable',
            'category': 'furniture',
            'quantity_in_stock': 8,
            'unit_price': Decimal('399.99'),
            'minimum_stock_level': 3,
            'maximum_stock_level': 20,
            'reorder_point': 5,
            'sku': 'DSK-STD-001',
            'barcode': '1234567890128',
            'warehouse_location': 'C2-A1',
            'supplier': supplier,
            'warehouse': warehouse
        }
    ]
    
    created_count = 0
    for product_data in products_data:
        product, created = WarehouseProduct.objects.get_or_create(
            product_id=product_data['product_id'],
            defaults=product_data
        )
        if created:
            created_count += 1
            print(f"Created product: {product.product_name} (Stock: {product.quantity_in_stock})")
        else:
            print(f"Product already exists: {product.product_name}")
    
    print(f"\nSetup complete!")
    print(f"- Warehouse: {warehouse.name}")
    print(f"- Supplier: {supplier.name}")
    print(f"- Products created: {created_count}")
    print(f"- Total products in warehouse: {WarehouseProduct.objects.filter(warehouse=warehouse).count()}")
    
    # Show stock status summary
    low_stock = WarehouseProduct.objects.filter(warehouse=warehouse, quantity_in_stock__lte=models.F('minimum_stock_level')).count()
    out_of_stock = WarehouseProduct.objects.filter(warehouse=warehouse, quantity_in_stock=0).count()
    print(f"- Low stock items: {low_stock}")
    print(f"- Out of stock items: {out_of_stock}")

if __name__ == "__main__":
    setup_warehouse_data()
