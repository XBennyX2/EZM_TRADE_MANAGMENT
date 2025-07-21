from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from Inventory.models import (
    Product, WarehouseProduct, Supplier, Warehouse, SupplierProfile, SupplierProduct
)


class Command(BaseCommand):
    help = 'Add comprehensive construction company product catalog with proper warehouse inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before adding new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing products...')
            Product.objects.all().delete()
            WarehouseProduct.objects.all().delete()
            SupplierProduct.objects.all().delete()

        # Get or create main warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Main Construction Warehouse',
            defaults={
                'address': 'Industrial Zone, Addis Ababa, Ethiopia',
                'phone': '+251-11-555-0100',
                'email': 'warehouse@ezmtrade.com',
                'manager_name': 'Ato Mulugeta Bekele',
                'capacity': 15000,
                'current_utilization': 0,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(f'✅ Created warehouse: {warehouse.name}')
        else:
            self.stdout.write(f'✅ Using existing warehouse: {warehouse.name}')

        # Get existing suppliers or create them
        suppliers = self.get_or_create_suppliers()
        
        # Create comprehensive product catalog
        self.create_comprehensive_catalog(warehouse, suppliers)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Successfully added comprehensive construction product catalog!')
        )

    def get_or_create_suppliers(self):
        """Get existing suppliers or create them if they don't exist"""
        supplier_mapping = {
            'Plumbing': 'AquaFlow Plumbing Supplies',
            'Electrical': 'PowerLine Electrical Co.',
            'Cement': 'SolidBuild Cement & Masonry', 
            'Hardware': 'ToolMaster Hardware',
            'Paint': 'ColorCraft Paint & Finishing'
        }
        
        suppliers = {}
        for category, supplier_name in supplier_mapping.items():
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_name,
                defaults={
                    'contact_person': f'Manager {supplier_name}',
                    'email': f'contact@{supplier_name.lower().replace(" ", "")}.com',
                    'phone': f'+251-11-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'address': f'{supplier_name} Headquarters, Addis Ababa',
                    'is_active': True
                }
            )
            suppliers[category] = supplier
            if created:
                self.stdout.write(f'✅ Created supplier: {supplier.name}')
            else:
                self.stdout.write(f'✅ Using existing supplier: {supplier.name}')
        
        return suppliers

    def create_comprehensive_catalog(self, warehouse, suppliers):
        """Create comprehensive construction product catalog"""
        
        # Comprehensive product data organized by category
        products_data = {
            'Plumbing': [
                # Pipes
                ('PVC Pipe 110mm x 6m', 'Heavy-duty PVC drainage pipe', 'pieces', 450.00, 120, 'A1-01'),
                ('PVC Pipe 75mm x 6m', 'Standard PVC drainage pipe', 'pieces', 320.00, 150, 'A1-02'),
                ('PVC Pipe 50mm x 6m', 'Small diameter PVC pipe', 'pieces', 180.00, 200, 'A1-03'),
                ('Copper Pipe 22mm x 3m', 'Premium copper water supply pipe', 'pieces', 850.00, 80, 'A1-04'),
                ('Copper Pipe 15mm x 3m', 'Standard copper water pipe', 'pieces', 620.00, 100, 'A1-05'),
                ('HDPE Pipe 32mm x 50m', 'High-density polyethylene pipe roll', 'rolls', 2800.00, 25, 'A1-06'),
                
                # Fittings
                ('PVC Elbow 90° 110mm', 'PVC elbow fitting for drainage', 'pieces', 45.00, 300, 'A2-01'),
                ('PVC Elbow 90° 75mm', 'Standard PVC elbow fitting', 'pieces', 32.00, 400, 'A2-02'),
                ('PVC T-Joint 110mm', 'PVC T-junction for drainage systems', 'pieces', 65.00, 200, 'A2-03'),
                ('Copper Elbow 22mm', 'Copper elbow for water systems', 'pieces', 85.00, 150, 'A2-04'),
                ('Pipe Coupling 50mm', 'Threaded pipe coupling', 'pieces', 28.00, 250, 'A2-05'),
                
                # Valves
                ('Ball Valve 25mm Brass', 'Heavy-duty brass ball valve', 'pieces', 320.00, 60, 'A3-01'),
                ('Gate Valve 20mm', 'Standard gate valve for water control', 'pieces', 280.00, 80, 'A3-02'),
                ('Check Valve 32mm', 'Non-return valve for water systems', 'pieces', 180.00, 100, 'A3-03'),
                ('Stop Valve 15mm', 'Water stop valve with handle', 'pieces', 120.00, 120, 'A3-04'),
                
                # Fixtures
                ('Toilet Suite Complete', 'Complete toilet with cistern and seat', 'sets', 2500.00, 30, 'A4-01'),
                ('Washbasin Ceramic', 'Standard ceramic washbasin', 'pieces', 800.00, 40, 'A4-02'),
                ('Kitchen Sink Stainless Steel', 'Single bowl stainless steel sink', 'pieces', 1200.00, 25, 'A4-03'),
                ('Shower Head Chrome', 'Chrome-plated shower head', 'pieces', 350.00, 60, 'A4-04'),
                ('Tap Mixer Kitchen', 'Kitchen mixer tap with swivel spout', 'pieces', 650.00, 45, 'A4-05'),
            ],

            'Electrical': [
                # Wires and Cables
                ('Electrical Cable 2.5mm² x 100m', 'PVC insulated copper cable', 'rolls', 1800.00, 50, 'B1-01'),
                ('Electrical Cable 1.5mm² x 100m', 'Standard house wiring cable', 'rolls', 1200.00, 80, 'B1-02'),
                ('Electrical Cable 4mm² x 100m', 'Heavy-duty electrical cable', 'rolls', 2800.00, 30, 'B1-03'),
                ('Armored Cable 6mm² x 50m', 'Steel wire armored cable', 'rolls', 3500.00, 20, 'B1-04'),
                ('Coaxial Cable RG6 x 100m', 'TV/satellite coaxial cable', 'rolls', 800.00, 40, 'B1-05'),
                ('Telephone Cable 4-pair x 100m', 'Multi-pair telephone cable', 'rolls', 600.00, 35, 'B1-06'),

                # Switches and Outlets
                ('Light Switch Single Gang', 'Standard single light switch', 'pieces', 45.00, 200, 'B2-01'),
                ('Light Switch Double Gang', 'Double gang light switch', 'pieces', 65.00, 150, 'B2-02'),
                ('Power Outlet 13A', 'Standard 13A power outlet', 'pieces', 55.00, 180, 'B2-03'),
                ('USB Power Outlet', 'Power outlet with USB charging ports', 'pieces', 120.00, 100, 'B2-04'),
                ('Dimmer Switch', 'Variable light dimmer switch', 'pieces', 180.00, 80, 'B2-05'),
                ('Weatherproof Outlet', 'Outdoor weatherproof power outlet', 'pieces', 220.00, 60, 'B2-06'),

                # Circuit Breakers and Protection
                ('MCB 16A Single Pole', 'Miniature circuit breaker 16A', 'pieces', 180.00, 100, 'B3-01'),
                ('MCB 20A Single Pole', 'Miniature circuit breaker 20A', 'pieces', 200.00, 80, 'B3-02'),
                ('MCB 32A Single Pole', 'Heavy-duty circuit breaker 32A', 'pieces', 280.00, 60, 'B3-03'),
                ('RCBO 20A', 'Residual current circuit breaker', 'pieces', 450.00, 40, 'B3-04'),
                ('Surge Protector', 'Electrical surge protection device', 'pieces', 320.00, 50, 'B3-05'),

                # Lighting Fixtures
                ('LED Bulb 9W E27', 'Energy-efficient LED bulb', 'pieces', 85.00, 300, 'B4-01'),
                ('LED Bulb 12W E27', 'High-brightness LED bulb', 'pieces', 120.00, 250, 'B4-02'),
                ('Fluorescent Tube 18W', 'Standard fluorescent tube light', 'pieces', 65.00, 200, 'B4-03'),
                ('Ceiling Light Fixture', 'Modern ceiling light fixture', 'pieces', 450.00, 60, 'B4-04'),
                ('Wall Light Fixture', 'Decorative wall-mounted light', 'pieces', 320.00, 80, 'B4-05'),
                ('Floodlight LED 50W', 'Outdoor LED floodlight', 'pieces', 850.00, 40, 'B4-06'),

                # Electrical Panels and Accessories
                ('Distribution Board 12-way', 'Main electrical distribution board', 'pieces', 1200.00, 25, 'B5-01'),
                ('Distribution Board 6-way', 'Small electrical distribution board', 'pieces', 650.00, 40, 'B5-02'),
                ('Cable Tray 100mm', 'Galvanized cable management tray', 'meters', 120.00, 100, 'B5-03'),
                ('Conduit PVC 20mm x 3m', 'PVC electrical conduit pipe', 'pieces', 45.00, 200, 'B5-04'),
                ('Junction Box IP65', 'Weatherproof electrical junction box', 'pieces', 180.00, 80, 'B5-05'),
            ],

            'Cement': [
                # Cement and Concrete
                ('Portland Cement 50kg', 'High-grade Portland cement', 'bags', 850.00, 500, 'C1-01'),
                ('Rapid Set Cement 25kg', 'Quick-setting cement mix', 'bags', 650.00, 200, 'C1-02'),
                ('White Cement 25kg', 'Premium white Portland cement', 'bags', 1200.00, 100, 'C1-03'),
                ('Ready Mix Concrete m³', 'Pre-mixed concrete delivery', 'cubic_meters', 2800.00, 50, 'C1-04'),
                ('Concrete Additive 5L', 'Concrete strength enhancer', 'liters', 320.00, 80, 'C1-05'),

                # Blocks and Bricks
                ('Concrete Block 200x200x400mm', 'Standard concrete building block', 'pieces', 25.00, 2000, 'C2-01'),
                ('Concrete Block 150x200x400mm', 'Medium concrete building block', 'pieces', 20.00, 2500, 'C2-02'),
                ('Concrete Block 100x200x400mm', 'Thin concrete building block', 'pieces', 15.00, 3000, 'C2-03'),
                ('Clay Brick Red 230x110x75mm', 'Traditional red clay brick', 'pieces', 8.00, 5000, 'C2-04'),
                ('Clay Brick Perforated', 'Lightweight perforated clay brick', 'pieces', 12.00, 3000, 'C2-05'),
                ('Interlocking Block', 'Self-locking concrete block', 'pieces', 35.00, 1500, 'C2-06'),

                # Mortar and Aggregates
                ('Mortar Mix 25kg', 'Ready-to-use mortar mix', 'bags', 180.00, 300, 'C3-01'),
                ('Sand Fine Grade m³', 'Fine construction sand', 'cubic_meters', 800.00, 100, 'C3-02'),
                ('Sand Coarse Grade m³', 'Coarse construction sand', 'cubic_meters', 750.00, 120, 'C3-03'),
                ('Gravel 20mm m³', 'Construction gravel aggregate', 'cubic_meters', 900.00, 80, 'C3-04'),
                ('Crushed Stone m³', 'Crushed stone aggregate', 'cubic_meters', 1200.00, 60, 'C3-05'),
                ('Lime Hydrated 25kg', 'Hydrated lime for mortar', 'bags', 220.00, 150, 'C3-06'),

                # Reinforcement
                ('Rebar 12mm x 12m', 'Deformed steel reinforcement bar', 'pieces', 180.00, 400, 'C4-01'),
                ('Rebar 16mm x 12m', 'Heavy-duty reinforcement bar', 'pieces', 320.00, 300, 'C4-02'),
                ('Rebar 20mm x 12m', 'Extra heavy reinforcement bar', 'pieces', 500.00, 200, 'C4-03'),
                ('Wire Mesh 6mm 2x3m', 'Welded wire reinforcement mesh', 'sheets', 450.00, 100, 'C4-04'),
                ('Tie Wire 1.6mm x 100m', 'Rebar binding wire', 'rolls', 120.00, 200, 'C4-05'),
                ('Rebar Cutter Tool', 'Manual rebar cutting tool', 'pieces', 850.00, 15, 'C4-06'),

                # Tiles and Finishing
                ('Ceramic Floor Tile 300x300mm', 'Standard ceramic floor tile', 'square_meters', 180.00, 500, 'C5-01'),
                ('Ceramic Wall Tile 200x300mm', 'Bathroom/kitchen wall tile', 'square_meters', 220.00, 400, 'C5-02'),
                ('Porcelain Tile 600x600mm', 'Premium porcelain floor tile', 'square_meters', 450.00, 200, 'C5-03'),
                ('Tile Adhesive 25kg', 'Ceramic tile adhesive', 'bags', 320.00, 150, 'C5-04'),
                ('Tile Grout 5kg', 'Waterproof tile grout', 'bags', 180.00, 200, 'C5-05'),
                ('Tile Spacers 2mm', 'Plastic tile spacing clips', 'packs', 25.00, 300, 'C5-06'),
            ],

            'Hardware': [
                # Fasteners
                ('Wood Screws 4x50mm', 'Self-tapping wood screws', 'boxes_100', 45.00, 200, 'D1-01'),
                ('Wood Screws 6x80mm', 'Heavy-duty wood screws', 'boxes_100', 85.00, 150, 'D1-02'),
                ('Machine Bolts M12x80mm', 'Galvanized machine bolts with nuts', 'boxes_50', 180.00, 100, 'D1-03'),
                ('Anchor Bolts M16x120mm', 'Concrete anchor bolts', 'boxes_25', 320.00, 80, 'D1-04'),
                ('Nails Common 75mm', 'Standard construction nails', 'kg', 120.00, 300, 'D1-05'),
                ('Nails Roofing 65mm', 'Galvanized roofing nails', 'kg', 140.00, 200, 'D1-06'),
                ('Washers M12 Galvanized', 'Flat washers for bolts', 'boxes_100', 65.00, 150, 'D1-07'),

                # Hand Tools
                ('Hammer Claw 450g', 'Steel claw hammer with wooden handle', 'pieces', 320.00, 50, 'D2-01'),
                ('Hammer Sledge 3kg', 'Heavy-duty sledge hammer', 'pieces', 650.00, 25, 'D2-02'),
                ('Screwdriver Set Phillips', 'Set of Phillips head screwdrivers', 'sets', 180.00, 60, 'D2-03'),
                ('Screwdriver Set Flathead', 'Set of flathead screwdrivers', 'sets', 160.00, 60, 'D2-04'),
                ('Pliers Combination 200mm', 'Multi-purpose combination pliers', 'pieces', 220.00, 80, 'D2-05'),
                ('Wire Cutters 150mm', 'Electrical wire cutting pliers', 'pieces', 180.00, 70, 'D2-06'),
                ('Adjustable Wrench 250mm', 'Adjustable spanner wrench', 'pieces', 280.00, 60, 'D2-07'),

                # Power Tools
                ('Drill Electric 13mm', 'Electric drill with chuck', 'pieces', 1200.00, 20, 'D3-01'),
                ('Angle Grinder 115mm', 'Electric angle grinder', 'pieces', 850.00, 25, 'D3-02'),
                ('Circular Saw 185mm', 'Electric circular saw', 'pieces', 1800.00, 15, 'D3-03'),
                ('Jigsaw Electric', 'Variable speed electric jigsaw', 'pieces', 950.00, 20, 'D3-04'),
                ('Impact Driver', 'Cordless impact driver', 'pieces', 1500.00, 18, 'D3-05'),
                ('Drill Bits Set HSS', 'High-speed steel drill bit set', 'sets', 320.00, 40, 'D3-06'),

                # Measuring Tools
                ('Tape Measure 5m', 'Steel tape measure with lock', 'pieces', 120.00, 100, 'D4-01'),
                ('Tape Measure 8m', 'Heavy-duty steel tape measure', 'pieces', 180.00, 80, 'D4-02'),
                ('Spirit Level 600mm', 'Aluminum spirit level', 'pieces', 280.00, 60, 'D4-03'),
                ('Spirit Level 1200mm', 'Professional long spirit level', 'pieces', 450.00, 40, 'D4-04'),
                ('Square Steel 300mm', 'Steel try square for marking', 'pieces', 150.00, 70, 'D4-05'),
                ('Measuring Wheel', 'Professional measuring wheel', 'pieces', 850.00, 15, 'D4-06'),

                # Safety Equipment
                ('Safety Helmet White', 'Construction safety helmet', 'pieces', 180.00, 100, 'D5-01'),
                ('Safety Goggles Clear', 'Impact-resistant safety goggles', 'pieces', 85.00, 150, 'D5-02'),
                ('Work Gloves Leather', 'Heavy-duty leather work gloves', 'pairs', 120.00, 200, 'D5-03'),
                ('Safety Vest Hi-Vis', 'High-visibility safety vest', 'pieces', 150.00, 100, 'D5-04'),
                ('Ear Plugs Foam', 'Disposable foam ear plugs', 'boxes_50', 45.00, 80, 'D5-05'),
                ('First Aid Kit', 'Complete workplace first aid kit', 'pieces', 320.00, 30, 'D5-06'),
            ],

            'Paint': [
                # Interior Paints
                ('Emulsion Paint White 20L', 'Premium white interior emulsion', 'liters', 1800.00, 60, 'E1-01'),
                ('Emulsion Paint Cream 20L', 'Cream colored interior emulsion', 'liters', 1850.00, 50, 'E1-02'),
                ('Emulsion Paint Blue 20L', 'Blue interior emulsion paint', 'liters', 1900.00, 40, 'E1-03'),
                ('Emulsion Paint Green 20L', 'Green interior emulsion paint', 'liters', 1900.00, 40, 'E1-04'),
                ('Gloss Paint White 5L', 'High-gloss white interior paint', 'liters', 850.00, 80, 'E1-05'),
                ('Matt Paint White 20L', 'Matt finish white interior paint', 'liters', 1600.00, 70, 'E1-06'),

                # Exterior Paints
                ('Exterior Paint White 20L', 'Weather-resistant exterior paint', 'liters', 2200.00, 50, 'E2-01'),
                ('Exterior Paint Beige 20L', 'Beige weather-resistant paint', 'liters', 2250.00, 45, 'E2-02'),
                ('Masonry Paint 20L', 'Specialized masonry exterior paint', 'liters', 2400.00, 40, 'E2-03'),
                ('Roof Paint Red 20L', 'Metal roof protective paint', 'liters', 2800.00, 30, 'E2-04'),
                ('Anti-Rust Paint 5L', 'Metal protection anti-rust paint', 'liters', 950.00, 60, 'E2-05'),

                # Primers and Undercoats
                ('Primer Sealer 20L', 'Universal primer sealer', 'liters', 1400.00, 80, 'E3-01'),
                ('Wood Primer 5L', 'Specialized wood primer', 'liters', 650.00, 100, 'E3-02'),
                ('Metal Primer 5L', 'Anti-corrosive metal primer', 'liters', 750.00, 80, 'E3-03'),
                ('Concrete Primer 20L', 'Concrete surface primer', 'liters', 1600.00, 60, 'E3-04'),
                ('Stain Blocker 5L', 'Stain blocking primer', 'liters', 850.00, 70, 'E3-05'),

                # Brushes and Rollers
                ('Paint Brush 50mm', 'Professional paint brush', 'pieces', 120.00, 150, 'E4-01'),
                ('Paint Brush 75mm', 'Wide professional paint brush', 'pieces', 180.00, 120, 'E4-02'),
                ('Paint Brush 100mm', 'Extra wide paint brush', 'pieces', 250.00, 100, 'E4-03'),
                ('Roller Frame 230mm', 'Paint roller frame with handle', 'pieces', 180.00, 80, 'E4-04'),
                ('Roller Sleeve Medium', 'Medium nap roller sleeve', 'pieces', 65.00, 200, 'E4-05'),
                ('Roller Sleeve Smooth', 'Smooth finish roller sleeve', 'pieces', 55.00, 200, 'E4-06'),
                ('Paint Tray Large', 'Large paint roller tray', 'pieces', 85.00, 100, 'E4-07'),

                # Sealants and Adhesives
                ('Silicone Sealant Clear', 'Clear waterproof silicone sealant', 'tubes', 85.00, 200, 'E5-01'),
                ('Silicone Sealant White', 'White bathroom silicone sealant', 'tubes', 90.00, 180, 'E5-02'),
                ('Acrylic Sealant', 'Paintable acrylic gap filler', 'tubes', 75.00, 220, 'E5-03'),
                ('Construction Adhesive', 'Heavy-duty construction adhesive', 'tubes', 120.00, 150, 'E5-04'),
                ('Wood Glue 500ml', 'PVA wood adhesive', 'bottles', 180.00, 100, 'E5-05'),
                ('Tile Adhesive Flexible', 'Flexible ceramic tile adhesive', 'bags', 320.00, 80, 'E5-06'),
                ('Caulking Gun', 'Professional caulking gun', 'pieces', 180.00, 60, 'E5-07'),

                # Finishing Materials
                ('Sandpaper 120 Grit', 'Medium grit sandpaper sheets', 'packs_10', 45.00, 200, 'E6-01'),
                ('Sandpaper 240 Grit', 'Fine grit sandpaper sheets', 'packs_10', 50.00, 180, 'E6-02'),
                ('Steel Wool Fine', 'Fine grade steel wool', 'packs', 35.00, 150, 'E6-03'),
                ('Masking Tape 25mm', 'Painter\'s masking tape', 'rolls', 45.00, 300, 'E6-04'),
                ('Drop Cloth Plastic', 'Protective plastic drop cloth', 'pieces', 25.00, 200, 'E6-05'),
                ('Paint Thinner 5L', 'Paint thinner and cleaner', 'liters', 320.00, 80, 'E6-06'),
            ]
        }

        # Create products for each category
        total_products = 0
        total_warehouse_products = 0

        for category, products in products_data.items():
            supplier = suppliers[category]
            self.stdout.write(f'\n📦 Creating {category} products for {supplier.name}...')

            category_products = 0
            category_warehouse_products = 0

            for product_data in products:
                name, description, unit, price, stock_qty, location = product_data

                # Generate unique SKU and product ID
                sku = f"{category[:3].upper()}-{len(Product.objects.filter(category=category)) + 1:04d}"
                product_id = f"WH-{category[:3].upper()}-{len(WarehouseProduct.objects.filter(category=category)) + 1:04d}"

                # Create Product
                product = Product.objects.create(
                    name=name,
                    category=category,
                    description=description,
                    price=Decimal(str(price)),
                    material='Construction Material',
                    product_type='raw_material' if 'material' in description.lower() else 'finished_product',
                    supplier_company=supplier.name
                )

                # Create WarehouseProduct
                warehouse_product = WarehouseProduct.objects.create(
                    product_id=product_id,
                    product_name=name,
                    category=category,
                    quantity_in_stock=stock_qty,
                    unit_price=Decimal(str(price * 0.85)),  # Cost price (15% less than selling price)
                    minimum_stock_level=max(10, stock_qty // 10),
                    maximum_stock_level=stock_qty * 3,
                    reorder_point=max(20, stock_qty // 5),
                    sku=sku,
                    barcode=f"251{random.randint(1000000000, 9999999999)}",
                    weight=self.calculate_weight(name, unit),
                    dimensions=self.calculate_dimensions(name),
                    warehouse_location=location,
                    supplier=supplier,
                    warehouse=warehouse,
                    batch_number=f"{category[:3].upper()}{timezone.now().strftime('%Y%m')}001",
                    arrival_date=timezone.now()
                )

                # Create SupplierProduct entry
                SupplierProduct.objects.create(
                    supplier=supplier,
                    warehouse_product=warehouse_product,
                    product_name=name,
                    product_code=sku,
                    description=description,
                    category=category,
                    unit_price=Decimal(str(price)),
                    minimum_order_quantity=1,
                    specifications=f"Unit: {unit}, Location: {location}",
                    availability_status='in_stock',
                    estimated_delivery_time='3-5 business days',
                    stock_quantity=stock_qty
                )

                category_products += 1
                category_warehouse_products += 1

                self.stdout.write(f'  ✅ {name} - Stock: {stock_qty} {unit} - Location: {location}')

            self.stdout.write(f'  📊 {category}: {category_products} products, {category_warehouse_products} warehouse items')
            total_products += category_products
            total_warehouse_products += category_warehouse_products

        self.stdout.write(f'\n📈 SUMMARY:')
        self.stdout.write(f'  Total Products Created: {total_products}')
        self.stdout.write(f'  Total Warehouse Items: {total_warehouse_products}')
        self.stdout.write(f'  Total Suppliers: {len(suppliers)}')

    def calculate_weight(self, name, unit):
        """Calculate estimated weight based on product name and unit"""
        name_lower = name.lower()

        # Weight estimates based on product type
        if 'cement' in name_lower and '50kg' in name_lower:
            return Decimal('50.00')
        elif 'cement' in name_lower and '25kg' in name_lower:
            return Decimal('25.00')
        elif 'pipe' in name_lower:
            if '110mm' in name_lower:
                return Decimal('8.50')
            elif '75mm' in name_lower:
                return Decimal('5.20')
            elif '50mm' in name_lower:
                return Decimal('2.80')
            elif '22mm' in name_lower:
                return Decimal('1.85')
            elif '15mm' in name_lower:
                return Decimal('1.20')
        elif 'block' in name_lower:
            return Decimal('18.50')
        elif 'brick' in name_lower:
            return Decimal('2.50')
        elif 'paint' in name_lower and '20l' in name_lower:
            return Decimal('22.00')
        elif 'paint' in name_lower and '5l' in name_lower:
            return Decimal('5.50')
        elif 'cable' in name_lower and '100m' in name_lower:
            return Decimal('15.00')
        elif 'rebar' in name_lower:
            if '20mm' in name_lower:
                return Decimal('23.50')
            elif '16mm' in name_lower:
                return Decimal('15.00')
            elif '12mm' in name_lower:
                return Decimal('8.50')

        # Default weights by unit type
        if unit == 'bags':
            return Decimal('25.00')
        elif unit == 'liters':
            return Decimal('1.10')  # Slightly more than water
        elif unit == 'pieces':
            return Decimal('2.50')
        elif unit == 'rolls':
            return Decimal('12.00')
        else:
            return Decimal('5.00')  # Default weight

    def calculate_dimensions(self, name):
        """Calculate estimated dimensions based on product name"""
        name_lower = name.lower()

        if 'cement' in name_lower and '50kg' in name_lower:
            return '60x40x15 cm'
        elif 'cement' in name_lower and '25kg' in name_lower:
            return '50x35x12 cm'
        elif 'pipe' in name_lower and '6m' in name_lower:
            return '600x11x11 cm'
        elif 'pipe' in name_lower and '3m' in name_lower:
            return '300x2.2x2.2 cm'
        elif 'block' in name_lower:
            return '40x20x20 cm'
        elif 'brick' in name_lower:
            return '23x11x7.5 cm'
        elif 'paint' in name_lower and '20l' in name_lower:
            return '35x25x40 cm'
        elif 'paint' in name_lower and '5l' in name_lower:
            return '25x20x30 cm'
        elif 'cable' in name_lower and '100m' in name_lower:
            return '40x40x15 cm'
        elif 'rebar' in name_lower and '12m' in name_lower:
            return '1200x2x2 cm'
        else:
            return '30x20x15 cm'  # Default dimensions
