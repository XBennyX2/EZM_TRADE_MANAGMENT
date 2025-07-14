from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from Inventory.models import (
    Product, WarehouseProduct, Warehouse, Supplier, Stock
)
from store.models import Store
import random
import uuid


class Command(BaseCommand):
    help = 'Add sample construction products to the warehouse inventory'

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

        # Create or get default warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            name='Main Construction Warehouse',
            defaults={
                'address': '123 Industrial Ave, Construction District',
                'phone': '+1-555-0123',
                'email': 'warehouse@ezmtrade.com',
                'manager_name': 'John Warehouse',
                'capacity': 10000,
                'current_utilization': 0,
                'is_active': True
            }
        )

        # Get suppliers or create default ones
        suppliers = {}
        supplier_names = [
            'Dangote Cement Ethiopia',
            'Ethiopian Steel Corporation',
            'Addis Tiles & Ceramics',
            'Crown Paints Ethiopia',
            'Electrical Supply House Ethiopia',
            'Plumbing Solutions Ethiopia',
            'Derba Cement Share Company',
            'Bricks & Blocks Manufacturing'
        ]

        for supplier_name in supplier_names:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_name,
                defaults={
                    'contact_person': 'Contact Person',
                    'email': f'contact@{supplier_name.lower().replace(" ", "")}.com',
                    'phone': '+251-11-123-4567',
                    'address': 'Addis Ababa, Ethiopia',
                    'is_active': True
                }
            )
            suppliers[supplier_name] = supplier

        # Construction products data with Ethiopian suppliers
        construction_products = [
            # Dangote Cement Products
            {
                'name': 'Dangote Portland Cement 50kg',
                'category': 'cement',
                'description': 'Premium Portland cement from Dangote Ethiopia',
                'price': Decimal('850.00'),  # ETB
                'material': 'Portland cement',
                'size': '50kg',
                'variation': 'Type I',
                'product_type': 'raw_material',
                'batch_number': f'DNG{timezone.now().strftime("%Y%m")}001',
                'storing_condition': 'dry',
                'warehouse_quantity': 800,
                'unit_price': Decimal('750.00'),
                'sku': 'DNG-CEM-50KG',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('50.00'),
                'dimensions': '60x40x15 cm',
                'warehouse_location': 'Aisle A, Section 1',
                'min_stock': 100,
                'max_stock': 2000,
                'reorder_point': 200,
                'supplier_name': 'Dangote Cement Ethiopia'
            },
            {
                'name': 'Derba Portland Cement 50kg',
                'category': 'cement',
                'description': 'High-quality Portland cement from Derba Cement',
                'price': Decimal('820.00'),  # ETB
                'material': 'Portland cement',
                'size': '50kg',
                'variation': 'Type I',
                'product_type': 'raw_material',
                'batch_number': f'DRB{timezone.now().strftime("%Y%m")}001',
                'storing_condition': 'dry',
                'warehouse_quantity': 600,
                'unit_price': Decimal('720.00'),
                'sku': 'DRB-CEM-50KG',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('50.00'),
                'dimensions': '60x40x15 cm',
                'warehouse_location': 'Aisle A, Section 2',
                'min_stock': 80,
                'max_stock': 1500,
                'reorder_point': 150,
                'supplier_name': 'Derba Cement Share Company'
            },
            # Ethiopian Steel Corporation Products
            {
                'name': 'Steel Rebar 8mm x 12m',
                'category': 'steel',
                'description': 'High-strength steel reinforcement bars from Ethiopian Steel Corp',
                'price': Decimal('450.00'),  # ETB
                'material': 'Carbon steel',
                'size': '8mm x 12m',
                'variation': 'Grade 60',
                'product_type': 'raw_material',
                'batch_number': f'ESC{timezone.now().strftime("%Y%m")}001',
                'storing_condition': 'dry',
                'warehouse_quantity': 500,
                'unit_price': Decimal('400.00'),
                'sku': 'ESC-RBR-8MM',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('4.74'),
                'dimensions': '1200x0.8x0.8 cm',
                'warehouse_location': 'Aisle B, Section 1',
                'min_stock': 100,
                'max_stock': 1000,
                'reorder_point': 200,
                'supplier_name': 'Ethiopian Steel Corporation'
            },
            {
                'name': 'Steel Rebar 12mm x 12m',
                'category': 'steel',
                'description': 'Medium-duty steel reinforcement bars',
                'price': Decimal('680.00'),  # ETB
                'material': 'Carbon steel',
                'size': '12mm x 12m',
                'variation': 'Grade 60',
                'product_type': 'raw_material',
                'batch_number': f'ESC{timezone.now().strftime("%Y%m")}002',
                'storing_condition': 'dry',
                'warehouse_quantity': 400,
                'unit_price': Decimal('620.00'),
                'sku': 'ESC-RBR-12MM',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('10.65'),
                'dimensions': '1200x1.2x1.2 cm',
                'warehouse_location': 'Aisle B, Section 2',
                'min_stock': 80,
                'max_stock': 800,
                'reorder_point': 150,
                'supplier_name': 'Ethiopian Steel Corporation'
            },
            {
                'name': 'Steel Rebar 16mm x 12m',
                'category': 'steel',
                'description': 'Heavy-duty steel reinforcement bars',
                'price': Decimal('1200.00'),  # ETB
                'material': 'Carbon steel',
                'size': '16mm x 12m',
                'variation': 'Grade 60',
                'product_type': 'raw_material',
                'batch_number': f'ESC{timezone.now().strftime("%Y%m")}003',
                'storing_condition': 'dry',
                'warehouse_quantity': 300,
                'unit_price': Decimal('1100.00'),
                'sku': 'ESC-RBR-16MM',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('18.94'),
                'dimensions': '1200x1.6x1.6 cm',
                'warehouse_location': 'Aisle B, Section 3',
                'min_stock': 60,
                'max_stock': 600,
                'reorder_point': 120,
                'supplier_name': 'Ethiopian Steel Corporation'
            },
            # Addis Tiles & Ceramics Products
            {
                'name': 'Ceramic Floor Tiles 60x60cm',
                'category': 'tiles',
                'description': 'Premium ceramic floor tiles from Addis Tiles',
                'price': Decimal('180.00'),  # ETB per piece
                'material': 'Ceramic',
                'size': '60x60cm',
                'variation': 'Polished',
                'product_type': 'finished_product',
                'batch_number': f'ATC{timezone.now().strftime("%Y%m")}001',
                'storing_condition': 'dry',
                'warehouse_quantity': 1200,
                'unit_price': Decimal('150.00'),
                'sku': 'ATC-CER-60X60',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('2.50'),
                'dimensions': '60x60x1 cm',
                'warehouse_location': 'Aisle C, Section 1',
                'min_stock': 200,
                'max_stock': 2000,
                'reorder_point': 400,
                'supplier_name': 'Addis Tiles & Ceramics'
            },
            {
                'name': 'Porcelain Wall Tiles 30x60cm',
                'category': 'tiles',
                'description': 'High-quality porcelain wall tiles',
                'price': Decimal('220.00'),  # ETB per piece
                'material': 'Porcelain',
                'size': '30x60cm',
                'variation': 'Matte finish',
                'product_type': 'finished_product',
                'batch_number': f'ATC{timezone.now().strftime("%Y%m")}002',
                'storing_condition': 'dry',
                'warehouse_quantity': 800,
                'unit_price': Decimal('190.00'),
                'sku': 'ATC-POR-30X60',
                'barcode': f'251{random.randint(1000000000, 9999999999)}',
                'weight': Decimal('1.80'),
                'dimensions': '30x60x1 cm',
                'warehouse_location': 'Aisle C, Section 2',
                'min_stock': 150,
                'max_stock': 1500,
                'reorder_point': 300,
                'supplier_name': 'Addis Tiles & Ceramics'
            },
            {
                'name': 'Steel I-Beam 200mm x 6m',
                'category': 'steel',
                'description': 'Structural steel I-beam for construction frameworks',
                'price': Decimal('180.00'),
                'material': 'Structural steel',
                'size': '200mm x 6m',
                'variation': 'S275',
                'product_type': 'raw_material',
                'batch_number': 'STL002',
                'storing_condition': 'dry',
                'warehouse_quantity': 25,
                'unit_price': Decimal('165.00'),
                'sku': 'STL-IBM-200MM',
                'barcode': '1234567890126',
                'weight': Decimal('178.20'),
                'dimensions': '600x20x10 cm',
                'warehouse_location': 'Aisle B, Rack 2',
                'min_stock': 5,
                'max_stock': 50,
                'reorder_point': 10
            },
            # Bricks and Blocks
            {
                'name': 'Red Clay Bricks (per 1000)',
                'category': 'bricks',
                'description': 'Traditional red clay bricks for wall construction',
                'price': Decimal('450.00'),
                'material': 'Clay',
                'size': '230x110x76mm',
                'variation': 'Standard',
                'product_type': 'finished_product',
                'batch_number': 'BRK001',
                'storing_condition': 'dry',
                'warehouse_quantity': 10,
                'unit_price': Decimal('400.00'),
                'sku': 'BRK-CLY-1000',
                'barcode': '1234567890127',
                'weight': Decimal('3500.00'),
                'dimensions': '120x80x60 cm (pallet)',
                'warehouse_location': 'Yard Area B',
                'min_stock': 2,
                'max_stock': 20,
                'reorder_point': 4
            },
            {
                'name': 'Concrete Blocks 200mm',
                'category': 'blocks',
                'description': 'Hollow concrete blocks for structural walls',
                'price': Decimal('3.50'),
                'material': 'Concrete',
                'size': '200x200x400mm',
                'variation': 'Hollow',
                'product_type': 'finished_product',
                'batch_number': 'BLK001',
                'storing_condition': 'dry',
                'warehouse_quantity': 800,
                'unit_price': Decimal('3.00'),
                'sku': 'BLK-CON-200MM',
                'barcode': '1234567890128',
                'weight': Decimal('18.50'),
                'dimensions': '40x20x20 cm',
                'warehouse_location': 'Aisle C, Stack 1',
                'min_stock': 100,
                'max_stock': 1500,
                'reorder_point': 200
            },
            # Paint and Coatings
            {
                'name': 'Exterior Wall Paint 20L',
                'category': 'paint',
                'description': 'Weather-resistant exterior wall paint',
                'price': Decimal('85.00'),
                'material': 'Acrylic paint',
                'size': '20L',
                'variation': 'White',
                'product_type': 'finished_product',
                'batch_number': 'PNT001',
                'storing_condition': 'room_temperature',
                'warehouse_quantity': 60,
                'unit_price': Decimal('75.00'),
                'sku': 'PNT-EXT-20L',
                'barcode': '1234567890129',
                'weight': Decimal('22.00'),
                'dimensions': '30x30x35 cm',
                'warehouse_location': 'Aisle D, Shelf 1',
                'min_stock': 10,
                'max_stock': 100,
                'reorder_point': 20
            },
            {
                'name': 'Primer Sealer 5L',
                'category': 'paint',
                'description': 'Multi-surface primer and sealer',
                'price': Decimal('35.00'),
                'material': 'Acrylic primer',
                'size': '5L',
                'variation': 'Clear',
                'product_type': 'finished_product',
                'batch_number': 'PNT002',
                'storing_condition': 'room_temperature',
                'warehouse_quantity': 40,
                'unit_price': Decimal('30.00'),
                'sku': 'PNT-PRM-5L',
                'barcode': '1234567890130',
                'weight': Decimal('5.50'),
                'dimensions': '20x20x25 cm',
                'warehouse_location': 'Aisle D, Shelf 2',
                'min_stock': 8,
                'max_stock': 80,
                'reorder_point': 15
            },
            # Electrical Materials
            {
                'name': 'Electrical Wire 2.5mm² 100m',
                'category': 'electrical',
                'description': 'PVC insulated copper electrical wire',
                'price': Decimal('120.00'),
                'material': 'Copper with PVC insulation',
                'size': '2.5mm² x 100m',
                'variation': 'Red',
                'product_type': 'raw_material',
                'batch_number': 'ELC001',
                'storing_condition': 'dry',
                'warehouse_quantity': 30,
                'unit_price': Decimal('110.00'),
                'sku': 'ELC-WIR-2.5MM',
                'barcode': '1234567890131',
                'weight': Decimal('18.50'),
                'dimensions': '35x35x15 cm',
                'warehouse_location': 'Aisle E, Shelf 1',
                'min_stock': 5,
                'max_stock': 60,
                'reorder_point': 10
            },
            {
                'name': 'PVC Conduit Pipe 20mm x 3m',
                'category': 'electrical',
                'description': 'PVC electrical conduit pipe for cable protection',
                'price': Decimal('8.50'),
                'material': 'PVC',
                'size': '20mm x 3m',
                'variation': 'Grey',
                'product_type': 'finished_product',
                'batch_number': 'ELC002',
                'storing_condition': 'room_temperature',
                'warehouse_quantity': 150,
                'unit_price': Decimal('7.50'),
                'sku': 'ELC-CON-20MM',
                'barcode': '1234567890132',
                'weight': Decimal('0.85'),
                'dimensions': '300x2x2 cm',
                'warehouse_location': 'Aisle E, Rack 1',
                'min_stock': 20,
                'max_stock': 300,
                'reorder_point': 40
            },
            # Plumbing Materials
            {
                'name': 'PVC Pipe 110mm x 6m',
                'category': 'plumbing',
                'description': 'PVC drainage pipe for sewage systems',
                'price': Decimal('45.00'),
                'material': 'PVC',
                'size': '110mm x 6m',
                'variation': 'Orange',
                'product_type': 'finished_product',
                'batch_number': 'PLB001',
                'storing_condition': 'room_temperature',
                'warehouse_quantity': 80,
                'unit_price': Decimal('40.00'),
                'sku': 'PLB-PVC-110MM',
                'barcode': '1234567890133',
                'weight': Decimal('12.50'),
                'dimensions': '600x11x11 cm',
                'warehouse_location': 'Aisle F, Rack 1',
                'min_stock': 15,
                'max_stock': 150,
                'reorder_point': 30
            },
            {
                'name': 'Copper Pipe 22mm x 3m',
                'category': 'plumbing',
                'description': 'Copper pipe for water supply systems',
                'price': Decimal('35.00'),
                'material': 'Copper',
                'size': '22mm x 3m',
                'variation': 'Standard',
                'product_type': 'raw_material',
                'batch_number': 'PLB002',
                'storing_condition': 'dry',
                'warehouse_quantity': 60,
                'unit_price': Decimal('32.00'),
                'sku': 'PLB-COP-22MM',
                'barcode': '1234567890134',
                'weight': Decimal('1.85'),
                'dimensions': '300x2.2x2.2 cm',
                'warehouse_location': 'Aisle F, Shelf 1',
                'min_stock': 10,
                'max_stock': 120,
                'reorder_point': 20
            }
        ]

        self.stdout.write('Creating construction products...')
        
        with transaction.atomic():
            for product_data in construction_products:
                # Get the correct supplier for this product
                supplier_name = product_data.get('supplier_name', 'Dangote Cement Ethiopia')
                product_supplier = suppliers.get(supplier_name, suppliers['Dangote Cement Ethiopia'])

                # Create Product
                product = Product.objects.create(
                    name=product_data['name'],
                    category=product_data['category'],
                    description=product_data['description'],
                    price=product_data['price'],
                    material=product_data['material'],
                    size=product_data['size'],
                    variation=product_data['variation'],
                    product_type=product_data['product_type'],
                    supplier_company=product_supplier,
                    batch_number=product_data['batch_number'],
                    storing_condition=product_data['storing_condition']
                )

                # Create WarehouseProduct with FIFO fields
                warehouse_product = WarehouseProduct.objects.create(
                    product_id=product_data['sku'],
                    product_name=product_data['name'],
                    category=product_data['category'],
                    quantity_in_stock=product_data['warehouse_quantity'],
                    unit_price=product_data['unit_price'],
                    minimum_stock_level=product_data['min_stock'],
                    maximum_stock_level=product_data['max_stock'],
                    reorder_point=product_data['reorder_point'],
                    sku=product_data['sku'],
                    barcode=product_data['barcode'],
                    weight=product_data['weight'],
                    dimensions=product_data['dimensions'],
                    warehouse_location=product_data['warehouse_location'],
                    supplier=product_supplier,
                    warehouse=warehouse,
                    batch_number=product_data['batch_number'],
                    arrival_date=timezone.now()
                )

                # Create Stock entries for all stores
                stores = Store.objects.all()
                for store in stores:
                    # Random stock quantity between 10-50% of warehouse quantity
                    store_quantity = random.randint(
                        int(product_data['warehouse_quantity'] * 0.1),
                        int(product_data['warehouse_quantity'] * 0.5)
                    )
                    
                    Stock.objects.create(
                        product=product,
                        store=store,
                        quantity=store_quantity,
                        low_stock_threshold=product_data['min_stock'] // 2,
                        selling_price=product_data['price']
                    )

                self.stdout.write(f'Created: {product.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(construction_products)} construction products!'
            )
        )
