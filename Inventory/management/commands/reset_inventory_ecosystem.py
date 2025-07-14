from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from Inventory.models import (
    Product, Stock, WarehouseProduct, Supplier, Warehouse, Store,
    RestockRequest, StoreStockTransferRequest, PurchaseOrder
)
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset and restructure the entire inventory ecosystem with synchronized data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to reset all inventory data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will DELETE ALL inventory data. '
                    'Use --confirm to proceed.'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('🔄 Starting Inventory Ecosystem Reset'))
        self.stdout.write('=' * 60)

        with transaction.atomic():
            # Step 1: Data Cleanup
            self.stdout.write('\n📋 Step 1: Data Cleanup')
            self.cleanup_existing_data()

            # Step 2: Supplier Setup
            self.stdout.write('\n🏢 Step 2: Supplier Setup')
            suppliers = self.create_suppliers()

            # Step 3: Product Catalog Creation
            self.stdout.write('\n📦 Step 3: Product Catalog Creation')
            products = self.create_product_catalog(suppliers)

            # Step 4: Warehouse Stock Initialization
            self.stdout.write('\n🏭 Step 4: Warehouse Stock Initialization')
            self.initialize_warehouse_stock(products, suppliers)

            # Step 5: Testing Data Creation
            self.stdout.write('\n🧪 Step 5: Testing Data Creation')
            self.create_testing_data()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Inventory Ecosystem Reset Complete!'))
        self.display_summary()

    def cleanup_existing_data(self):
        """Remove all existing inventory data while preserving structure"""
        models_to_clean = [
            (RestockRequest, 'Restock Requests'),
            (StoreStockTransferRequest, 'Transfer Requests'),
            (PurchaseOrder, 'Purchase Orders'),
            (Stock, 'Store Stocks'),
            (WarehouseProduct, 'Warehouse Products'),
            (Product, 'Products'),
            (Supplier, 'Suppliers'),
        ]

        for model, name in models_to_clean:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'   🗑️  Deleted {count} {name}')

    def create_suppliers(self):
        """Create 5 specialized suppliers"""
        suppliers_data = [
            {
                'name': 'AquaFlow Plumbing Supplies',
                'contact_person': 'Ahmed Hassan',
                'email': 'ahmed@aquaflow.et',
                'phone': '+251911234567',
                'address': 'Merkato, Addis Ababa'
            },
            {
                'name': 'PowerLine Electrical Co.',
                'contact_person': 'Meron Tadesse',
                'email': 'meron@powerline.et',
                'phone': '+251922345678',
                'address': 'Piassa, Addis Ababa'
            },
            {
                'name': 'SolidBuild Cement & Masonry',
                'contact_person': 'Dawit Bekele',
                'email': 'dawit@solidbuild.et',
                'phone': '+251933456789',
                'address': 'Kaliti, Addis Ababa'
            },
            {
                'name': 'ToolMaster Hardware',
                'contact_person': 'Sara Alemayehu',
                'email': 'sara@toolmaster.et',
                'phone': '+251944567890',
                'address': 'Bole, Addis Ababa'
            },
            {
                'name': 'ColorCraft Paint & Finishing',
                'contact_person': 'Yohannes Girma',
                'email': 'yohannes@colorcraft.et',
                'phone': '+251955678901',
                'address': 'CMC, Addis Ababa'
            }
        ]

        suppliers = []
        for data in suppliers_data:
            supplier = Supplier.objects.create(**data)
            suppliers.append(supplier)
            self.stdout.write(f'   ✅ Created supplier: {supplier.name}')

        return suppliers

    def create_product_catalog(self, suppliers):
        """Create 8-10 products for each supplier"""
        products_data = {
            'AquaFlow Plumbing Supplies': [
                ('PVC Pipe 4 inch x 3m', 'High-quality PVC pipe for drainage systems', 'Pipes', 450.00),
                ('Copper Pipe 1/2 inch x 3m', 'Premium copper pipe for water supply', 'Pipes', 850.00),
                ('Ball Valve 1 inch', 'Brass ball valve with lever handle', 'Valves', 320.00),
                ('Gate Valve 3/4 inch', 'Heavy-duty gate valve for water control', 'Valves', 280.00),
                ('PVC Elbow 90° 2 inch', 'PVC elbow fitting for pipe connections', 'Fittings', 45.00),
                ('Pipe Coupling 1 inch', 'Threaded pipe coupling for connections', 'Fittings', 65.00),
                ('Toilet Flush Tank', 'Complete toilet flush tank assembly', 'Fixtures', 1250.00),
                ('Kitchen Sink Faucet', 'Stainless steel kitchen faucet with spray', 'Fixtures', 980.00),
                ('Shower Head Deluxe', 'Multi-function shower head with hose', 'Fixtures', 650.00),
            ],
            'PowerLine Electrical Co.': [
                ('Electrical Wire 2.5mm² x 100m', 'Copper electrical wire for house wiring', 'Wires', 1200.00),
                ('Coaxial Cable RG6 x 100m', 'High-quality coaxial cable for TV/Internet', 'Cables', 850.00),
                ('Light Switch Double', 'Modern double light switch with LED indicator', 'Switches', 125.00),
                ('Power Outlet 3-Pin', 'Grounded power outlet with safety cover', 'Outlets', 85.00),
                ('Circuit Breaker 20A', '20 Amp circuit breaker for electrical panels', 'Breakers', 180.00),
                ('LED Bulb 12W', 'Energy-efficient LED bulb warm white', 'Lighting', 95.00),
                ('Fluorescent Tube 40W', 'Standard fluorescent tube for office lighting', 'Lighting', 65.00),
                ('Electrical Conduit 20mm x 3m', 'PVC electrical conduit for wire protection', 'Conduits', 120.00),
                ('Junction Box 4x4', 'Electrical junction box with cover', 'Accessories', 45.00),
            ],
            'SolidBuild Cement & Masonry': [
                ('Portland Cement 50kg', 'High-grade Portland cement for construction', 'Cement', 380.00),
                ('Concrete Block 20x20x40cm', 'Standard concrete block for walls', 'Blocks', 25.00),
                ('Red Brick Standard', 'Traditional red clay brick for construction', 'Bricks', 8.50),
                ('Mortar Mix 25kg', 'Ready-mix mortar for masonry work', 'Mortar', 180.00),
                ('Rebar 12mm x 12m', 'Steel reinforcement bar for concrete', 'Reinforcement', 450.00),
                ('Concrete Admixture 5L', 'Chemical admixture for concrete strength', 'Additives', 320.00),
                ('Gravel 20mm - 1 ton', 'Crushed gravel for concrete aggregate', 'Aggregates', 850.00),
                ('Sand Fine - 1 ton', 'Fine sand for mortar and concrete', 'Aggregates', 650.00),
                ('Waterproofing Membrane', 'Bitumen waterproofing membrane roll', 'Waterproofing', 1200.00),
            ],
            'ToolMaster Hardware': [
                ('Hammer Claw 16oz', 'Professional claw hammer with fiberglass handle', 'Tools', 280.00),
                ('Screwdriver Set 6pc', 'Phillips and flathead screwdriver set', 'Tools', 450.00),
                ('Drill Bit Set HSS', 'High-speed steel drill bit set 1-10mm', 'Tools', 380.00),
                ('Bolt M10x50mm Galvanized', 'Galvanized hex bolt with nut and washer', 'Fasteners', 12.00),
                ('Screw Wood 4x50mm', 'Phillips head wood screw zinc plated', 'Fasteners', 3.50),
                ('Nail Common 3 inch', 'Common construction nail galvanized', 'Fasteners', 2.80),
                ('Padlock Heavy Duty 50mm', 'Weather-resistant padlock with 3 keys', 'Security', 180.00),
                ('Chain Link 6mm x 1m', 'Galvanized steel chain for security', 'Security', 85.00),
                ('Measuring Tape 5m', 'Steel measuring tape with magnetic tip', 'Measuring', 120.00),
            ],
            'ColorCraft Paint & Finishing': [
                ('Interior Paint White 4L', 'Premium interior wall paint washable', 'Paint', 680.00),
                ('Exterior Paint Blue 4L', 'Weather-resistant exterior paint', 'Paint', 750.00),
                ('Wood Stain Mahogany 1L', 'Oil-based wood stain for furniture', 'Stains', 320.00),
                ('Paint Brush 2 inch', 'Professional paint brush natural bristles', 'Brushes', 85.00),
                ('Paint Roller 9 inch', 'Paint roller with replaceable sleeve', 'Rollers', 120.00),
                ('Primer Sealer 4L', 'Universal primer sealer for all surfaces', 'Primers', 580.00),
                ('Sandpaper 120 Grit', 'Medium grit sandpaper for surface prep', 'Abrasives', 25.00),
                ('Masking Tape 2 inch', 'High-quality masking tape for painting', 'Accessories', 45.00),
                ('Paint Thinner 1L', 'Paint thinner for oil-based paints', 'Solvents', 180.00),
            ]
        }

        all_products = []
        for supplier in suppliers:
            if supplier.name in products_data:
                for name, description, category, price in products_data[supplier.name]:
                    product = Product.objects.create(
                        name=name,
                        description=description,
                        category=category,
                        price=Decimal(str(price)),
                        supplier_company=supplier.name,
                        material='Construction Material'
                    )
                    all_products.append(product)
                    self.stdout.write(f'   📦 Created: {product.name} - ETB {price}')

        return all_products

    def initialize_warehouse_stock(self, products, suppliers):
        """Stock all products in the Head Manager's warehouse"""
        # Get or create the main warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Main Construction Warehouse',
            defaults={
                'address': 'Industrial Zone, Addis Ababa',
                'phone_number': '+251911000000',
                'capacity': 10000
            }
        )

        if created:
            self.stdout.write(f'   🏭 Created warehouse: {warehouse.name}')
        else:
            self.stdout.write(f'   🏭 Using existing warehouse: {warehouse.name}')

        # Stock each product in the warehouse with realistic quantities
        for product in products:
            # Generate realistic stock quantities based on product type
            if 'ton' in product.name.lower():
                quantity = random.randint(5, 20)  # Bulk materials
            elif any(word in product.name.lower() for word in ['cement', 'paint', 'wire', 'cable']):
                quantity = random.randint(50, 200)  # Medium volume items
            elif any(word in product.name.lower() for word in ['bolt', 'screw', 'nail']):
                quantity = random.randint(500, 2000)  # Small fasteners
            else:
                quantity = random.randint(20, 100)  # Standard items

            # Determine warehouse location based on category
            location_mapping = {
                'Pipes': f'Aisle A, Section {random.randint(1, 5)}',
                'Valves': f'Aisle A, Shelf {random.randint(1, 10)}',
                'Fittings': f'Aisle A, Shelf {random.randint(1, 10)}',
                'Fixtures': f'Aisle A, Section {random.randint(1, 5)}',
                'Wires': f'Aisle B, Section {random.randint(1, 5)}',
                'Cables': f'Aisle B, Section {random.randint(1, 5)}',
                'Switches': f'Aisle B, Shelf {random.randint(1, 10)}',
                'Outlets': f'Aisle B, Shelf {random.randint(1, 10)}',
                'Breakers': f'Aisle B, Shelf {random.randint(1, 10)}',
                'Lighting': f'Aisle B, Shelf {random.randint(1, 10)}',
                'Conduits': f'Aisle B, Section {random.randint(1, 5)}',
                'Accessories': f'Aisle B, Shelf {random.randint(1, 10)}',
                'Cement': f'Yard Area {random.randint(1, 3)}',
                'Blocks': f'Yard Area {random.randint(1, 3)}',
                'Bricks': f'Yard Area {random.randint(1, 3)}',
                'Mortar': f'Aisle C, Section {random.randint(1, 5)}',
                'Reinforcement': f'Yard Area {random.randint(1, 3)}',
                'Additives': f'Aisle C, Shelf {random.randint(1, 10)}',
                'Aggregates': f'Yard Area {random.randint(1, 3)}',
                'Waterproofing': f'Aisle C, Section {random.randint(1, 5)}',
                'Tools': f'Aisle D, Shelf {random.randint(1, 10)}',
                'Fasteners': f'Aisle D, Shelf {random.randint(1, 10)}',
                'Security': f'Aisle D, Shelf {random.randint(1, 10)}',
                'Measuring': f'Aisle D, Shelf {random.randint(1, 10)}',
                'Paint': f'Aisle E, Section {random.randint(1, 5)}',
                'Stains': f'Aisle E, Shelf {random.randint(1, 10)}',
                'Brushes': f'Aisle E, Shelf {random.randint(1, 10)}',
                'Rollers': f'Aisle E, Shelf {random.randint(1, 10)}',
                'Primers': f'Aisle E, Section {random.randint(1, 5)}',
                'Abrasives': f'Aisle E, Shelf {random.randint(1, 10)}',
                'Solvents': f'Aisle E, Section {random.randint(1, 5)}',
            }

            location = location_mapping.get(product.category, f'Aisle F, Section {random.randint(1, 5)}')

            # Find the supplier object based on the product's supplier_company
            supplier = None
            for s in suppliers:
                if s.name == product.supplier_company:
                    supplier = s
                    break

            if not supplier:
                supplier = suppliers[0]  # Fallback to first supplier

            # Generate unique product_id and sku
            product_id = f"WH-{product.id:04d}"
            sku = f"SKU-{product.category[:3].upper()}-{product.id:04d}"

            warehouse_product = WarehouseProduct.objects.create(
                warehouse=warehouse,
                product_id=product_id,
                product_name=product.name,
                category=product.category,
                supplier=supplier,
                quantity_in_stock=quantity,
                unit_price=product.price,
                warehouse_location=location,
                sku=sku
            )

            self.stdout.write(f'   📦 Stocked: {product.name} - Qty: {quantity} - Location: {location}')

    def create_testing_data(self):
        """Create sample restock requests and transfer requests for testing"""
        # Get required objects
        warehouse = Warehouse.objects.first()
        stores = Store.objects.all()
        products = Product.objects.all()[:10]  # Use first 10 products for testing

        # Get users
        head_manager = User.objects.filter(role='head_manager').first()
        store_managers = User.objects.filter(role='store_manager')

        if not all([warehouse, stores.exists(), products, head_manager, store_managers.exists()]):
            self.stdout.write('   ⚠️  Missing required data for testing. Skipping test data creation.')
            return

        # Create sample restock requests in various states
        restock_states = ['pending', 'approved', 'shipped', 'received']

        for i, state in enumerate(restock_states):
            if i < len(products) and store_managers.exists():
                product = products[i]
                store = stores[i % stores.count()]
                store_manager = store_managers[i % store_managers.count()]

                restock_request = RestockRequest.objects.create(
                    store=store,
                    product=product,
                    requested_by=store_manager,
                    requested_quantity=random.randint(10, 50),
                    current_stock=random.randint(0, 10),
                    priority=random.choice(['low', 'medium', 'high']),
                    reason=f'Sample {state} restock request for testing inventory system',
                    status=state
                )

                if state in ['approved', 'shipped', 'received']:
                    restock_request.approved_quantity = restock_request.requested_quantity
                    restock_request.reviewed_by = head_manager
                    restock_request.save()

                if state in ['shipped', 'received']:
                    restock_request.ship(
                        shipped_by=head_manager,
                        shipped_quantity=restock_request.approved_quantity,
                        tracking_number=f'TRACK-{random.randint(1000, 9999)}'
                    )

                if state == 'received':
                    restock_request.receive(
                        received_by=store_manager,
                        received_quantity=restock_request.shipped_quantity,
                        notes='Sample received request for testing'
                    )

                self.stdout.write(f'   📋 Created {state} restock request: {restock_request.request_number}')

        # Create sample stock transfer requests
        if stores.count() >= 2:
            for i in range(3):
                if i < len(products):
                    product = products[i + 4]  # Use different products
                    from_store = stores[0]
                    to_store = stores[1]
                    store_manager = store_managers.first()

                    transfer_request = StoreStockTransferRequest.objects.create(
                        product=product,
                        from_store=from_store,
                        to_store=to_store,
                        requested_by=store_manager,
                        requested_quantity=random.randint(5, 20),
                        priority=random.choice(['low', 'medium', 'high']),
                        reason=f'Sample transfer request {i+1} for testing',
                        status=random.choice(['pending', 'approved', 'completed'])
                    )

                    self.stdout.write(f'   🔄 Created transfer request: {transfer_request.request_number}')

    def display_summary(self):
        """Display summary of created data"""
        self.stdout.write('\n📊 INVENTORY ECOSYSTEM SUMMARY')
        self.stdout.write('-' * 40)

        # Count created objects
        supplier_count = Supplier.objects.count()
        product_count = Product.objects.count()
        warehouse_product_count = WarehouseProduct.objects.count()
        restock_count = RestockRequest.objects.count()
        transfer_count = StoreStockTransferRequest.objects.count()

        self.stdout.write(f'🏢 Suppliers Created: {supplier_count}')
        self.stdout.write(f'📦 Products Created: {product_count}')
        self.stdout.write(f'🏭 Warehouse Products: {warehouse_product_count}')
        self.stdout.write(f'📋 Restock Requests: {restock_count}')
        self.stdout.write(f'🔄 Transfer Requests: {transfer_count}')

        # Display supplier breakdown
        self.stdout.write('\n🏢 SUPPLIER BREAKDOWN:')
        for supplier in Supplier.objects.all():
            product_count = Product.objects.filter(supplier_company=supplier.name).count()
            self.stdout.write(f'   • {supplier.name}: {product_count} products')

        self.stdout.write('\n✅ System is ready for synchronized inventory management!')
        self.stdout.write('💡 Head Manager can now manage central warehouse inventory')
        self.stdout.write('💡 Store Managers can submit restock requests')
        self.stdout.write('💡 All inventory movements are tracked and synchronized')
