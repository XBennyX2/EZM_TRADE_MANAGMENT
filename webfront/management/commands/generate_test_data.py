from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

from store.models import Store
from Inventory.models import Product, Stock
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Generate test data for webfront app testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stores',
            type=int,
            default=5,
            help='Number of stores to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before generating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test data...')
            Stock.objects.all().delete()
            Product.objects.all().delete()
            Store.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        with transaction.atomic():
            # Create stores
            stores = self.create_stores(options['stores'])
            self.stdout.write(f'Created {len(stores)} stores')

            # Create products
            products = self.create_products(options['products'])
            self.stdout.write(f'Created {len(products)} products')

            # Create stock entries
            stock_count = self.create_stock_entries(stores, products)
            self.stdout.write(f'Created {stock_count} stock entries')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated test data: {len(stores)} stores, '
                f'{len(products)} products, {stock_count} stock entries'
            )
        )

    def create_stores(self, count):
        stores = []
        store_names = [
            'Downtown Branch', 'Mall Location', 'Airport Store', 'City Center',
            'Suburban Outlet', 'Express Store', 'Flagship Store', 'Corner Shop',
            'Market Square', 'Shopping Plaza', 'Business District', 'Riverside Branch'
        ]
        
        addresses = [
            '123 Main Street, Downtown', '456 Mall Avenue, Shopping Center',
            '789 Airport Road, Terminal 1', '321 City Center Blvd',
            '654 Suburban Lane, Residential Area', '987 Express Way, Quick Stop',
            '147 Flagship Drive, Premium Location', '258 Corner Street, Local Area',
            '369 Market Square, Traditional Market', '741 Plaza Circle, Shopping Complex',
            '852 Business Ave, Corporate District', '963 Riverside Drive, Scenic Location'
        ]

        phone_numbers = [
            '+251-11-123-4567', '+251-11-234-5678', '+251-11-345-6789',
            '+251-11-456-7890', '+251-11-567-8901', '+251-11-678-9012',
            '+251-11-789-0123', '+251-11-890-1234', '+251-11-901-2345',
            '+251-11-012-3456', '+251-11-123-4567', '+251-11-234-5678'
        ]

        for i in range(count):
            store = Store.objects.create(
                name=store_names[i % len(store_names)],
                address=addresses[i % len(addresses)],
                phone_number=phone_numbers[i % len(phone_numbers)]
            )
            stores.append(store)

        return stores

    def create_products(self, count):
        products = []
        
        categories = [
            'Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors',
            'Books & Media', 'Health & Beauty', 'Toys & Games', 'Automotive',
            'Food & Beverages', 'Office Supplies'
        ]

        product_templates = {
            'Electronics': [
                ('Smartphone', 'Latest model smartphone with advanced features'),
                ('Laptop', 'High-performance laptop for work and gaming'),
                ('Headphones', 'Wireless noise-canceling headphones'),
                ('Tablet', 'Portable tablet for entertainment and productivity'),
                ('Smart Watch', 'Fitness tracking smartwatch'),
            ],
            'Clothing': [
                ('T-Shirt', 'Comfortable cotton t-shirt'),
                ('Jeans', 'Classic denim jeans'),
                ('Sneakers', 'Comfortable running sneakers'),
                ('Jacket', 'Stylish casual jacket'),
                ('Dress', 'Elegant evening dress'),
            ],
            'Home & Garden': [
                ('Coffee Maker', 'Automatic drip coffee maker'),
                ('Garden Tools', 'Complete gardening tool set'),
                ('Bedding Set', 'Luxury cotton bedding set'),
                ('Kitchen Knife', 'Professional chef knife'),
                ('Plant Pot', 'Decorative ceramic plant pot'),
            ],
            'Sports & Outdoors': [
                ('Basketball', 'Official size basketball'),
                ('Yoga Mat', 'Non-slip exercise yoga mat'),
                ('Camping Tent', 'Waterproof camping tent'),
                ('Bicycle', 'Mountain bike for outdoor adventures'),
                ('Fitness Tracker', 'Activity monitoring device'),
            ],
            'Books & Media': [
                ('Novel', 'Bestselling fiction novel'),
                ('Cookbook', 'International cuisine cookbook'),
                ('DVD Movie', 'Popular movie on DVD'),
                ('Magazine', 'Monthly lifestyle magazine'),
                ('Educational Book', 'Academic textbook'),
            ]
        }

        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        variations = ['Red', 'Blue', 'Green', 'Black', 'White', 'Gray', 'Brown']
        materials = ['Cotton', 'Polyester', 'Leather', 'Metal', 'Plastic', 'Wood', 'Glass']

        for i in range(count):
            category = random.choice(categories)
            if category in product_templates:
                name, description = random.choice(product_templates[category])
            else:
                name = f'Product {i+1}'
                description = f'Description for product {i+1}'

            # Add variation to make products unique
            if random.choice([True, False]):
                variation = random.choice(variations)
                name = f'{name} - {variation}'

            product = Product.objects.create(
                name=name,
                category=category,
                description=description,
                price=Decimal(str(random.uniform(10, 1000))).quantize(Decimal('0.01')),
                material=random.choice(materials),
                size=random.choice(sizes) if random.choice([True, False]) else None,
                variation=random.choice(variations) if random.choice([True, False]) else None,
                supplier_company=f'Supplier {random.randint(1, 10)}',
                batch_number=f'BATCH{random.randint(1000, 9999)}',
                expiry_date=datetime.now().date() + timedelta(days=random.randint(30, 365)),
                room=f'Room {random.randint(1, 10)}',
                shelf=f'Shelf {random.randint(1, 20)}',
                floor=random.randint(1, 5),
                storing_condition=random.choice([
                    'room_temperature', 'cool_dry_place', 'moisture_free',
                    'temperature_sensitive', 'electrical_safe'
                ])
            )
            products.append(product)

        return products

    def create_stock_entries(self, stores, products):
        stock_count = 0

        for store in stores:
            # Each store will have 60-80% of all products
            products_for_store = random.sample(
                products,
                random.randint(int(len(products) * 0.6), int(len(products) * 0.8))
            )

            for product in products_for_store:
                # Generate realistic stock quantities
                # Some items will be low stock, some medium, some high
                stock_level_type = random.choices(
                    ['low', 'medium', 'high'],
                    weights=[20, 30, 50],  # 20% low, 30% medium, 50% high stock
                    k=1
                )[0]

                if stock_level_type == 'low':
                    quantity = random.randint(1, 15)
                    threshold = random.randint(10, 20)
                elif stock_level_type == 'medium':
                    quantity = random.randint(20, 60)
                    threshold = random.randint(15, 25)
                else:  # high
                    quantity = random.randint(70, 200)
                    threshold = random.randint(20, 30)

                # Calculate selling price (cost price + margin)
                cost_price = product.price
                margin_percentage = Decimal(str(random.uniform(0.2, 0.8)))  # 20-80% margin
                selling_price = cost_price * (Decimal('1') + margin_percentage)
                selling_price = selling_price.quantize(Decimal('0.01'))

                Stock.objects.create(
                    product=product,
                    store=store,
                    quantity=quantity,
                    low_stock_threshold=threshold,
                    selling_price=selling_price
                )
                stock_count += 1

        return stock_count
