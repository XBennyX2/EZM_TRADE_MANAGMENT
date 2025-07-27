#!/usr/bin/env python3
"""
Add more construction products to reach 100+ products
"""

import sqlite3
import random

# Database connection
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("ADDING MORE CONSTRUCTION PRODUCTS")
print("=" * 50)

# Additional construction products to reach 100+
additional_products = [
    # More Construction Materials (10 products)
    ('Crushed Stone 10mm - 1 ton', 'construction_materials', 'Fine crushed stone for concrete', 1400, 'Stone', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1016', 'Room 1', 'Shelf 16', 1, 'normal'),
    ('Crushed Stone 20mm - 1 ton', 'construction_materials', 'Standard crushed stone aggregate', 1600, 'Stone', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1017', 'Room 1', 'Shelf 17', 1, 'normal'),
    ('Lime Powder 25kg', 'construction_materials', 'Hydrated lime for mortar and plaster', 350, 'Lime', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1018', 'Room 1', 'Shelf 18', 1, 'dry'),
    ('Cement Mortar Mix 25kg', 'construction_materials', 'Pre-mixed mortar for masonry work', 450, 'Cement Mortar', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1019', 'Room 1', 'Shelf 19', 1, 'dry'),
    ('Waterproof Cement 50kg', 'construction_materials', 'Water-resistant cement for wet areas', 1200, 'Waterproof Cement', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1020', 'Room 1', 'Shelf 20', 1, 'dry'),
    ('Reinforcement Steel Bars 6mm', 'construction_materials', 'Small steel reinforcement bars', 650, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1021', 'Room 2', 'Shelf 1', 1, 'normal'),
    ('Reinforcement Steel Bars 10mm', 'construction_materials', 'Medium steel reinforcement bars', 950, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1022', 'Room 2', 'Shelf 2', 1, 'normal'),
    ('Reinforcement Steel Bars 20mm', 'construction_materials', 'Heavy steel reinforcement bars', 2200, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1023', 'Room 2', 'Shelf 3', 1, 'normal'),
    ('Welding Wire 2.5mm', 'construction_materials', 'Steel welding wire for construction', 450, 'Steel Wire', 'small', '', 'finished_product', 'Default Supplier', 'BATCH1024', 'Room 2', 'Shelf 4', 1, 'normal'),
    ('Binding Wire 1.6mm', 'construction_materials', 'Steel binding wire for reinforcement', 280, 'Steel Wire', 'small', '', 'finished_product', 'Default Supplier', 'BATCH1025', 'Room 2', 'Shelf 5', 1, 'normal'),

    # More Building Materials (15 products)
    ('Solid Bricks', 'building_materials', 'Heavy-duty solid clay bricks', 12, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2021', 'Room 2', 'Shelf 6', 1, 'normal'),
    ('Engineering Bricks', 'building_materials', 'High-strength engineering bricks', 18, 'Clay', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH2022', 'Room 2', 'Shelf 7', 1, 'normal'),
    ('Perforated Bricks', 'building_materials', 'Lightweight perforated bricks', 10, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2023', 'Room 2', 'Shelf 8', 1, 'normal'),
    ('Concrete Pavers 20x20cm', 'building_materials', 'Small concrete paving blocks', 45, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2024', 'Room 2', 'Shelf 9', 1, 'normal'),
    ('Concrete Pavers 25x25cm', 'building_materials', 'Medium concrete paving blocks', 65, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2025', 'Room 2', 'Shelf 10', 1, 'normal'),
    ('Decorative Blocks', 'building_materials', 'Decorative concrete blocks for walls', 85, 'Concrete', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2026', 'Room 2', 'Shelf 11', 1, 'normal'),
    ('Insulation Blocks', 'building_materials', 'Thermal insulation concrete blocks', 95, 'Insulated Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2027', 'Room 2', 'Shelf 12', 1, 'normal'),
    ('Precast Concrete Panels', 'building_materials', 'Large precast concrete wall panels', 2500, 'Concrete', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2028', 'Room 2', 'Shelf 13', 1, 'normal'),
    ('Concrete Lintels', 'building_materials', 'Reinforced concrete lintels', 450, 'Reinforced Concrete', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2029', 'Room 2', 'Shelf 14', 1, 'normal'),
    ('Concrete Posts', 'building_materials', 'Precast concrete fence posts', 350, 'Concrete', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2030', 'Room 2', 'Shelf 15', 1, 'normal'),
    ('Roofing Felt 10m', 'building_materials', 'Waterproof roofing felt', 850, 'Bitumen Felt', 'large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2031', 'Room 2', 'Shelf 16', 1, 'normal'),
    ('Roofing Membrane', 'building_materials', 'EPDM roofing membrane', 1200, 'EPDM Rubber', 'large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2032', 'Room 2', 'Shelf 17', 1, 'normal'),
    ('Flashing Strips', 'building_materials', 'Lead flashing for roof joints', 650, 'Lead', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2033', 'Room 2', 'Shelf 18', 1, 'normal'),
    ('Roof Vents', 'building_materials', 'Plastic roof ventilation units', 280, 'Plastic', 'small', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH2034', 'Room 2', 'Shelf 19', 1, 'normal'),
    ('Soffit Boards', 'building_materials', 'PVC soffit boards for eaves', 450, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2035', 'Room 2', 'Shelf 20', 1, 'normal'),

    # Power Tools (15 products)
    ('Cordless Screwdriver', 'construction_tools', 'Lightweight cordless screwdriver', 1800, 'Plastic and Metal', 'small', 'Color: Green', 'finished_product', 'Default Supplier', 'BATCH3026', 'Room 3', 'Shelf 1', 1, 'normal'),
    ('Rotary Hammer 26mm', 'construction_tools', 'SDS rotary hammer drill', 6500, 'Metal', 'medium', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH3027', 'Room 3', 'Shelf 2', 1, 'normal'),
    ('Demolition Hammer', 'construction_tools', 'Heavy-duty demolition hammer', 8500, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3028', 'Room 3', 'Shelf 3', 1, 'normal'),
    ('Orbital Sander', 'construction_tools', 'Electric orbital sander', 2200, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3029', 'Room 3', 'Shelf 4', 1, 'normal'),
    ('Belt Sander', 'construction_tools', 'Heavy-duty belt sander', 3500, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3030', 'Room 3', 'Shelf 5', 1, 'normal'),
    ('Router Electric', 'construction_tools', 'Wood router for edge work', 4200, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3031', 'Room 3', 'Shelf 6', 1, 'normal'),
    ('Planer Electric', 'construction_tools', 'Electric wood planer', 3800, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3032', 'Room 3', 'Shelf 7', 1, 'normal'),
    ('Biscuit Joiner', 'construction_tools', 'Wood biscuit joining tool', 2800, 'Metal and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3033', 'Room 3', 'Shelf 8', 1, 'normal'),
    ('Nail Gun Electric', 'construction_tools', 'Electric nail gun for framing', 4500, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3034', 'Room 3', 'Shelf 9', 1, 'normal'),
    ('Staple Gun Heavy Duty', 'construction_tools', 'Heavy-duty staple gun', 850, 'Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3035', 'Room 3', 'Shelf 10', 1, 'normal'),
    ('Heat Gun 2000W', 'construction_tools', 'Electric heat gun for paint removal', 1800, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3036', 'Room 3', 'Shelf 11', 1, 'normal'),
    ('Soldering Iron 60W', 'construction_tools', 'Electric soldering iron', 450, 'Metal and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3037', 'Room 3', 'Shelf 12', 1, 'normal'),
    ('Multi-tool Oscillating', 'construction_tools', 'Oscillating multi-tool', 3200, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3038', 'Room 3', 'Shelf 13', 1, 'normal'),
    ('Chainsaw Electric', 'construction_tools', 'Electric chainsaw for cutting', 5500, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3039', 'Room 3', 'Shelf 14', 1, 'normal'),
    ('Leaf Blower', 'construction_tools', 'Electric leaf blower for cleanup', 2800, 'Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3040', 'Room 3', 'Shelf 15', 1, 'normal'),

    # Hand Tools (20 products)
    ('Tool Box Large', 'hand_tools', 'Large metal tool storage box', 1200, 'Metal', 'large', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH4016', 'Room 4', 'Shelf 1', 1, 'normal'),
    ('Tool Belt Leather', 'hand_tools', 'Professional leather tool belt', 850, 'Leather', 'medium', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH4017', 'Room 4', 'Shelf 2', 1, 'normal'),
    ('Crowbar 24"', 'hand_tools', 'Heavy-duty steel crowbar', 650, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4018', 'Room 4', 'Shelf 3', 1, 'normal'),
    ('Pry Bar Set', 'hand_tools', 'Set of different sized pry bars', 850, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4019', 'Room 4', 'Shelf 4', 1, 'normal'),
    ('Wire Cutters', 'hand_tools', 'Heavy-duty wire cutting pliers', 450, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4020', 'Room 4', 'Shelf 5', 1, 'normal'),
    ('Bolt Cutters 24"', 'hand_tools', 'Heavy-duty bolt cutters', 1200, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4021', 'Room 4', 'Shelf 6', 1, 'normal'),
    ('Tin Snips', 'hand_tools', 'Metal cutting tin snips', 380, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4022', 'Room 4', 'Shelf 7', 1, 'normal'),
    ('Files Set', 'hand_tools', 'Complete metal files set', 650, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4023', 'Room 4', 'Shelf 8', 1, 'normal'),
    ('Sandpaper Blocks', 'hand_tools', 'Sanding blocks with sandpaper', 280, 'Wood and Abrasive', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4024', 'Room 4', 'Shelf 9', 1, 'normal'),
    ('Steel Wool Pack', 'hand_tools', 'Steel wool for surface preparation', 120, 'Steel Wool', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4025', 'Room 4', 'Shelf 10', 1, 'normal'),
    ('Putty Knife Set', 'hand_tools', 'Flexible putty knives for filling', 320, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4026', 'Room 4', 'Shelf 11', 1, 'normal'),
    ('Trowel Pointing', 'hand_tools', 'Pointing trowel for mortar work', 280, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4027', 'Room 4', 'Shelf 12', 1, 'normal'),
    ('Trowel Brick', 'hand_tools', 'Brick laying trowel', 450, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4028', 'Room 4', 'Shelf 13', 1, 'normal'),
    ('Float Wooden', 'hand_tools', 'Wooden float for concrete finishing', 320, 'Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4029', 'Room 4', 'Shelf 14', 1, 'normal'),
    ('Float Plastic', 'hand_tools', 'Plastic float for smooth finishing', 180, 'Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4030', 'Room 4', 'Shelf 15', 1, 'normal'),
    ('Jointing Tool', 'hand_tools', 'Mortar jointing tool', 220, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4031', 'Room 4', 'Shelf 16', 1, 'normal'),
    ('Line Blocks', 'hand_tools', 'Corner blocks for string lines', 150, 'Plastic', 'small', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH4032', 'Room 4', 'Shelf 17', 1, 'normal'),
    ('Builder\'s Line 100m', 'hand_tools', 'Strong nylon builder\'s line', 180, 'Nylon', 'small', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH4033', 'Room 4', 'Shelf 18', 1, 'normal'),
    ('Chalk Line Reel', 'hand_tools', 'Chalk line marking tool', 350, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4034', 'Room 4', 'Shelf 19', 1, 'normal'),
    ('Marking Chalk Blue', 'hand_tools', 'Blue marking chalk powder', 85, 'Chalk', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH4035', 'Room 4', 'Shelf 20', 1, 'normal'),

    # Electrical Supplies (15 products)
    ('LED Light Bulbs 9W', 'plumbing_electrical', 'Energy efficient LED bulbs 9W', 150, 'Plastic and LED', 'small', 'Color: Warm White', 'finished_product', 'Default Supplier', 'BATCH5021', 'Room 5', 'Shelf 1', 1, 'normal'),
    ('LED Light Bulbs 12W', 'plumbing_electrical', 'Energy efficient LED bulbs 12W', 180, 'Plastic and LED', 'small', 'Color: Cool White', 'finished_product', 'Default Supplier', 'BATCH5022', 'Room 5', 'Shelf 2', 1, 'normal'),
    ('LED Light Bulbs 18W', 'plumbing_electrical', 'High power LED bulbs 18W', 250, 'Plastic and LED', 'small', 'Color: Daylight', 'finished_product', 'Default Supplier', 'BATCH5023', 'Room 5', 'Shelf 3', 1, 'normal'),
    ('Fluorescent Tubes 18W', 'plumbing_electrical', 'Standard fluorescent tubes', 120, 'Glass and Phosphor', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5024', 'Room 5', 'Shelf 4', 1, 'normal'),
    ('Fluorescent Tubes 36W', 'plumbing_electrical', 'Long fluorescent tubes', 180, 'Glass and Phosphor', 'large', '', 'finished_product', 'Default Supplier', 'BATCH5025', 'Room 5', 'Shelf 5', 1, 'normal'),
    ('Wall Switches Single', 'plumbing_electrical', 'Single gang wall switches', 85, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5026', 'Room 5', 'Shelf 6', 1, 'normal'),
    ('Wall Switches Double', 'plumbing_electrical', 'Double gang wall switches', 120, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5027', 'Room 5', 'Shelf 7', 1, 'normal'),
    ('Power Sockets Single', 'plumbing_electrical', 'Single power sockets', 95, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5028', 'Room 5', 'Shelf 8', 1, 'normal'),
    ('Power Sockets Double', 'plumbing_electrical', 'Double power sockets', 150, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5029', 'Room 5', 'Shelf 9', 1, 'normal'),
    ('Extension Cords 10m', 'plumbing_electrical', 'Heavy duty extension cords', 450, 'Rubber and Copper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5030', 'Room 5', 'Shelf 10', 1, 'normal'),
    ('Conduit Pipes 16mm', 'plumbing_electrical', 'Small electrical conduit pipes', 18, 'PVC', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH5031', 'Room 5', 'Shelf 11', 1, 'normal'),
    ('Conduit Pipes 20mm', 'plumbing_electrical', 'Standard electrical conduit pipes', 25, 'PVC', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH5032', 'Room 5', 'Shelf 12', 1, 'normal'),
    ('Conduit Pipes 25mm', 'plumbing_electrical', 'Large electrical conduit pipes', 35, 'PVC', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH5033', 'Room 5', 'Shelf 13', 1, 'normal'),
    ('Junction Boxes Small', 'plumbing_electrical', 'Small electrical junction boxes', 65, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5034', 'Room 5', 'Shelf 14', 1, 'normal'),
    ('Junction Boxes Large', 'plumbing_electrical', 'Large electrical junction boxes', 120, 'Plastic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5035', 'Room 5', 'Shelf 15', 1, 'normal'),
]

# Insert additional products
print("\n3. Adding more construction products...")
products_created = 0
for product_data in additional_products:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO Inventory_product 
            (name, category, description, price, material, size, variation, product_type, 
             supplier_company, batch_number, room, shelf, floor, storing_condition) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, product_data)
        if cursor.rowcount > 0:
            products_created += 1
            print(f"  - {product_data[0]}")
    except Exception as e:
        print(f"  Error creating product {product_data[0]}: {e}")

print(f"\nNew products created: {products_created}")

# Create additional stock entries for new products
cursor.execute("SELECT id, name FROM store_store")
stores = cursor.fetchall()

cursor.execute("SELECT id, name, price FROM Inventory_product WHERE id > 15")  # Only new products
new_products = cursor.fetchall()

print("\n4. Creating stock entries for new products...")
stocks_created = 0

for store_id, store_name in stores:
    for product_id, product_name, product_price in new_products:
        # 85% chance of having this product in this store
        if random.choice([True, True, True, True, True, True, True, True, False]):
            try:
                # Calculate selling price (cost + markup)
                markup_percentage = random.uniform(0.25, 0.65)  # 25-65% markup
                selling_price = float(product_price) * (1 + markup_percentage)
                
                # Random stock quantity
                quantity = random.randint(10, 200)
                low_stock_threshold = random.randint(5, 25)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO Inventory_stock 
                    (product_id, store_id, quantity, low_stock_threshold, selling_price, last_updated) 
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (product_id, store_id, quantity, low_stock_threshold, round(selling_price, 2)))
                
                if cursor.rowcount > 0:
                    stocks_created += 1
                    
            except Exception as e:
                print(f"  Error creating stock for {product_name} at {store_name}: {e}")

print(f"New stock entries created: {stocks_created}")

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
print("ADDITIONAL PRODUCTS ADDED SUCCESSFULLY!")
print("=" * 50)
print(f"Total stores: {total_stores}")
print(f"Total products: {total_products}")
print(f"Total stock entries: {total_stocks}")
print("=" * 50)

# Close connection
conn.close()

print(f"\nNow you have {total_products} construction products!")
print("Browse them at: http://127.0.0.1:8000/webfront/")
