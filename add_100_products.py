#!/usr/bin/env python3
"""
Add 85+ more construction products to reach 100+ total products
"""

import sqlite3
import random

# Database connection
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("ADDING 85+ NEW CONSTRUCTION PRODUCTS")
print("=" * 50)

# 85+ completely new construction products with unique names
new_products = [
    # Cement & Concrete Products (10)
    ('White Portland Cement 25kg', 'construction_materials', 'Premium white cement for decorative work', 1200, 'White Cement', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2001', 'Room 1', 'Shelf 1', 1, 'dry'),
    ('Quick Set Cement 50kg', 'construction_materials', 'Fast-setting cement for urgent repairs', 950, 'Quick Set Cement', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2002', 'Room 1', 'Shelf 2', 1, 'dry'),
    ('Masonry Cement 50kg', 'construction_materials', 'Specialized cement for masonry work', 780, 'Masonry Cement', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2003', 'Room 1', 'Shelf 3', 1, 'dry'),
    ('Concrete Additive 5L', 'construction_materials', 'Concrete strength enhancer additive', 650, 'Chemical Additive', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2004', 'Room 1', 'Shelf 4', 1, 'normal'),
    ('Concrete Sealer 20L', 'construction_materials', 'Protective concrete surface sealer', 1800, 'Acrylic Sealer', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2005', 'Room 1', 'Shelf 5', 1, 'normal'),
    ('Expansion Joint Filler', 'construction_materials', 'Flexible joint filler for concrete', 450, 'Foam Filler', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2006', 'Room 1', 'Shelf 6', 1, 'normal'),
    ('Concrete Bonding Agent 5L', 'construction_materials', 'Adhesive for concrete repairs', 850, 'Polymer Adhesive', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2007', 'Room 1', 'Shelf 7', 1, 'normal'),
    ('Waterproof Concrete Mix 25kg', 'construction_materials', 'Water-resistant concrete mix', 1100, 'Waterproof Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2008', 'Room 1', 'Shelf 8', 1, 'dry'),
    ('Fiber Reinforced Concrete Mix', 'construction_materials', 'Concrete with synthetic fibers', 1350, 'Fiber Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2009', 'Room 1', 'Shelf 9', 1, 'dry'),
    ('Self-Leveling Concrete 25kg', 'construction_materials', 'Self-leveling floor concrete', 1450, 'Self-Level Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2010', 'Room 1', 'Shelf 10', 1, 'dry'),

    # Steel & Metal Products (15)
    ('Rebar 8mm x 12m - Grade 60', 'construction_materials', 'Small diameter reinforcement steel', 650, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2011', 'Room 1', 'Shelf 11', 1, 'normal'),
    ('Rebar 10mm x 12m - Grade 60', 'construction_materials', 'Medium diameter reinforcement steel', 850, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2012', 'Room 1', 'Shelf 12', 1, 'normal'),
    ('Rebar 20mm x 12m - Grade 60', 'construction_materials', 'Large diameter reinforcement steel', 2200, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2013', 'Room 1', 'Shelf 13', 1, 'normal'),
    ('Steel H-Beam 150mm', 'construction_materials', 'Structural steel H-beam', 3500, 'Structural Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2014', 'Room 1', 'Shelf 14', 1, 'normal'),
    ('Steel H-Beam 250mm', 'construction_materials', 'Heavy structural steel H-beam', 5500, 'Structural Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2015', 'Room 1', 'Shelf 15', 1, 'normal'),
    ('Steel Channel 100mm', 'construction_materials', 'Steel channel for framing', 1200, 'Structural Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2016', 'Room 1', 'Shelf 16', 1, 'normal'),
    ('Steel Channel 150mm', 'construction_materials', 'Large steel channel', 1800, 'Structural Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2017', 'Room 1', 'Shelf 17', 1, 'normal'),
    ('Steel Flat Bar 50x5mm', 'construction_materials', 'Flat steel bar for construction', 450, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2018', 'Room 1', 'Shelf 18', 1, 'normal'),
    ('Steel Round Bar 12mm', 'construction_materials', 'Round steel bar', 380, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2019', 'Room 1', 'Shelf 19', 1, 'normal'),
    ('Steel Round Bar 16mm', 'construction_materials', 'Large round steel bar', 550, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2020', 'Room 1', 'Shelf 20', 1, 'normal'),
    ('Galvanized Steel Sheet 1.2mm', 'construction_materials', 'Corrosion-resistant steel sheet', 850, 'Galvanized Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2021', 'Room 2', 'Shelf 1', 1, 'normal'),
    ('Galvanized Steel Sheet 2mm', 'construction_materials', 'Heavy galvanized steel sheet', 1200, 'Galvanized Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2022', 'Room 2', 'Shelf 2', 1, 'normal'),
    ('Steel Mesh Reinforcement 6mm', 'construction_materials', 'Welded steel mesh for slabs', 950, 'Steel Mesh', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2023', 'Room 2', 'Shelf 3', 1, 'normal'),
    ('Steel Mesh Reinforcement 8mm', 'construction_materials', 'Heavy welded steel mesh', 1350, 'Steel Mesh', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2024', 'Room 2', 'Shelf 4', 1, 'normal'),
    ('Expanded Metal Mesh', 'construction_materials', 'Expanded steel mesh for plastering', 650, 'Expanded Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2025', 'Room 2', 'Shelf 5', 1, 'normal'),

    # Bricks & Blocks (15)
    ('Engineering Brick - Blue', 'building_materials', 'High-strength engineering bricks', 18, 'Engineering Clay', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH2026', 'Room 2', 'Shelf 6', 1, 'normal'),
    ('Fire Brick - Refractory', 'building_materials', 'Heat-resistant fire bricks', 45, 'Fire Clay', 'small', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH2027', 'Room 2', 'Shelf 7', 1, 'normal'),
    ('Perforated Brick - Lightweight', 'building_materials', 'Lightweight perforated bricks', 10, 'Perforated Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2028', 'Room 2', 'Shelf 8', 1, 'normal'),
    ('Solid Brick - Dense', 'building_materials', 'Dense solid clay bricks', 12, 'Dense Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2029', 'Room 2', 'Shelf 9', 1, 'normal'),
    ('Interlocking Brick - Stabilized', 'building_materials', 'Cement-stabilized interlocking bricks', 15, 'Stabilized Clay', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH2030', 'Room 2', 'Shelf 10', 1, 'normal'),
    ('Concrete Block 10x20x40cm', 'building_materials', 'Small concrete masonry blocks', 28, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2031', 'Room 2', 'Shelf 11', 1, 'normal'),
    ('Concrete Block 25x20x40cm', 'building_materials', 'Large concrete masonry blocks', 55, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2032', 'Room 2', 'Shelf 12', 1, 'normal'),
    ('Aerated Concrete Block', 'building_materials', 'Lightweight aerated concrete blocks', 65, 'Aerated Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2033', 'Room 2', 'Shelf 13', 1, 'normal'),
    ('Insulated Concrete Block', 'building_materials', 'Thermal insulated concrete blocks', 85, 'Insulated Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2034', 'Room 2', 'Shelf 14', 1, 'normal'),
    ('Decorative Concrete Block', 'building_materials', 'Decorative screen blocks', 95, 'Decorative Concrete', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2035', 'Room 2', 'Shelf 15', 1, 'normal'),
    ('Retaining Wall Block', 'building_materials', 'Interlocking retaining wall blocks', 120, 'Concrete', 'large', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2036', 'Room 2', 'Shelf 16', 1, 'normal'),
    ('Paving Block 20x10x8cm', 'building_materials', 'Standard concrete paving blocks', 35, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2037', 'Room 2', 'Shelf 17', 1, 'normal'),
    ('Paving Block 20x20x8cm', 'building_materials', 'Square concrete paving blocks', 65, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2038', 'Room 2', 'Shelf 18', 1, 'normal'),
    ('Grass Paver Block', 'building_materials', 'Permeable grass paver blocks', 85, 'Concrete', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2039', 'Room 2', 'Shelf 19', 1, 'normal'),
    ('Kerb Stone - Precast', 'building_materials', 'Precast concrete kerb stones', 180, 'Precast Concrete', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2040', 'Room 2', 'Shelf 20', 1, 'normal'),

    # Roofing Materials (10)
    ('Corrugated Iron Sheet 2m - 28 Gauge', 'building_materials', 'Short corrugated iron sheets', 750, 'Galvanized Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2041', 'Room 3', 'Shelf 1', 1, 'normal'),
    ('Corrugated Iron Sheet 4m - 26 Gauge', 'building_materials', 'Long corrugated iron sheets', 1600, 'Galvanized Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2042', 'Room 3', 'Shelf 2', 1, 'normal'),
    ('Aluminum Roofing Sheet 2m', 'building_materials', 'Short aluminum roofing sheets', 1200, 'Aluminum', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2043', 'Room 3', 'Shelf 3', 1, 'normal'),
    ('Aluminum Roofing Sheet 4m', 'building_materials', 'Long aluminum roofing sheets', 2400, 'Aluminum', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2044', 'Room 3', 'Shelf 4', 1, 'normal'),
    ('Clay Roof Tile - Spanish', 'building_materials', 'Spanish-style clay roof tiles', 35, 'Clay', 'small', 'Color: Terracotta', 'finished_product', 'Default Supplier', 'BATCH2045', 'Room 3', 'Shelf 5', 1, 'normal'),
    ('Clay Roof Tile - French', 'building_materials', 'French-style clay roof tiles', 38, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2046', 'Room 3', 'Shelf 6', 1, 'normal'),
    ('Concrete Roof Tile - Flat', 'building_materials', 'Flat concrete roof tiles', 28, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2047', 'Room 3', 'Shelf 7', 1, 'normal'),
    ('Concrete Roof Tile - Curved', 'building_materials', 'Curved concrete roof tiles', 32, 'Concrete', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH2048', 'Room 3', 'Shelf 8', 1, 'normal'),
    ('Ridge Tile - Clay', 'building_materials', 'Clay ridge tiles for roof peaks', 45, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2049', 'Room 3', 'Shelf 9', 1, 'normal'),
    ('Ridge Tile - Concrete', 'building_materials', 'Concrete ridge tiles', 38, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2050', 'Room 3', 'Shelf 10', 1, 'normal'),

    # Power Tools (15)
    ('Cordless Drill 14.4V', 'construction_tools', 'Compact cordless drill', 2800, 'Metal and Plastic', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH2051', 'Room 3', 'Shelf 11', 1, 'normal'),
    ('Cordless Drill 20V Max', 'construction_tools', 'High-power cordless drill', 4200, 'Metal and Plastic', 'medium', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH2052', 'Room 3', 'Shelf 12', 1, 'normal'),
    ('Impact Wrench 1/2"', 'construction_tools', 'Heavy-duty impact wrench', 5500, 'Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2053', 'Room 3', 'Shelf 13', 1, 'normal'),
    ('Rotary Hammer 24mm SDS', 'construction_tools', 'SDS rotary hammer drill', 6800, 'Metal', 'medium', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2054', 'Room 3', 'Shelf 14', 1, 'normal'),
    ('Demolition Hammer 1500W', 'construction_tools', 'Electric demolition hammer', 8500, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2055', 'Room 3', 'Shelf 15', 1, 'normal'),
    ('Angle Grinder 5"', 'construction_tools', 'Medium angle grinder', 2200, 'Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2056', 'Room 3', 'Shelf 16', 1, 'normal'),
    ('Angle Grinder 7.5"', 'construction_tools', 'Large angle grinder', 3200, 'Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2057', 'Room 3', 'Shelf 17', 1, 'normal'),
    ('Circular Saw 6.5"', 'construction_tools', 'Compact circular saw', 3500, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2058', 'Room 3', 'Shelf 18', 1, 'normal'),
    ('Circular Saw 8.25"', 'construction_tools', 'Large circular saw', 4800, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2059', 'Room 3', 'Shelf 19', 1, 'normal'),
    ('Reciprocating Saw 1200W', 'construction_tools', 'Electric reciprocating saw', 3800, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2060', 'Room 3', 'Shelf 20', 1, 'normal'),
    ('Jigsaw Variable Speed', 'construction_tools', 'Variable speed jigsaw', 2800, 'Metal and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2061', 'Room 4', 'Shelf 1', 1, 'normal'),
    ('Router 1200W', 'construction_tools', 'Electric wood router', 4500, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2062', 'Room 4', 'Shelf 2', 1, 'normal'),
    ('Planer 750W', 'construction_tools', 'Electric wood planer', 3200, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2063', 'Room 4', 'Shelf 3', 1, 'normal'),
    ('Belt Sander 900W', 'construction_tools', 'Heavy-duty belt sander', 3800, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2064', 'Room 4', 'Shelf 4', 1, 'normal'),
    ('Orbital Sander 300W', 'construction_tools', 'Finishing orbital sander', 2200, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2065', 'Room 4', 'Shelf 5', 1, 'normal'),

    # Hand Tools (20)
    ('Claw Hammer 20oz', 'hand_tools', 'Heavy-duty claw hammer', 550, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2066', 'Room 4', 'Shelf 6', 1, 'normal'),
    ('Ball Peen Hammer 12oz', 'hand_tools', 'Ball peen hammer for metalwork', 420, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2067', 'Room 4', 'Shelf 7', 1, 'normal'),
    ('Sledge Hammer 5kg', 'hand_tools', 'Heavy sledge hammer', 1200, 'Steel and Wood', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2068', 'Room 4', 'Shelf 8', 1, 'normal'),
    ('Dead Blow Hammer 2kg', 'hand_tools', 'Non-rebound dead blow hammer', 850, 'Steel and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2069', 'Room 4', 'Shelf 9', 1, 'normal'),
    ('Rubber Mallet 16oz', 'hand_tools', 'Soft-face rubber mallet', 380, 'Rubber and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2070', 'Room 4', 'Shelf 10', 1, 'normal'),
    ('Screwdriver Set Phillips', 'hand_tools', 'Phillips head screwdriver set', 450, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2071', 'Room 4', 'Shelf 11', 1, 'normal'),
    ('Screwdriver Set Flathead', 'hand_tools', 'Flathead screwdriver set', 420, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2072', 'Room 4', 'Shelf 12', 1, 'normal'),
    ('Adjustable Wrench 8"', 'hand_tools', 'Small adjustable wrench', 320, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2073', 'Room 4', 'Shelf 13', 1, 'normal'),
    ('Adjustable Wrench 12"', 'hand_tools', 'Large adjustable wrench', 480, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2074', 'Room 4', 'Shelf 14', 1, 'normal'),
    ('Pipe Wrench 10"', 'hand_tools', 'Small pipe wrench', 450, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2075', 'Room 4', 'Shelf 15', 1, 'normal'),
    ('Pipe Wrench 18"', 'hand_tools', 'Large pipe wrench', 850, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2076', 'Room 4', 'Shelf 16', 1, 'normal'),
    ('Combination Wrench Set', 'hand_tools', 'Complete combination wrench set', 1200, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2077', 'Room 4', 'Shelf 17', 1, 'normal'),
    ('Socket Set 1/2" Drive', 'hand_tools', 'Professional socket set', 1800, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2078', 'Room 4', 'Shelf 18', 1, 'normal'),
    ('Socket Set 3/8" Drive', 'hand_tools', 'Compact socket set', 1200, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2079', 'Room 4', 'Shelf 19', 1, 'normal'),
    ('Torque Wrench 1/2"', 'hand_tools', 'Precision torque wrench', 2800, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2080', 'Room 4', 'Shelf 20', 1, 'normal'),
    ('Needle Nose Pliers 6"', 'hand_tools', 'Long nose pliers', 280, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2081', 'Room 5', 'Shelf 1', 1, 'normal'),
    ('Diagonal Cutting Pliers', 'hand_tools', 'Wire cutting pliers', 350, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2082', 'Room 5', 'Shelf 2', 1, 'normal'),
    ('Locking Pliers 10"', 'hand_tools', 'Vice grip locking pliers', 450, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2083', 'Room 5', 'Shelf 3', 1, 'normal'),
    ('Lineman\'s Pliers 9"', 'hand_tools', 'Heavy-duty lineman pliers', 550, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2084', 'Room 5', 'Shelf 4', 1, 'normal'),
    ('Wire Strippers', 'hand_tools', 'Automatic wire stripping tool', 380, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH2085', 'Room 5', 'Shelf 5', 1, 'normal'),
]

# Insert new products
print("\n1. Adding 85+ new construction products...")
products_created = 0
for product_data in new_products:
    try:
        cursor.execute("""
            INSERT INTO Inventory_product 
            (name, category, description, price, material, size, variation, product_type, 
             supplier_company, batch_number, room, shelf, floor, storing_condition) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, product_data)
        products_created += 1
        if products_created % 10 == 0:
            print(f"  Created {products_created} products...")
    except Exception as e:
        print(f"  Error creating product {product_data[0]}: {e}")

print(f"\nNew products created: {products_created}")

# Create stock entries for new products
cursor.execute("SELECT id, name FROM store_store")
stores = cursor.fetchall()

cursor.execute("SELECT id, name, price FROM Inventory_product WHERE id > 15")  # Only new products
new_products_db = cursor.fetchall()

print("\n2. Creating stock entries for new products...")
stocks_created = 0

for store_id, store_name in stores:
    for product_id, product_name, product_price in new_products_db:
        # 80% chance of having this product in this store
        if random.choice([True, True, True, True, False]):
            try:
                # Calculate selling price (cost + markup)
                markup_percentage = random.uniform(0.20, 0.70)  # 20-70% markup
                selling_price = float(product_price) * (1 + markup_percentage)
                
                # Random stock quantity
                quantity = random.randint(5, 150)
                low_stock_threshold = random.randint(5, 20)
                
                cursor.execute("""
                    INSERT INTO Inventory_stock 
                    (product_id, store_id, quantity, low_stock_threshold, selling_price, last_updated) 
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (product_id, store_id, quantity, low_stock_threshold, round(selling_price, 2)))
                
                stocks_created += 1
                    
            except Exception as e:
                print(f"  Error creating stock for {product_name} at {store_name}: {e}")

print(f"Stock entries created: {stocks_created}")

# Commit changes
conn.commit()

# Get final counts
cursor.execute("SELECT COUNT(*) FROM store_store")
total_stores = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Inventory_product")
total_products = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Inventory_stock")
total_stocks = cursor.fetchone()[0]

print("\n" + "=" * 50)
print("🎉 100+ CONSTRUCTION PRODUCTS ADDED! 🎉")
print("=" * 50)
print(f"Total stores: {total_stores}")
print(f"Total products: {total_products}")
print(f"Total stock entries: {total_stocks}")
print("=" * 50)

# Close connection
conn.close()

print(f"\n🏗️ SUCCESS! You now have {total_products} construction products!")
print("🌐 Browse them at: http://127.0.0.1:8000/webfront/")
print("📱 Categories include:")
print("   • Construction Materials (Cement, Steel, Aggregates)")
print("   • Building Materials (Bricks, Blocks, Roofing)")
print("   • Construction Tools (Power Tools, Hand Tools)")
print("   • Plumbing & Electrical Supplies")
print("   • Hardware & Fasteners")
print("   • Safety Equipment")
print("   • Paints & Finishes")
print("   • Doors & Windows")
print("   • Flooring & Tiles")
