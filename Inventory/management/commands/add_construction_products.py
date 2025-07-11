from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from Inventory.models import (
    Product, WarehouseProduct, Warehouse, Supplier, Stock
)
from store.models import Store
import random


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

        # Create or get default supplier
        supplier, created = Supplier.objects.get_or_create(
            name='Construction Materials Ltd',
            defaults={
                'contact_person': 'Mike Builder',
                'email': 'mike@constructionmaterials.com',
                'phone': '+1-555-0456',
                'address': '456 Builder St, Industrial Zone',
                'is_active': True
            }
        )

        # Construction products data
        construction_products = [
            # Cement and Concrete
            {
                'name': 'Portland Cement Bag 50kg',
                'category': 'cement',
                'description': 'High-quality Portland cement for construction projects',
                'price': Decimal('12.50'),
                'material': 'Portland cement',
                'size': '50kg',
                'variation': 'Type I',
                'product_type': 'raw_material',
                'batch_number': 'CEM001',
                'storing_condition': 'dry',
                'warehouse_quantity': 500,
                'unit_price': Decimal('10.00'),
                'sku': 'CEM-PORT-50KG',
                'barcode': '1234567890123',
                'weight': Decimal('50.00'),
                'dimensions': '60x40x15 cm',
                'warehouse_location': 'Aisle A, Shelf 1',
                'min_stock': 50,
                'max_stock': 1000,
                'reorder_point': 100
            },
            {
                'name': 'Ready Mix Concrete m³',
                'category': 'concrete',
                'description': 'Ready-to-use concrete mix for foundations and structures',
                'price': Decimal('85.00'),
                'material': 'Concrete mix',
                'size': '1m³',
                'variation': 'C25/30',
                'product_type': 'finished_product',
                'batch_number': 'CON001',
                'storing_condition': 'room_temperature',
                'warehouse_quantity': 50,
                'unit_price': Decimal('75.00'),
                'sku': 'CON-RDY-1M3',
                'barcode': '1234567890124',
                'weight': Decimal('2400.00'),
                'dimensions': '1x1x1 m',
                'warehouse_location': 'Yard Area A',
                'min_stock': 10,
                'max_stock': 100,
                'reorder_point': 20
            },
            # Steel and Metal
            {
                'name': 'Steel Rebar 12mm x 6m',
                'category': 'steel',
                'description': 'High-strength steel reinforcement bars for concrete structures',
                'price': Decimal('25.00'),
                'material': 'Carbon steel',
                'size': '12mm x 6m',
                'variation': 'Grade 60',
                'product_type': 'raw_material',
                'batch_number': 'STL001',
                'storing_condition': 'dry',
                'warehouse_quantity': 200,
                'unit_price': Decimal('22.00'),
                'sku': 'STL-RBR-12MM',
                'barcode': '1234567890125',
                'weight': Decimal('5.33'),
                'dimensions': '600x1.2x1.2 cm',
                'warehouse_location': 'Aisle B, Rack 1',
                'min_stock': 30,
                'max_stock': 500,
                'reorder_point': 60
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
                    supplier_company=supplier,
                    batch_number=product_data['batch_number'],
                    storing_condition=product_data['storing_condition']
                )

                # Create WarehouseProduct
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
                    supplier=supplier,
                    warehouse=warehouse
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
