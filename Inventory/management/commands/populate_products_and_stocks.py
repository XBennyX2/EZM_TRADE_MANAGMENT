from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import Store
from Inventory.models import Product, Stock, Supplier
from decimal import Decimal
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Populate database with sample products and store stocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products and stocks before creating new ones'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing products and stocks...')
            Stock.objects.all().delete()
            Product.objects.all().delete()

        # Create sample products
        self.create_products(options['products'])
        
        # Create stocks for each store
        self.create_store_stocks()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with {options["products"]} products and store stocks!'
            )
        )

    def create_products(self, num_products):
        """Create sample products across different categories"""
        
        # Sample product data organized by category
        product_data = {
            'electronics': [
                {'name': 'Samsung Galaxy A54', 'desc': 'Latest Android smartphone with 128GB storage', 'price': 25000, 'material': 'Aluminum and Glass'},
                {'name': 'iPhone 14', 'desc': 'Apple iPhone with advanced camera system', 'price': 65000, 'material': 'Aluminum and Ceramic Shield'},
                {'name': 'Dell Laptop Inspiron 15', 'desc': 'Business laptop with Intel i5 processor', 'price': 45000, 'material': 'Plastic and Metal'},
                {'name': 'HP Printer LaserJet', 'desc': 'Wireless laser printer for office use', 'price': 8500, 'material': 'Plastic'},
                {'name': 'Sony Headphones WH-1000XM4', 'desc': 'Noise-canceling wireless headphones', 'price': 15000, 'material': 'Plastic and Metal'},
                {'name': 'Samsung 55" Smart TV', 'desc': '4K UHD Smart TV with HDR support', 'price': 35000, 'material': 'Plastic and Metal'},
                {'name': 'iPad Air', 'desc': 'Apple tablet with 64GB storage', 'price': 28000, 'material': 'Aluminum'},
                {'name': 'Canon DSLR Camera', 'desc': 'Professional camera with 24MP sensor', 'price': 42000, 'material': 'Metal and Plastic'},
            ],
            'clothing': [
                {'name': 'Men\'s Cotton T-Shirt', 'desc': 'Comfortable cotton t-shirt in various colors', 'price': 450, 'material': '100% Cotton'},
                {'name': 'Women\'s Jeans', 'desc': 'Slim fit denim jeans', 'price': 1200, 'material': 'Denim Cotton'},
                {'name': 'Leather Jacket', 'desc': 'Genuine leather jacket for men', 'price': 3500, 'material': 'Genuine Leather'},
                {'name': 'Running Shoes', 'desc': 'Athletic shoes for running and sports', 'price': 2800, 'material': 'Synthetic and Mesh'},
                {'name': 'Winter Coat', 'desc': 'Warm winter coat with hood', 'price': 4200, 'material': 'Polyester and Down'},
                {'name': 'Formal Shirt', 'desc': 'Business formal shirt for men', 'price': 850, 'material': 'Cotton Blend'},
                {'name': 'Summer Dress', 'desc': 'Light summer dress for women', 'price': 1800, 'material': 'Cotton and Polyester'},
                {'name': 'Sports Bra', 'desc': 'High-support sports bra', 'price': 650, 'material': 'Polyester and Spandex'},
            ],
            'home_garden': [
                {'name': 'Coffee Table', 'desc': 'Modern wooden coffee table', 'price': 5500, 'material': 'Solid Wood'},
                {'name': 'Garden Hose 50ft', 'desc': 'Flexible garden hose with spray nozzle', 'price': 1200, 'material': 'Rubber and Plastic'},
                {'name': 'LED Desk Lamp', 'desc': 'Adjustable LED desk lamp with USB charging', 'price': 2200, 'material': 'Metal and Plastic'},
                {'name': 'Flower Pots Set', 'desc': 'Set of 5 ceramic flower pots', 'price': 800, 'material': 'Ceramic'},
                {'name': 'Kitchen Knife Set', 'desc': 'Professional kitchen knife set with block', 'price': 3200, 'material': 'Stainless Steel'},
                {'name': 'Bed Sheets Queen', 'desc': 'Egyptian cotton bed sheet set', 'price': 2800, 'material': 'Egyptian Cotton'},
                {'name': 'Wall Mirror', 'desc': 'Decorative wall mirror 24x36 inches', 'price': 1800, 'material': 'Glass and Wood Frame'},
                {'name': 'Garden Tools Set', 'desc': 'Complete gardening tools set', 'price': 2500, 'material': 'Steel and Wood'},
            ],
            'books': [
                {'name': 'Python Programming Guide', 'desc': 'Complete guide to Python programming', 'price': 850, 'material': 'Paper'},
                {'name': 'Ethiopian History Book', 'desc': 'Comprehensive Ethiopian history', 'price': 650, 'material': 'Paper'},
                {'name': 'Business Management', 'desc': 'Modern business management principles', 'price': 1200, 'material': 'Paper'},
                {'name': 'Cookbook Ethiopian Cuisine', 'desc': 'Traditional Ethiopian recipes', 'price': 750, 'material': 'Paper'},
                {'name': 'Children\'s Story Book', 'desc': 'Illustrated children\'s stories', 'price': 350, 'material': 'Paper'},
                {'name': 'English Dictionary', 'desc': 'Comprehensive English dictionary', 'price': 950, 'material': 'Paper'},
                {'name': 'Mathematics Textbook', 'desc': 'Advanced mathematics textbook', 'price': 1100, 'material': 'Paper'},
                {'name': 'Art and Design Book', 'desc': 'Modern art and design concepts', 'price': 1400, 'material': 'Paper'},
            ],
            'sports': [
                {'name': 'Football Soccer Ball', 'desc': 'Official size soccer ball', 'price': 850, 'material': 'Synthetic Leather'},
                {'name': 'Basketball', 'desc': 'Professional basketball', 'price': 1200, 'material': 'Rubber'},
                {'name': 'Tennis Racket', 'desc': 'Professional tennis racket', 'price': 3500, 'material': 'Carbon Fiber'},
                {'name': 'Yoga Mat', 'desc': 'Non-slip yoga exercise mat', 'price': 1800, 'material': 'PVC'},
                {'name': 'Dumbbells Set', 'desc': 'Adjustable dumbbells 5-50 lbs', 'price': 8500, 'material': 'Cast Iron'},
                {'name': 'Swimming Goggles', 'desc': 'Anti-fog swimming goggles', 'price': 450, 'material': 'Silicone and Plastic'},
                {'name': 'Bicycle Helmet', 'desc': 'Safety bicycle helmet', 'price': 2200, 'material': 'Polycarbonate'},
                {'name': 'Running Shorts', 'desc': 'Moisture-wicking running shorts', 'price': 650, 'material': 'Polyester'},
            ],
            'beauty': [
                {'name': 'Face Moisturizer', 'desc': 'Daily face moisturizer with SPF', 'price': 1200, 'material': 'Cosmetic Formula'},
                {'name': 'Shampoo 500ml', 'desc': 'Nourishing shampoo for all hair types', 'price': 450, 'material': 'Cosmetic Formula'},
                {'name': 'Lipstick Set', 'desc': 'Set of 6 matte lipsticks', 'price': 1800, 'material': 'Cosmetic Formula'},
                {'name': 'Perfume 100ml', 'desc': 'Long-lasting eau de parfum', 'price': 3500, 'material': 'Fragrance'},
                {'name': 'Face Mask Pack', 'desc': 'Hydrating face mask pack of 10', 'price': 850, 'material': 'Cosmetic Formula'},
                {'name': 'Hair Conditioner', 'desc': 'Deep conditioning hair treatment', 'price': 650, 'material': 'Cosmetic Formula'},
                {'name': 'Nail Polish Set', 'desc': 'Set of 12 nail polish colors', 'price': 1400, 'material': 'Cosmetic Formula'},
                {'name': 'Body Lotion', 'desc': 'Moisturizing body lotion 400ml', 'price': 750, 'material': 'Cosmetic Formula'},
            ]
        }

        # Get or create a default supplier
        supplier, created = Supplier.objects.get_or_create(
            name='Default Supplier',
            defaults={
                'contact_person': 'Supply Manager',
                'email': 'supplier@example.com',
                'phone': '+251911000000',
                'address': 'Addis Ababa, Ethiopia'
            }
        )

        products_created = 0
        
        # Create products from each category
        for category, items in product_data.items():
            for item in items:
                if products_created >= num_products:
                    break
                    
                # Add some variation to prices
                base_price = item['price']
                varied_price = base_price + random.randint(-int(base_price*0.1), int(base_price*0.1))
                
                # Create product
                product = Product.objects.create(
                    name=item['name'],
                    category=category,
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
                
                if products_created % 10 == 0:
                    self.stdout.write(f'Created {products_created} products...')
            
            if products_created >= num_products:
                break

        self.stdout.write(f'Created {products_created} products total.')

    def create_store_stocks(self):
        """Create stock entries for each product in each store"""
        
        stores = Store.objects.all()
        products = Product.objects.all()
        
        if not stores.exists():
            self.stdout.write(self.style.WARNING('No stores found. Creating sample stores...'))
            # Create sample stores
            sample_stores = [
                {'name': 'Main Branch', 'address': 'Bole, Addis Ababa', 'phone_number': '+251911111111'},
                {'name': 'Piazza Branch', 'address': 'Piazza, Addis Ababa', 'phone_number': '+251911111112'},
                {'name': 'Merkato Branch', 'address': 'Merkato, Addis Ababa', 'phone_number': '+251911111113'},
                {'name': 'CMC Branch', 'address': 'CMC, Addis Ababa', 'phone_number': '+251911111114'},
            ]
            
            for store_data in sample_stores:
                Store.objects.create(**store_data)
            
            stores = Store.objects.all()

        stocks_created = 0
        
        with transaction.atomic():
            for store in stores:
                for product in products:
                    # Not every product needs to be in every store
                    if random.choice([True, True, True, False]):  # 75% chance
                        
                        # Calculate selling price (cost + markup)
                        markup_percentage = random.uniform(0.2, 0.8)  # 20-80% markup
                        selling_price = product.price * (1 + markup_percentage)
                        
                        # Random stock quantity
                        quantity = random.randint(0, 100)
                        
                        # Create stock entry
                        Stock.objects.create(
                            product=product,
                            store=store,
                            quantity=quantity,
                            low_stock_threshold=random.randint(5, 20),
                            selling_price=selling_price.quantize(Decimal('0.01'))
                        )
                        
                        stocks_created += 1

        self.stdout.write(f'Created {stocks_created} stock entries across {stores.count()} stores.')
