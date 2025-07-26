#!/usr/bin/env python3
"""
Simple script to populate construction products and stocks
Run this with: python simple_populate.py
"""

import sqlite3
import random
from decimal import Decimal

# Database connection
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("EZM TRADE - CONSTRUCTION PRODUCTS POPULATION")
print("=" * 50)

# Sample stores data
stores_data = [
    ('Main Branch', 'Bole, Addis Ababa', '+251911111111'),
    ('Piazza Branch', 'Piazza, Addis Ababa', '+251911111112'),
    ('Merkato Branch', 'Merkato, Addis Ababa', '+251911111113'),
    ('CMC Branch', 'CMC, Addis Ababa', '+251911111114'),
    ('Kazanchis Branch', 'Kazanchis, Addis Ababa', '+251911111115'),
]

# Insert stores
print("\n1. Creating stores...")
for store_data in stores_data:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO store_store (name, address, phone_number) 
            VALUES (?, ?, ?)
        """, store_data)
        print(f"  - {store_data[0]}")
    except Exception as e:
        print(f"  Error creating store {store_data[0]}: {e}")

# Insert supplier
print("\n2. Creating supplier...")
try:
    cursor.execute("""
        INSERT OR IGNORE INTO Inventory_supplier (name, contact_person, email, phone, address) 
        VALUES (?, ?, ?, ?, ?)
    """, ('Default Supplier', 'Supply Manager', 'supplier@example.com', '+251911000000', 'Addis Ababa, Ethiopia'))
    print("  - Default Supplier created")
except Exception as e:
    print(f"  Error creating supplier: {e}")

# Construction products data - Comprehensive catalog (100+ products)
products_data = [
    # Construction Materials - Cement & Concrete (15 products)
    ('Portland Cement 50kg', 'construction_materials', 'High-quality Portland cement for construction', 850, 'Cement', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1001', 'Room 1', 'Shelf 1', 1, 'dry'),
    ('White Cement 25kg', 'construction_materials', 'Premium white cement for decorative work', 1200, 'White Cement', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH1002', 'Room 1', 'Shelf 2', 1, 'dry'),
    ('Ready Mix Concrete m³', 'construction_materials', 'Pre-mixed concrete for construction projects', 2500, 'Concrete', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1003', 'Room 1', 'Shelf 3', 1, 'normal'),
    ('High Strength Concrete m³', 'construction_materials', 'High-grade concrete for heavy construction', 3200, 'High Grade Concrete', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1004', 'Room 1', 'Shelf 4', 1, 'normal'),
    ('Concrete Blocks 20x20x40cm', 'construction_materials', 'Standard concrete blocks for building', 25, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1005', 'Room 1', 'Shelf 5', 1, 'normal'),
    ('Lightweight Concrete Blocks', 'construction_materials', 'Lightweight blocks for partition walls', 35, 'Lightweight Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1006', 'Room 1', 'Shelf 6', 1, 'normal'),
    ('Reinforcement Steel Bars 8mm', 'construction_materials', 'Steel reinforcement bars 8mm diameter', 850, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1007', 'Room 1', 'Shelf 7', 1, 'normal'),
    ('Reinforcement Steel Bars 12mm', 'construction_materials', 'Steel reinforcement bars 12mm diameter', 1200, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1008', 'Room 1', 'Shelf 8', 1, 'normal'),
    ('Reinforcement Steel Bars 16mm', 'construction_materials', 'Steel reinforcement bars 16mm diameter', 1800, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH1009', 'Room 1', 'Shelf 9', 1, 'normal'),
    ('Wire Mesh 4mm', 'construction_materials', 'Fine steel wire mesh for reinforcement', 650, 'Steel Wire', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1010', 'Room 1', 'Shelf 10', 1, 'normal'),
    ('Wire Mesh 6mm', 'construction_materials', 'Standard steel wire mesh for reinforcement', 850, 'Steel Wire', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1011', 'Room 1', 'Shelf 11', 1, 'normal'),
    ('Wire Mesh 8mm', 'construction_materials', 'Heavy-duty steel wire mesh', 1200, 'Steel Wire', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH1012', 'Room 1', 'Shelf 12', 1, 'normal'),
    ('Gravel 10mm - 1 ton', 'construction_materials', 'Fine gravel aggregate for concrete', 1500, 'Stone Aggregate', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1013', 'Room 1', 'Shelf 13', 1, 'normal'),
    ('Gravel 20mm - 1 ton', 'construction_materials', 'Standard gravel aggregate for construction', 1800, 'Stone Aggregate', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1014', 'Room 1', 'Shelf 14', 1, 'normal'),
    ('Sand - Fine Grade 1 ton', 'construction_materials', 'Fine sand for construction and plastering', 1200, 'Sand', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH1015', 'Room 1', 'Shelf 15', 1, 'normal'),

    # Building Materials - Bricks, Blocks & Roofing (20 products)
    ('Red Clay Bricks', 'building_materials', 'Traditional red clay bricks for construction', 8, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2001', 'Room 2', 'Shelf 1', 1, 'normal'),
    ('Fire Bricks', 'building_materials', 'Heat-resistant fire bricks for furnaces', 45, 'Fire Clay', 'small', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH2002', 'Room 2', 'Shelf 2', 1, 'normal'),
    ('Interlocking Bricks', 'building_materials', 'Self-locking clay bricks', 12, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2003', 'Room 2', 'Shelf 3', 1, 'normal'),
    ('Hollow Blocks 10x20x40cm', 'building_materials', 'Small hollow concrete blocks', 28, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2004', 'Room 2', 'Shelf 4', 1, 'normal'),
    ('Hollow Blocks 15x20x40cm', 'building_materials', 'Standard hollow concrete blocks', 35, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2005', 'Room 2', 'Shelf 5', 1, 'normal'),
    ('Hollow Blocks 20x20x40cm', 'building_materials', 'Large hollow concrete blocks', 45, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2006', 'Room 2', 'Shelf 6', 1, 'normal'),
    ('Solid Concrete Blocks', 'building_materials', 'Heavy-duty solid concrete blocks', 55, 'Concrete', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH2007', 'Room 2', 'Shelf 7', 1, 'normal'),
    ('Paving Stones 30x30cm', 'building_materials', 'Decorative concrete paving stones', 85, 'Concrete', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2008', 'Room 2', 'Shelf 8', 1, 'normal'),
    ('Paving Stones 40x40cm', 'building_materials', 'Large decorative paving stones', 120, 'Concrete', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2009', 'Room 2', 'Shelf 9', 1, 'normal'),
    ('Kerb Stones', 'building_materials', 'Concrete kerb stones for roads', 180, 'Concrete', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2010', 'Room 2', 'Shelf 10', 1, 'normal'),
    ('Corrugated Iron Sheets 2m', 'building_materials', 'Short galvanized iron roofing sheets', 850, 'Galvanized Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2011', 'Room 2', 'Shelf 11', 1, 'normal'),
    ('Corrugated Iron Sheets 3m', 'building_materials', 'Standard galvanized iron roofing sheets', 1200, 'Galvanized Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2012', 'Room 2', 'Shelf 12', 1, 'normal'),
    ('Corrugated Iron Sheets 4m', 'building_materials', 'Long galvanized iron roofing sheets', 1600, 'Galvanized Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH2013', 'Room 2', 'Shelf 13', 1, 'normal'),
    ('Aluminum Roofing Sheets 3m', 'building_materials', 'Lightweight aluminum roofing sheets', 1800, 'Aluminum', 'large', '', 'finished_product', 'Default Supplier', 'BATCH2014', 'Room 2', 'Shelf 14', 1, 'normal'),
    ('Roof Tiles - Clay Red', 'building_materials', 'Traditional red clay roof tiles', 25, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2015', 'Room 2', 'Shelf 15', 1, 'normal'),
    ('Roof Tiles - Clay Brown', 'building_materials', 'Brown clay roof tiles', 28, 'Clay', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH2016', 'Room 2', 'Shelf 16', 1, 'normal'),
    ('Concrete Roof Tiles', 'building_materials', 'Durable concrete roof tiles', 35, 'Concrete', 'small', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH2017', 'Room 2', 'Shelf 17', 1, 'normal'),
    ('Ridge Tiles', 'building_materials', 'Roof ridge tiles for finishing', 45, 'Clay', 'small', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH2018', 'Room 2', 'Shelf 18', 1, 'normal'),
    ('Gutters PVC 4m', 'building_materials', 'PVC rain gutters for roofing', 350, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2019', 'Room 2', 'Shelf 19', 1, 'normal'),
    ('Downpipes PVC 3m', 'building_materials', 'PVC downpipes for drainage', 280, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH2020', 'Room 2', 'Shelf 20', 1, 'normal'),

    # Construction Tools & Equipment (25 products)
    ('Electric Drill 12V', 'construction_tools', 'Compact cordless drill for light work', 2500, 'Metal and Plastic', 'small', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH3001', 'Room 3', 'Shelf 1', 1, 'normal'),
    ('Electric Drill 18V', 'construction_tools', 'Professional cordless drill with battery', 3500, 'Metal and Plastic', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH3002', 'Room 3', 'Shelf 2', 1, 'normal'),
    ('Hammer Drill 24V', 'construction_tools', 'Heavy-duty hammer drill for concrete', 5500, 'Metal', 'medium', 'Color: Red', 'finished_product', 'Default Supplier', 'BATCH3003', 'Room 3', 'Shelf 3', 1, 'normal'),
    ('Impact Driver 18V', 'construction_tools', 'High-torque impact driver', 4200, 'Metal and Plastic', 'small', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH3004', 'Room 3', 'Shelf 4', 1, 'normal'),
    ('Angle Grinder 4.5"', 'construction_tools', 'Small angle grinder for precision work', 1800, 'Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3005', 'Room 3', 'Shelf 5', 1, 'normal'),
    ('Angle Grinder 7"', 'construction_tools', 'Medium angle grinder for general use', 2400, 'Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3006', 'Room 3', 'Shelf 6', 1, 'normal'),
    ('Angle Grinder 9"', 'construction_tools', 'Heavy-duty angle grinder for cutting', 2800, 'Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3007', 'Room 3', 'Shelf 7', 1, 'normal'),
    ('Circular Saw 7.25"', 'construction_tools', 'Electric circular saw for wood cutting', 4200, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3008', 'Room 3', 'Shelf 8', 1, 'normal'),
    ('Jigsaw Electric', 'construction_tools', 'Electric jigsaw for curved cuts', 2800, 'Metal and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH3009', 'Room 3', 'Shelf 9', 1, 'normal'),
    ('Reciprocating Saw', 'construction_tools', 'Powerful reciprocating saw', 3800, 'Metal and Plastic', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3010', 'Room 3', 'Shelf 10', 1, 'normal'),
    ('Welding Machine 160A', 'construction_tools', 'Compact arc welding machine', 12000, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3011', 'Room 3', 'Shelf 11', 1, 'normal'),
    ('Welding Machine 200A', 'construction_tools', 'Professional arc welding machine', 15000, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3012', 'Room 3', 'Shelf 12', 1, 'normal'),
    ('MIG Welder 180A', 'construction_tools', 'MIG welding machine for steel', 18000, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3013', 'Room 3', 'Shelf 13', 1, 'normal'),
    ('Concrete Mixer 100L', 'construction_tools', 'Small electric concrete mixer', 8500, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3014', 'Room 3', 'Shelf 14', 1, 'normal'),
    ('Concrete Mixer 150L', 'construction_tools', 'Standard electric concrete mixer', 12000, 'Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH3015', 'Room 3', 'Shelf 15', 1, 'normal'),
    ('Concrete Mixer 200L', 'construction_tools', 'Large concrete mixer for big jobs', 16000, 'Steel', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH3016', 'Room 3', 'Shelf 16', 1, 'normal'),
    ('Tile Cutter 600mm', 'construction_tools', 'Manual tile cutting machine', 2200, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3017', 'Room 3', 'Shelf 17', 1, 'normal'),
    ('Tile Cutter Electric', 'construction_tools', 'Electric tile cutting machine', 4500, 'Steel and Plastic', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3018', 'Room 3', 'Shelf 18', 1, 'normal'),
    ('Compactor Plate', 'construction_tools', 'Vibrating plate compactor', 8500, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3019', 'Room 3', 'Shelf 19', 1, 'normal'),
    ('Jackhammer Electric', 'construction_tools', 'Electric demolition hammer', 6500, 'Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3020', 'Room 3', 'Shelf 20', 1, 'normal'),
    ('Generator 2.5KW', 'construction_tools', 'Portable petrol generator', 15000, 'Metal', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3021', 'Room 4', 'Shelf 1', 1, 'normal'),
    ('Generator 5KW', 'construction_tools', 'Heavy-duty petrol generator', 25000, 'Metal', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH3022', 'Room 4', 'Shelf 2', 1, 'normal'),
    ('Air Compressor 50L', 'construction_tools', 'Electric air compressor', 8500, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH3023', 'Room 4', 'Shelf 3', 1, 'normal'),
    ('Pressure Washer', 'construction_tools', 'High-pressure cleaning machine', 6500, 'Plastic and Metal', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH3024', 'Room 4', 'Shelf 4', 1, 'normal'),
    ('Scaffolding Set', 'construction_tools', 'Aluminum scaffolding system', 12000, 'Aluminum', 'extra_large', '', 'finished_product', 'Default Supplier', 'BATCH3025', 'Room 4', 'Shelf 5', 1, 'normal'),

    # Hand Tools & Measuring (15 products)
    ('Claw Hammer 16oz', 'hand_tools', 'Professional claw hammer with steel handle', 450, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4001', 'Room 4', 'Shelf 6', 1, 'normal'),
    ('Sledge Hammer 3kg', 'hand_tools', 'Heavy-duty sledge hammer', 850, 'Steel and Wood', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4002', 'Room 4', 'Shelf 7', 1, 'normal'),
    ('Screwdriver Set', 'hand_tools', 'Complete screwdriver set with case', 650, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4003', 'Room 4', 'Shelf 8', 1, 'normal'),
    ('Adjustable Wrench 10"', 'hand_tools', 'Professional adjustable wrench', 380, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4004', 'Room 4', 'Shelf 9', 1, 'normal'),
    ('Pipe Wrench 14"', 'hand_tools', 'Heavy-duty pipe wrench', 650, 'Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4005', 'Room 4', 'Shelf 10', 1, 'normal'),
    ('Pliers Set', 'hand_tools', 'Complete pliers set for electrical work', 850, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4006', 'Room 4', 'Shelf 11', 1, 'normal'),
    ('Chisel Set', 'hand_tools', 'Wood and stone chisel set', 550, 'Steel and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4007', 'Room 4', 'Shelf 12', 1, 'normal'),
    ('Hand Saw 22"', 'hand_tools', 'Sharp hand saw for wood cutting', 450, 'Steel and Wood', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4008', 'Room 4', 'Shelf 13', 1, 'normal'),
    ('Hacksaw with Blades', 'hand_tools', 'Metal cutting hacksaw with spare blades', 280, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4009', 'Room 4', 'Shelf 14', 1, 'normal'),
    ('Spirit Level 60cm', 'hand_tools', 'Compact aluminum spirit level', 450, 'Aluminum', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH4010', 'Room 4', 'Shelf 15', 1, 'normal'),
    ('Spirit Level 1.2m', 'hand_tools', 'Professional aluminum spirit level', 850, 'Aluminum', 'large', '', 'finished_product', 'Default Supplier', 'BATCH4011', 'Room 4', 'Shelf 16', 1, 'normal'),
    ('Measuring Tape 3m', 'hand_tools', 'Compact steel measuring tape', 180, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4012', 'Room 4', 'Shelf 17', 1, 'normal'),
    ('Measuring Tape 5m', 'hand_tools', 'Standard steel measuring tape with lock', 280, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4013', 'Room 4', 'Shelf 18', 1, 'normal'),
    ('Measuring Tape 10m', 'hand_tools', 'Long steel measuring tape', 450, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4014', 'Room 4', 'Shelf 19', 1, 'normal'),
    ('Utility Knife Set', 'hand_tools', 'Professional utility knives with blades', 320, 'Steel and Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH4015', 'Room 4', 'Shelf 20', 1, 'normal'),

    # Plumbing & Electrical (20 products)
    ('PVC Pipes 2" x 3m', 'plumbing_electrical', 'Small PVC pipes for drainage', 280, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5001', 'Room 5', 'Shelf 1', 1, 'normal'),
    ('PVC Pipes 4" x 3m', 'plumbing_electrical', 'Standard PVC drainage pipes', 450, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5002', 'Room 5', 'Shelf 2', 1, 'normal'),
    ('PVC Pipes 6" x 3m', 'plumbing_electrical', 'Large PVC drainage pipes', 650, 'PVC', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5003', 'Room 5', 'Shelf 3', 1, 'normal'),
    ('Copper Pipes 1/2" x 3m', 'plumbing_electrical', 'Small copper pipes for water supply', 650, 'Copper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5004', 'Room 5', 'Shelf 4', 1, 'normal'),
    ('Copper Pipes 3/4" x 3m', 'plumbing_electrical', 'Standard copper pipes for water supply', 850, 'Copper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5005', 'Room 5', 'Shelf 5', 1, 'normal'),
    ('Copper Pipes 1" x 3m', 'plumbing_electrical', 'Large copper pipes for main supply', 1200, 'Copper', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5006', 'Room 5', 'Shelf 6', 1, 'normal'),
    ('PVC Fittings Set', 'plumbing_electrical', 'Complete set of PVC pipe fittings', 650, 'PVC', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH5007', 'Room 5', 'Shelf 7', 1, 'normal'),
    ('Copper Fittings Set', 'plumbing_electrical', 'Complete set of copper pipe fittings', 1200, 'Copper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5008', 'Room 5', 'Shelf 8', 1, 'normal'),
    ('Water Pump 0.5HP', 'plumbing_electrical', 'Small centrifugal water pump', 5500, 'Cast Iron', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5009', 'Room 5', 'Shelf 9', 1, 'normal'),
    ('Water Pump 1HP', 'plumbing_electrical', 'Standard centrifugal water pump', 8500, 'Cast Iron', 'large', '', 'finished_product', 'Default Supplier', 'BATCH5010', 'Room 5', 'Shelf 10', 1, 'normal'),
    ('Water Pump 2HP', 'plumbing_electrical', 'Heavy-duty centrifugal water pump', 12000, 'Cast Iron', 'large', '', 'finished_product', 'Default Supplier', 'BATCH5011', 'Room 5', 'Shelf 11', 1, 'normal'),
    ('Submersible Pump 1HP', 'plumbing_electrical', 'Submersible water pump for wells', 15000, 'Stainless Steel', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH5012', 'Room 5', 'Shelf 12', 1, 'normal'),
    ('Water Tank 500L', 'plumbing_electrical', 'Plastic water storage tank', 3500, 'Polyethylene', 'extra_large', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH5013', 'Room 5', 'Shelf 13', 1, 'normal'),
    ('Water Tank 1000L', 'plumbing_electrical', 'Large plastic water storage tank', 6500, 'Polyethylene', 'extra_large', 'Color: Blue', 'finished_product', 'Default Supplier', 'BATCH5014', 'Room 5', 'Shelf 14', 1, 'normal'),
    ('Electrical Cable 1.5mm²', 'plumbing_electrical', 'Light duty copper electrical cable', 28, 'Copper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5015', 'Room 5', 'Shelf 15', 1, 'normal'),
    ('Electrical Cable 2.5mm²', 'plumbing_electrical', 'Standard copper electrical cable', 45, 'Copper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5016', 'Room 5', 'Shelf 16', 1, 'normal'),
    ('Electrical Cable 4mm²', 'plumbing_electrical', 'Heavy duty copper electrical cable', 65, 'Copper', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5017', 'Room 5', 'Shelf 17', 1, 'normal'),
    ('Circuit Breaker 16A', 'plumbing_electrical', 'Single pole circuit breaker 16A', 280, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5018', 'Room 5', 'Shelf 18', 1, 'normal'),
    ('Circuit Breaker 20A', 'plumbing_electrical', 'Single pole circuit breaker 20A', 350, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5019', 'Room 5', 'Shelf 19', 1, 'normal'),
    ('Circuit Breaker 32A', 'plumbing_electrical', 'Single pole circuit breaker 32A', 450, 'Plastic and Metal', 'small', '', 'finished_product', 'Default Supplier', 'BATCH5020', 'Room 5', 'Shelf 20', 1, 'normal'),

    # Hardware & Fasteners (15 products)
    ('Steel Nails 2" - 1kg', 'hardware_fasteners', 'Small steel nails for light work', 120, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6001', 'Room 1', 'Shelf 16', 1, 'normal'),
    ('Steel Nails 3" - 1kg', 'hardware_fasteners', 'Medium steel nails for general use', 150, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6002', 'Room 1', 'Shelf 17', 1, 'normal'),
    ('Steel Nails 4" - 1kg', 'hardware_fasteners', 'Large steel nails for heavy construction', 180, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6003', 'Room 1', 'Shelf 18', 1, 'normal'),
    ('Roofing Nails - 1kg', 'hardware_fasteners', 'Galvanized roofing nails', 220, 'Galvanized Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6004', 'Room 1', 'Shelf 19', 1, 'normal'),
    ('Wood Screws 1" - 100pcs', 'hardware_fasteners', 'Small self-tapping wood screws', 150, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6005', 'Room 1', 'Shelf 20', 1, 'normal'),
    ('Wood Screws 2" - 100pcs', 'hardware_fasteners', 'Medium self-tapping wood screws', 200, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6006', 'Room 2', 'Shelf 21', 1, 'normal'),
    ('Wood Screws 3" - 100pcs', 'hardware_fasteners', 'Large self-tapping wood screws', 250, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6007', 'Room 2', 'Shelf 22', 1, 'normal'),
    ('Machine Bolts M8 - 10pcs', 'hardware_fasteners', 'Standard machine bolts M8', 180, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6008', 'Room 2', 'Shelf 23', 1, 'normal'),
    ('Machine Bolts M10 - 10pcs', 'hardware_fasteners', 'Standard machine bolts M10', 220, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6009', 'Room 2', 'Shelf 24', 1, 'normal'),
    ('Anchor Bolts M10 - 10pcs', 'hardware_fasteners', 'Medium anchor bolts for concrete', 350, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6010', 'Room 2', 'Shelf 25', 1, 'normal'),
    ('Anchor Bolts M12 - 10pcs', 'hardware_fasteners', 'Heavy-duty anchor bolts for concrete', 450, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6011', 'Room 3', 'Shelf 21', 1, 'normal'),
    ('Hinges Light Duty - Pair', 'hardware_fasteners', 'Light door hinges for interior doors', 180, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6012', 'Room 3', 'Shelf 22', 1, 'normal'),
    ('Hinges Heavy Duty - Pair', 'hardware_fasteners', 'Heavy door hinges for exterior doors', 350, 'Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6013', 'Room 3', 'Shelf 23', 1, 'normal'),
    ('Padlocks 40mm', 'hardware_fasteners', 'Medium security padlocks', 220, 'Steel and Brass', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6014', 'Room 3', 'Shelf 24', 1, 'normal'),
    ('Padlocks 50mm', 'hardware_fasteners', 'Heavy security padlocks', 280, 'Steel and Brass', 'small', '', 'finished_product', 'Default Supplier', 'BATCH6015', 'Room 3', 'Shelf 25', 1, 'normal'),

    # Safety Equipment (10 products)
    ('Safety Helmet Yellow', 'safety_equipment', 'Construction safety helmet', 350, 'Plastic', 'medium', 'Color: Yellow', 'finished_product', 'Default Supplier', 'BATCH7001', 'Room 4', 'Shelf 21', 1, 'normal'),
    ('Safety Helmet White', 'safety_equipment', 'Construction safety helmet', 350, 'Plastic', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH7002', 'Room 4', 'Shelf 22', 1, 'normal'),
    ('Safety Goggles', 'safety_equipment', 'Protective safety goggles', 180, 'Plastic', 'small', '', 'finished_product', 'Default Supplier', 'BATCH7003', 'Room 4', 'Shelf 23', 1, 'normal'),
    ('Work Gloves Leather', 'safety_equipment', 'Heavy-duty leather work gloves', 280, 'Leather', 'small', '', 'finished_product', 'Default Supplier', 'BATCH7004', 'Room 4', 'Shelf 24', 1, 'normal'),
    ('Work Gloves Rubber', 'safety_equipment', 'Waterproof rubber work gloves', 220, 'Rubber', 'small', '', 'finished_product', 'Default Supplier', 'BATCH7005', 'Room 4', 'Shelf 25', 1, 'normal'),
    ('Safety Boots Size 42', 'safety_equipment', 'Steel toe safety boots', 1200, 'Leather and Steel', 'medium', 'Size: 42', 'finished_product', 'Default Supplier', 'BATCH7006', 'Room 5', 'Shelf 21', 1, 'normal'),
    ('Safety Boots Size 44', 'safety_equipment', 'Steel toe safety boots', 1200, 'Leather and Steel', 'medium', 'Size: 44', 'finished_product', 'Default Supplier', 'BATCH7007', 'Room 5', 'Shelf 22', 1, 'normal'),
    ('High Visibility Vest', 'safety_equipment', 'Reflective safety vest', 450, 'Polyester', 'medium', 'Color: Orange', 'finished_product', 'Default Supplier', 'BATCH7008', 'Room 5', 'Shelf 23', 1, 'normal'),
    ('Dust Masks - 10pcs', 'safety_equipment', 'Disposable dust masks', 120, 'Non-woven Fabric', 'small', '', 'finished_product', 'Default Supplier', 'BATCH7009', 'Room 5', 'Shelf 24', 1, 'normal'),
    ('First Aid Kit', 'safety_equipment', 'Complete construction site first aid kit', 850, 'Plastic Case', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH7010', 'Room 5', 'Shelf 25', 1, 'normal'),

    # Paints & Finishes (10 products)
    ('Exterior Wall Paint 5L', 'paints_finishes', 'Small weather-resistant exterior paint', 850, 'Acrylic Paint', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH8001', 'Room 2', 'Shelf 26', 2, 'normal'),
    ('Exterior Wall Paint 20L', 'paints_finishes', 'Large weather-resistant exterior paint', 2800, 'Acrylic Paint', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH8002', 'Room 2', 'Shelf 27', 2, 'normal'),
    ('Interior Emulsion Paint 5L', 'paints_finishes', 'Small smooth finish interior paint', 650, 'Emulsion Paint', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH8003', 'Room 2', 'Shelf 28', 2, 'normal'),
    ('Interior Emulsion Paint 20L', 'paints_finishes', 'Large smooth finish interior paint', 2200, 'Emulsion Paint', 'large', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH8004', 'Room 2', 'Shelf 29', 2, 'normal'),
    ('Primer Sealer 1L', 'paints_finishes', 'Small wall primer and sealer', 220, 'Primer', 'small', '', 'finished_product', 'Default Supplier', 'BATCH8005', 'Room 2', 'Shelf 30', 2, 'normal'),
    ('Primer Sealer 5L', 'paints_finishes', 'Standard wall primer and sealer', 850, 'Primer', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH8006', 'Room 3', 'Shelf 26', 2, 'normal'),
    ('Wood Stain 500ml', 'paints_finishes', 'Small protective wood stain', 380, 'Wood Stain', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH8007', 'Room 3', 'Shelf 27', 2, 'normal'),
    ('Wood Stain 1L', 'paints_finishes', 'Standard protective wood stain', 650, 'Wood Stain', 'small', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH8008', 'Room 3', 'Shelf 28', 2, 'normal'),
    ('Paint Brushes Set', 'paints_finishes', 'Professional painting brushes', 450, 'Bristle and Wood', 'small', '', 'finished_product', 'Default Supplier', 'BATCH8009', 'Room 3', 'Shelf 29', 2, 'normal'),
    ('Paint Rollers & Tray', 'paints_finishes', 'Paint roller set with tray', 350, 'Plastic and Fabric', 'small', '', 'finished_product', 'Default Supplier', 'BATCH8010', 'Room 3', 'Shelf 30', 2, 'normal'),

    # Flooring & Tiles (10 products)
    ('Ceramic Floor Tiles 30x30cm', 'flooring_tiles', 'Standard ceramic floor tiles', 280, 'Ceramic', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9001', 'Room 1', 'Shelf 21', 1, 'normal'),
    ('Ceramic Floor Tiles 60x60cm', 'flooring_tiles', 'Large ceramic floor tiles', 450, 'Ceramic', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9002', 'Room 1', 'Shelf 22', 1, 'normal'),
    ('Porcelain Tiles 60x60cm', 'flooring_tiles', 'Premium porcelain floor tiles', 650, 'Porcelain', 'medium', 'Color: Gray', 'finished_product', 'Default Supplier', 'BATCH9003', 'Room 1', 'Shelf 23', 1, 'normal'),
    ('Wall Tiles 20x30cm', 'flooring_tiles', 'Decorative wall tiles for bathrooms', 220, 'Ceramic', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9004', 'Room 1', 'Shelf 24', 1, 'normal'),
    ('Wall Tiles 30x30cm', 'flooring_tiles', 'Standard decorative wall tiles', 280, 'Ceramic', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9005', 'Room 1', 'Shelf 25', 1, 'normal'),
    ('Marble Tiles 30x30cm', 'flooring_tiles', 'Natural marble tiles', 850, 'Marble', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9006', 'Room 2', 'Shelf 31', 1, 'normal'),
    ('Marble Tiles 60x60cm', 'flooring_tiles', 'Large natural marble tiles', 1200, 'Marble', 'medium', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9007', 'Room 2', 'Shelf 32', 1, 'normal'),
    ('Granite Tiles 60x60cm', 'flooring_tiles', 'Durable granite floor tiles', 1500, 'Granite', 'medium', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH9008', 'Room 2', 'Shelf 33', 1, 'normal'),
    ('Tile Adhesive 25kg', 'flooring_tiles', 'Strong tile adhesive cement', 650, 'Cement Adhesive', 'medium', '', 'finished_product', 'Default Supplier', 'BATCH9009', 'Room 2', 'Shelf 34', 1, 'dry'),
    ('Tile Grout 5kg', 'flooring_tiles', 'Waterproof tile grout', 280, 'Cement Grout', 'small', 'Color: White', 'finished_product', 'Default Supplier', 'BATCH9010', 'Room 2', 'Shelf 35', 1, 'dry'),

    # Doors & Windows (5 products)
    ('Wooden Door 80x200cm', 'doors_windows', 'Solid wood interior door', 4500, 'Solid Wood', 'extra_large', 'Color: Brown', 'finished_product', 'Default Supplier', 'BATCH10001', 'Room 3', 'Shelf 31', 1, 'normal'),
    ('Steel Security Door', 'doors_windows', 'Heavy-duty steel entrance door', 8500, 'Steel', 'extra_large', 'Color: Black', 'finished_product', 'Default Supplier', 'BATCH10002', 'Room 3', 'Shelf 32', 1, 'normal'),
    ('Aluminum Window 120x100cm', 'doors_windows', 'Aluminum frame window with glass', 3200, 'Aluminum and Glass', 'large', '', 'finished_product', 'Default Supplier', 'BATCH10003', 'Room 3', 'Shelf 33', 1, 'normal'),
    ('Door Handles Set', 'doors_windows', 'Complete door handle and lock set', 650, 'Brass and Steel', 'small', '', 'finished_product', 'Default Supplier', 'BATCH10004', 'Room 3', 'Shelf 34', 1, 'normal'),
    ('Window Grilles Steel', 'doors_windows', 'Security window grilles', 1200, 'Steel', 'large', '', 'finished_product', 'Default Supplier', 'BATCH10005', 'Room 3', 'Shelf 35', 1, 'normal'),
]

# Insert products
print("\n3. Creating construction products...")
products_created = 0
for product_data in products_data:
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

print(f"\nProducts created: {products_created}")

# Get store and product IDs
cursor.execute("SELECT id, name FROM store_store")
stores = cursor.fetchall()

cursor.execute("SELECT id, name, price FROM Inventory_product")
products = cursor.fetchall()

# Create stock entries
print("\n4. Creating stock entries...")
stocks_created = 0

for store_id, store_name in stores:
    for product_id, product_name, product_price in products:
        # 80% chance of having this product in this store
        if random.choice([True, True, True, True, False]):
            try:
                # Calculate selling price (cost + markup)
                markup_percentage = random.uniform(0.2, 0.6)  # 20-60% markup
                selling_price = float(product_price) * (1 + markup_percentage)
                
                # Random stock quantity
                quantity = random.randint(5, 150)
                low_stock_threshold = random.randint(5, 20)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO Inventory_stock 
                    (product_id, store_id, quantity, low_stock_threshold, selling_price, last_updated) 
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (product_id, store_id, quantity, low_stock_threshold, round(selling_price, 2)))
                
                if cursor.rowcount > 0:
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
print("DATABASE POPULATION COMPLETED!")
print("=" * 50)
print(f"Total stores: {total_stores}")
print(f"Total products: {total_products}")
print(f"Total stock entries: {total_stocks}")
print("=" * 50)

# Close connection
conn.close()

print("\nConstruction products and stocks have been successfully added!")
print("You can now browse them in the webfront at: http://127.0.0.1:8000/webfront/")
