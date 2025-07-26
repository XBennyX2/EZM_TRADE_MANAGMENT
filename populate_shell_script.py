# Run this script in Django shell: python manage.py shell < populate_shell_script.py

from store.models import Store
from Inventory.models import Product, Stock, Supplier
from decimal import Decimal
import random
from datetime import datetime, timedelta

print("Starting database population...")

# Create sample stores
sample_stores = [
    {'name': 'Main Branch', 'address': 'Bole, Addis Ababa', 'phone_number': '+251911111111'},
    {'name': 'Piazza Branch', 'address': 'Piazza, Addis Ababa', 'phone_number': '+251911111112'},
    {'name': 'Merkato Branch', 'address': 'Merkato, Addis Ababa', 'phone_number': '+251911111113'},
    {'name': 'CMC Branch', 'address': 'CMC, Addis Ababa', 'phone_number': '+251911111114'},
    {'name': 'Kazanchis Branch', 'address': 'Kazanchis, Addis Ababa', 'phone_number': '+251911111115'},
]

stores_created = 0
for store_data in sample_stores:
    store, created = Store.objects.get_or_create(
        name=store_data['name'],
        defaults=store_data
    )
    if created:
        stores_created += 1
        print(f"Created store: {store.name}")

print(f"Stores created: {stores_created}")

# Get or create supplier
supplier, created = Supplier.objects.get_or_create(
    name='Default Supplier',
    defaults={
        'contact_person': 'Supply Manager',
        'email': 'supplier@example.com',
        'phone': '+251911000000',
        'address': 'Addis Ababa, Ethiopia'
    }
)

# Sample construction products
products_data = [
    # Construction Materials - Cement & Concrete
    {'name': 'Portland Cement 50kg', 'category': 'construction_materials', 'desc': 'High-quality Portland cement for construction', 'price': 850, 'material': 'Cement'},
    {'name': 'Ready Mix Concrete m³', 'category': 'construction_materials', 'desc': 'Pre-mixed concrete for construction projects', 'price': 2500, 'material': 'Concrete'},
    {'name': 'Concrete Blocks 20x20x40cm', 'category': 'construction_materials', 'desc': 'Standard concrete blocks for building', 'price': 25, 'material': 'Concrete'},
    {'name': 'Cement Mortar Mix 25kg', 'category': 'construction_materials', 'desc': 'Pre-mixed mortar for masonry work', 'price': 450, 'material': 'Cement Mortar'},
    {'name': 'Reinforcement Steel Bars 12mm', 'category': 'construction_materials', 'desc': 'Steel reinforcement bars for concrete', 'price': 1200, 'material': 'Steel'},
    {'name': 'Wire Mesh 6mm', 'category': 'construction_materials', 'desc': 'Steel wire mesh for reinforcement', 'price': 850, 'material': 'Steel Wire'},
    {'name': 'Gravel 20mm - 1 ton', 'category': 'construction_materials', 'desc': 'Construction grade gravel aggregate', 'price': 1800, 'material': 'Stone Aggregate'},
    {'name': 'Sand - Fine Grade 1 ton', 'category': 'construction_materials', 'desc': 'Fine sand for construction and plastering', 'price': 1200, 'material': 'Sand'},
    {'name': 'Crushed Stone 40mm - 1 ton', 'category': 'construction_materials', 'desc': 'Crushed stone for foundation work', 'price': 1500, 'material': 'Stone'},
    {'name': 'Lime Powder 25kg', 'category': 'construction_materials', 'desc': 'Hydrated lime for mortar and plaster', 'price': 350, 'material': 'Lime'},

    # Building Materials - Bricks & Blocks
    {'name': 'Red Clay Bricks', 'category': 'building_materials', 'desc': 'Traditional red clay bricks for construction', 'price': 8, 'material': 'Clay'},
    {'name': 'Hollow Blocks 15x20x40cm', 'category': 'building_materials', 'desc': 'Lightweight hollow concrete blocks', 'price': 35, 'material': 'Concrete'},
    {'name': 'Interlocking Blocks', 'category': 'building_materials', 'desc': 'Self-locking concrete blocks', 'price': 45, 'material': 'Concrete'},
    {'name': 'Paving Stones 30x30cm', 'category': 'building_materials', 'desc': 'Decorative paving stones for walkways', 'price': 85, 'material': 'Concrete'},
    {'name': 'Roof Tiles - Clay', 'category': 'building_materials', 'desc': 'Traditional clay roof tiles', 'price': 25, 'material': 'Clay'},
    {'name': 'Corrugated Iron Sheets 3m', 'category': 'building_materials', 'desc': 'Galvanized iron roofing sheets', 'price': 1200, 'material': 'Galvanized Steel'},
    {'name': 'Aluminum Roofing Sheets 3m', 'category': 'building_materials', 'desc': 'Lightweight aluminum roofing', 'price': 1800, 'material': 'Aluminum'},
    {'name': 'Ceramic Floor Tiles 60x60cm', 'category': 'building_materials', 'desc': 'High-quality ceramic floor tiles', 'price': 450, 'material': 'Ceramic'},
    {'name': 'Wall Tiles 30x30cm', 'category': 'building_materials', 'desc': 'Decorative wall tiles for bathrooms', 'price': 280, 'material': 'Ceramic'},
    {'name': 'Marble Tiles 60x60cm', 'category': 'building_materials', 'desc': 'Premium marble tiles for flooring', 'price': 1200, 'material': 'Marble'},

    # Construction Tools & Equipment
    {'name': 'Electric Drill 18V', 'category': 'construction_tools', 'desc': 'Cordless electric drill with battery', 'price': 3500, 'material': 'Metal and Plastic'},
    {'name': 'Angle Grinder 9"', 'category': 'construction_tools', 'desc': 'Heavy-duty angle grinder for cutting', 'price': 2800, 'material': 'Metal'},
    {'name': 'Circular Saw 7.25"', 'category': 'construction_tools', 'desc': 'Electric circular saw for wood cutting', 'price': 4200, 'material': 'Metal and Plastic'},
    {'name': 'Hammer Drill SDS', 'category': 'construction_tools', 'desc': 'Professional hammer drill for concrete', 'price': 5500, 'material': 'Metal'},
    {'name': 'Welding Machine 200A', 'category': 'construction_tools', 'desc': 'Arc welding machine for steel work', 'price': 15000, 'material': 'Metal'},
    {'name': 'Concrete Mixer 150L', 'category': 'construction_tools', 'desc': 'Electric concrete mixer for small jobs', 'price': 12000, 'material': 'Steel'},
    {'name': 'Tile Cutter 600mm', 'category': 'construction_tools', 'desc': 'Manual tile cutting machine', 'price': 2200, 'material': 'Steel'},
    {'name': 'Spirit Level 1.2m', 'category': 'construction_tools', 'desc': 'Professional aluminum spirit level', 'price': 850, 'material': 'Aluminum'},
    {'name': 'Measuring Tape 5m', 'category': 'construction_tools', 'desc': 'Steel measuring tape with lock', 'price': 450, 'material': 'Steel and Plastic'},
    {'name': 'Safety Helmet', 'category': 'construction_tools', 'desc': 'Construction safety helmet', 'price': 350, 'material': 'Plastic'},

    # Plumbing & Electrical
    {'name': 'PVC Pipes 4" x 3m', 'category': 'plumbing_electrical', 'desc': 'PVC drainage pipes for plumbing', 'price': 450, 'material': 'PVC'},
    {'name': 'Copper Pipes 1/2" x 3m', 'category': 'plumbing_electrical', 'desc': 'Copper pipes for water supply', 'price': 850, 'material': 'Copper'},
    {'name': 'PVC Fittings Set', 'category': 'plumbing_electrical', 'desc': 'Complete set of PVC pipe fittings', 'price': 650, 'material': 'PVC'},
    {'name': 'Water Pump 1HP', 'category': 'plumbing_electrical', 'desc': 'Centrifugal water pump for buildings', 'price': 8500, 'material': 'Cast Iron'},
    {'name': 'Electrical Cable 2.5mm²', 'category': 'plumbing_electrical', 'desc': 'Copper electrical cable per meter', 'price': 45, 'material': 'Copper'},
    {'name': 'Circuit Breaker 20A', 'category': 'plumbing_electrical', 'desc': 'Single pole circuit breaker', 'price': 350, 'material': 'Plastic and Metal'},
    {'name': 'LED Light Bulbs 12W', 'category': 'plumbing_electrical', 'desc': 'Energy efficient LED bulbs', 'price': 180, 'material': 'Plastic and LED'},
    {'name': 'Wall Switches & Sockets', 'category': 'plumbing_electrical', 'desc': 'Standard electrical switches and sockets', 'price': 120, 'material': 'Plastic'},
    {'name': 'Conduit Pipes 20mm', 'category': 'plumbing_electrical', 'desc': 'Electrical conduit pipes per meter', 'price': 25, 'material': 'PVC'},
    {'name': 'Junction Boxes', 'category': 'plumbing_electrical', 'desc': 'Electrical junction boxes', 'price': 85, 'material': 'Plastic'},

    # Hardware & Fasteners
    {'name': 'Steel Nails 4" - 1kg', 'category': 'hardware_fasteners', 'desc': 'Common steel nails for construction', 'price': 180, 'material': 'Steel'},
    {'name': 'Wood Screws 3" - 100pcs', 'category': 'hardware_fasteners', 'desc': 'Self-tapping wood screws', 'price': 250, 'material': 'Steel'},
    {'name': 'Anchor Bolts M12 - 10pcs', 'category': 'hardware_fasteners', 'desc': 'Heavy-duty anchor bolts for concrete', 'price': 450, 'material': 'Steel'},
    {'name': 'Hinges Heavy Duty - Pair', 'category': 'hardware_fasteners', 'desc': 'Strong door hinges for construction', 'price': 350, 'material': 'Steel'},
    {'name': 'Padlocks 50mm', 'category': 'hardware_fasteners', 'desc': 'Security padlocks for construction sites', 'price': 280, 'material': 'Steel and Brass'},
    {'name': 'Chain Link 8mm - 1m', 'category': 'hardware_fasteners', 'desc': 'Heavy-duty steel chain per meter', 'price': 120, 'material': 'Steel'},
    {'name': 'Wire Rope 6mm - 1m', 'category': 'hardware_fasteners', 'desc': 'Galvanized steel wire rope', 'price': 85, 'material': 'Galvanized Steel'},
    {'name': 'U-Bolts M10 - 10pcs', 'category': 'hardware_fasteners', 'desc': 'U-shaped bolts for pipe mounting', 'price': 320, 'material': 'Steel'},
    {'name': 'Washers Assorted - 100pcs', 'category': 'hardware_fasteners', 'desc': 'Mixed size steel washers', 'price': 150, 'material': 'Steel'},
    {'name': 'Nuts & Bolts Set M8-M16', 'category': 'hardware_fasteners', 'desc': 'Assorted nuts and bolts set', 'price': 650, 'material': 'Steel'},

    # Paints & Finishes
    {'name': 'Exterior Wall Paint 20L', 'category': 'paints_finishes', 'desc': 'Weather-resistant exterior paint', 'price': 2800, 'material': 'Acrylic Paint'},
    {'name': 'Interior Emulsion Paint 20L', 'category': 'paints_finishes', 'desc': 'Smooth finish interior wall paint', 'price': 2200, 'material': 'Emulsion Paint'},
    {'name': 'Primer Sealer 5L', 'category': 'paints_finishes', 'desc': 'Wall primer and sealer', 'price': 850, 'material': 'Primer'},
    {'name': 'Wood Stain 1L', 'category': 'paints_finishes', 'desc': 'Protective wood stain and finish', 'price': 650, 'material': 'Wood Stain'},
    {'name': 'Metal Paint Anti-Rust 5L', 'category': 'paints_finishes', 'desc': 'Anti-corrosion metal paint', 'price': 1800, 'material': 'Enamel Paint'},
    {'name': 'Floor Paint Epoxy 5L', 'category': 'paints_finishes', 'desc': 'Durable epoxy floor coating', 'price': 3500, 'material': 'Epoxy'},
    {'name': 'Paint Brushes Set', 'category': 'paints_finishes', 'desc': 'Professional painting brushes', 'price': 450, 'material': 'Bristle and Wood'},
    {'name': 'Paint Rollers & Tray', 'category': 'paints_finishes', 'desc': 'Paint roller set with tray', 'price': 350, 'material': 'Plastic and Fabric'},
    {'name': 'Masking Tape 50mm', 'category': 'paints_finishes', 'desc': 'Painter\'s masking tape', 'price': 120, 'material': 'Paper and Adhesive'},
    {'name': 'Sandpaper Assorted Pack', 'category': 'paints_finishes', 'desc': 'Various grit sandpaper sheets', 'price': 280, 'material': 'Abrasive Paper'},

    # Doors & Windows
    {'name': 'Wooden Door 80x200cm', 'category': 'doors_windows', 'desc': 'Solid wood interior door', 'price': 4500, 'material': 'Solid Wood'},
    {'name': 'Steel Security Door', 'category': 'doors_windows', 'desc': 'Heavy-duty steel entrance door', 'price': 8500, 'material': 'Steel'},
    {'name': 'Aluminum Window 120x100cm', 'category': 'doors_windows', 'desc': 'Aluminum frame window with glass', 'price': 3200, 'material': 'Aluminum and Glass'},
    {'name': 'PVC Window 100x80cm', 'category': 'doors_windows', 'desc': 'Double-glazed PVC window', 'price': 2800, 'material': 'PVC and Glass'},
    {'name': 'Door Handles Set', 'category': 'doors_windows', 'desc': 'Complete door handle and lock set', 'price': 650, 'material': 'Brass and Steel'},
    {'name': 'Window Grilles Steel', 'category': 'doors_windows', 'desc': 'Security window grilles', 'price': 1200, 'material': 'Steel'},
    {'name': 'Door Frame Wood', 'category': 'doors_windows', 'desc': 'Wooden door frame set', 'price': 1800, 'material': 'Wood'},
    {'name': 'Window Blinds 120cm', 'category': 'doors_windows', 'desc': 'Horizontal window blinds', 'price': 850, 'material': 'Aluminum'},
    {'name': 'Glass Sheets 4mm', 'category': 'doors_windows', 'desc': 'Clear glass sheets per square meter', 'price': 450, 'material': 'Glass'},
    {'name': 'Weather Stripping', 'category': 'doors_windows', 'desc': 'Door and window sealing strips', 'price': 180, 'material': 'Rubber'},

    # Insulation & Waterproofing
    {'name': 'Foam Insulation Boards', 'category': 'insulation_waterproofing', 'desc': 'Rigid foam insulation panels', 'price': 850, 'material': 'Polyurethane Foam'},
    {'name': 'Waterproof Membrane', 'category': 'insulation_waterproofing', 'desc': 'Bitumen waterproofing membrane', 'price': 1200, 'material': 'Bitumen'},
    {'name': 'Roof Sealant 5L', 'category': 'insulation_waterproofing', 'desc': 'Liquid roof waterproofing sealant', 'price': 2200, 'material': 'Polymer Sealant'},
    {'name': 'Thermal Insulation Wool', 'category': 'insulation_waterproofing', 'desc': 'Mineral wool insulation rolls', 'price': 650, 'material': 'Mineral Wool'},
    {'name': 'Vapor Barrier Plastic', 'category': 'insulation_waterproofing', 'desc': 'Plastic vapor barrier sheeting', 'price': 280, 'material': 'Polyethylene'},
    {'name': 'Expansion Joint Filler', 'category': 'insulation_waterproofing', 'desc': 'Flexible joint filler material', 'price': 450, 'material': 'Foam'},
    {'name': 'Waterproof Coating 20L', 'category': 'insulation_waterproofing', 'desc': 'Liquid waterproof coating', 'price': 3500, 'material': 'Acrylic Polymer'},
    {'name': 'Damp Proof Course', 'category': 'insulation_waterproofing', 'desc': 'Damp proof membrane for walls', 'price': 380, 'material': 'Bitumen'},
    {'name': 'Silicone Sealant Tubes', 'category': 'insulation_waterproofing', 'desc': 'Waterproof silicone sealant', 'price': 150, 'material': 'Silicone'},
    {'name': 'Caulking Gun', 'category': 'insulation_waterproofing', 'desc': 'Professional caulking gun', 'price': 320, 'material': 'Metal and Plastic'},
]

# Create products
products_created = 0
for item in products_data:
    if not Product.objects.filter(name=item['name']).exists():
        # Add some variation to prices
        base_price = item['price']
        varied_price = base_price + random.randint(-int(base_price*0.1), int(base_price*0.1))
        
        product = Product.objects.create(
            name=item['name'],
            category=item['category'],
            description=item['desc'],
            price=Decimal(str(varied_price)),
            material=item['material'],
            size=random.choice(['small', 'medium', 'large', 'extra_large']) if random.choice([True, False]) else '',
            variation=f"Color: {random.choice(['Black', 'White', 'Blue', 'Red', 'Green'])}" if random.choice([True, False]) else '',
            product_type='finished_product',
            supplier_company=supplier.name,
            batch_number=f"BATCH{random.randint(1000, 9999)}",
            expiry_date=datetime.now().date() + timedelta(days=random.randint(365, 1095)) if random.choice([True, False]) else None,
            room=f"Room {random.randint(1, 5)}",
            shelf=f"Shelf {random.randint(1, 20)}",
            floor=random.randint(1, 3),
            storing_condition=random.choice(['normal', 'cold', 'dry', 'frozen'])
        )
        products_created += 1
        print(f"Created product: {product.name}")

print(f"Products created: {products_created}")

# Create stocks
stores = Store.objects.all()
products = Product.objects.all()
stocks_created = 0

for store in stores:
    for product in products:
        # 75% chance of having this product in this store
        if random.choice([True, True, True, False]):
            if not Stock.objects.filter(product=product, store=store).exists():
                # Calculate selling price (cost + markup)
                markup_percentage = random.uniform(0.2, 0.8)  # 20-80% markup
                selling_price = product.price * (1 + markup_percentage)
                
                # Random stock quantity
                quantity = random.randint(0, 100)
                
                Stock.objects.create(
                    product=product,
                    store=store,
                    quantity=quantity,
                    low_stock_threshold=random.randint(5, 20),
                    selling_price=selling_price.quantize(Decimal('0.01'))
                )
                stocks_created += 1

print(f"Stock entries created: {stocks_created}")
print(f"Total stores: {Store.objects.count()}")
print(f"Total products: {Product.objects.count()}")
print(f"Total stock entries: {Stock.objects.count()}")
print("Database population completed!")
