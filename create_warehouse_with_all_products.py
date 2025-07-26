#!/usr/bin/env python3
"""
Create a main warehouse and add all 100 products to it with proper stock levels
"""

import sqlite3
import random
from datetime import datetime, timedelta

# Database connection
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("CREATING MAIN WAREHOUSE WITH ALL 100 PRODUCTS")
print("=" * 60)

# Create the main warehouse
warehouse_data = (
    'EZM Main Construction Warehouse',
    'Industrial Zone, Addis Ababa, Ethiopia\nSector 5, Plot 123\nNear Ring Road',
    '+251-11-555-0100',
    'warehouse@ezmtrade.com',
    'Ato Mulugeta Bekele',
    15000,  # capacity
    0,      # current_utilization (will be calculated)
    1,      # is_active
)

print("\n1. Creating main warehouse...")
try:
    cursor.execute("""
        INSERT OR REPLACE INTO Inventory_warehouse 
        (name, address, phone, email, manager_name, capacity, current_utilization, is_active, created_date, updated_date) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, warehouse_data)
    
    # Get the warehouse ID
    cursor.execute("SELECT id FROM Inventory_warehouse WHERE name = ?", (warehouse_data[0],))
    warehouse_id = cursor.fetchone()[0]
    print(f"✅ Created warehouse: {warehouse_data[0]} (ID: {warehouse_id})")
    
except Exception as e:
    print(f"❌ Error creating warehouse: {e}")
    conn.close()
    exit(1)

# Get all products from the database
print("\n2. Retrieving all products...")
cursor.execute("""
    SELECT id, name, category, price, material, size, variation, 
           supplier_company, batch_number, room, shelf, floor, storing_condition
    FROM Inventory_product 
    ORDER BY id
""")
all_products = cursor.fetchall()
print(f"📦 Found {len(all_products)} products to add to warehouse")

# Get the first available supplier ID
cursor.execute("SELECT id, name FROM Inventory_supplier ORDER BY id LIMIT 1")
supplier_result = cursor.fetchone()
if supplier_result:
    supplier_id, supplier_name = supplier_result
    print(f"📋 Using supplier: {supplier_name} (ID: {supplier_id})")
else:
    print("❌ No suppliers found!")
    conn.close()
    exit(1)

print("\n3. Adding all products to warehouse...")
warehouse_products_created = 0
total_utilization = 0

for product in all_products:
    product_id, name, category, price, material, size, variation, supplier_company, batch_number, room, shelf, floor, storing_condition = product
    
    try:
        # Generate warehouse-specific data
        stock_quantity = random.randint(100, 2000)  # Large warehouse quantities
        cost_price = float(price) * 0.75  # Cost is 75% of selling price (25% markup)
        min_stock = max(50, stock_quantity // 20)  # 5% of stock as minimum
        max_stock = stock_quantity * 4  # 4x current stock as maximum
        reorder_point = max(100, stock_quantity // 10)  # 10% of stock as reorder point
        
        # Generate SKU and barcode
        category_code = category[:3].upper() if category else 'GEN'
        sku = f"{category_code}-{product_id:04d}"
        barcode = f"251{random.randint(1000000000, 9999999999)}"
        
        # Calculate weight based on product type
        weight = None
        if 'cement' in name.lower() or 'concrete' in name.lower():
            if '50kg' in name:
                weight = 50.0
            elif '25kg' in name:
                weight = 25.0
            elif 'ton' in name.lower():
                weight = 1000.0
            else:
                weight = random.uniform(20.0, 100.0)
        elif 'brick' in name.lower() or 'block' in name.lower():
            weight = random.uniform(2.0, 15.0)
        elif 'sheet' in name.lower() or 'tile' in name.lower():
            weight = random.uniform(5.0, 25.0)
        elif 'tool' in category.lower() or 'drill' in name.lower() or 'hammer' in name.lower():
            weight = random.uniform(0.5, 10.0)
        elif 'pipe' in name.lower():
            weight = random.uniform(1.0, 20.0)
        else:
            weight = random.uniform(0.1, 50.0)
        
        # Calculate dimensions based on product type
        dimensions = ""
        if 'block' in name.lower() and 'cm' in name:
            # Extract dimensions from name if available
            dimensions = name.split('cm')[0].split()[-1] + "cm" if 'x' in name else ""
        elif 'sheet' in name.lower():
            if '2m' in name:
                dimensions = "200 x 90 x 0.5 cm"
            elif '3m' in name:
                dimensions = "300 x 90 x 0.5 cm"
            elif '4m' in name:
                dimensions = "400 x 90 x 0.5 cm"
        elif 'tile' in name.lower():
            if '30x30' in name:
                dimensions = "30 x 30 x 1 cm"
            elif '60x60' in name:
                dimensions = "60 x 60 x 1 cm"
        
        if not dimensions:
            dimensions = f"{random.randint(10, 200)} x {random.randint(10, 200)} x {random.randint(1, 50)} cm"
        
        # Generate warehouse location
        aisle = random.choice(['A', 'B', 'C', 'D', 'E'])
        section = random.randint(1, 20)
        level = random.randint(1, 5)
        warehouse_location = f"Aisle {aisle}, Section {section}, Level {level}"
        
        # Generate batch info
        batch_code = f"{category_code}{datetime.now().strftime('%Y%m')}{random.randint(100, 999)}"
        arrival_date = datetime.now() - timedelta(days=random.randint(1, 90))
        
        # Set expiry date for applicable products
        expiry_date = None
        if any(word in name.lower() for word in ['cement', 'paint', 'adhesive', 'sealant']):
            expiry_date = (datetime.now() + timedelta(days=random.randint(365, 1095))).date()
        
        # Create warehouse product entry
        warehouse_product_data = (
            f"WP-{product_id:06d}",  # product_id (unique identifier)
            name,                    # product_name
            category,               # category
            stock_quantity,         # quantity_in_stock
            round(cost_price, 2),   # unit_price
            min_stock,              # minimum_stock_level
            max_stock,              # maximum_stock_level
            reorder_point,          # reorder_point
            sku,                    # sku
            barcode,                # barcode
            weight,                 # weight
            dimensions,             # dimensions
            1,                      # is_active
            0,                      # is_discontinued
            warehouse_location,     # warehouse_location
            supplier_id,            # supplier_id
            warehouse_id,           # warehouse_id
            batch_code,             # batch_number
            expiry_date.isoformat() if expiry_date else None,  # expiry_date
        )
        
        cursor.execute("""
            INSERT OR REPLACE INTO Inventory_warehouseproduct 
            (product_id, product_name, category, quantity_in_stock, unit_price, 
             date_added, last_updated, minimum_stock_level, maximum_stock_level, 
             reorder_point, sku, barcode, weight, dimensions, is_active, 
             is_discontinued, warehouse_location, supplier_id, warehouse_id, 
             arrival_date, batch_number, expiry_date) 
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
        """, warehouse_product_data)
        
        warehouse_products_created += 1
        total_utilization += stock_quantity
        
        if warehouse_products_created % 20 == 0:
            print(f"   Added {warehouse_products_created} products to warehouse...")
            
    except Exception as e:
        print(f"❌ Error adding product {name}: {e}")

print(f"✅ Added {warehouse_products_created} products to warehouse")

# Update warehouse utilization
print("\n4. Updating warehouse utilization...")
utilization_percentage = min(100, (total_utilization / warehouse_data[5]) * 100)
cursor.execute("""
    UPDATE Inventory_warehouse 
    SET current_utilization = ?, updated_date = datetime('now')
    WHERE id = ?
""", (int(utilization_percentage), warehouse_id))

print(f"📊 Warehouse utilization: {utilization_percentage:.1f}% ({total_utilization:,} items)")

# Create some inventory movements for tracking
print("\n5. Creating initial inventory movements...")
movements_created = 0
for i in range(min(50, warehouse_products_created)):  # Create movements for first 50 products
    try:
        cursor.execute("SELECT id FROM Inventory_warehouseproduct LIMIT 1 OFFSET ?", (i,))
        warehouse_product_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO Inventory_inventorymovement 
            (warehouse_product_id, movement_type, quantity_change, old_quantity, new_quantity, 
             reason, created_at, created_by_id) 
            VALUES (?, 'initial_stock', ?, 0, ?, 'Initial warehouse stock setup', datetime('now'), NULL)
        """, (warehouse_product_id, random.randint(100, 500), random.randint(100, 500)))
        
        movements_created += 1
    except Exception as e:
        print(f"Warning: Could not create movement record: {e}")

print(f"📝 Created {movements_created} inventory movement records")

# Commit all changes
conn.commit()

# Get final statistics
cursor.execute("SELECT COUNT(*) FROM Inventory_warehouse")
total_warehouses = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Inventory_warehouseproduct")
total_warehouse_products = cursor.fetchone()[0]

cursor.execute("SELECT SUM(quantity_in_stock) FROM Inventory_warehouseproduct")
total_warehouse_stock = cursor.fetchone()[0] or 0

cursor.execute("SELECT COUNT(*) FROM Inventory_inventorymovement")
total_movements = cursor.fetchone()[0]

print("\n" + "=" * 60)
print("🎉 WAREHOUSE CREATION COMPLETED SUCCESSFULLY! 🎉")
print("=" * 60)
print(f"🏭 Total Warehouses: {total_warehouses}")
print(f"📦 Products in Warehouse: {total_warehouse_products}")
print(f"📊 Total Stock Items: {total_warehouse_stock:,}")
print(f"📝 Inventory Movements: {total_movements}")
print(f"🏢 Warehouse Capacity: {warehouse_data[5]:,} items")
print(f"📈 Current Utilization: {utilization_percentage:.1f}%")
print("=" * 60)

# Close connection
conn.close()

print(f"\n🏗️ SUCCESS! Main warehouse created with all {warehouse_products_created} products!")
print("🌐 Warehouse Details:")
print(f"   📍 Name: {warehouse_data[0]}")
print(f"   📍 Address: Industrial Zone, Addis Ababa, Ethiopia")
print(f"   📞 Phone: {warehouse_data[2]}")
print(f"   📧 Email: {warehouse_data[3]}")
print(f"   👨‍💼 Manager: {warehouse_data[4]}")
print(f"   📦 Stock Range: 100-2,000 items per product")
print(f"   💰 Cost Pricing: 75% of retail price (25% markup)")
print(f"   📊 Reorder Points: Set for all products")
print(f"   🏷️ SKUs & Barcodes: Generated for all products")
print(f"   📐 Weights & Dimensions: Calculated based on product type")
print(f"   📍 Warehouse Locations: Assigned to aisles and sections")
print(f"   📅 Batch Tracking: Enabled with arrival dates")
print(f"   ⏰ Expiry Dates: Set for applicable products")
print("\n🎯 The warehouse is now ready for full inventory management!")
