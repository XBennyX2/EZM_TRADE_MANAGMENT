from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Store
from Inventory.models import Product, Stock, RestockRequest, StoreStockTransferRequest
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for Store Manager functionality'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')

        # Create test users if they don't exist
        head_manager, created = User.objects.get_or_create(
            username='head_manager_test',
            defaults={
                'email': 'head_manager@test.com',
                'role': 'head_manager',
                'is_first_login': False,
                'first_name': 'Head',
                'last_name': 'Manager'
            }
        )
        if created:
            head_manager.set_password('password123')
            head_manager.save()
            self.stdout.write(f'Created head manager: {head_manager.username}')

        # Create test stores
        store1, created = Store.objects.get_or_create(
            name='Downtown Store',
            defaults={
                'address': '123 Main St, Downtown',
                'phone_number': '555-0101'
            }
        )
        if created:
            self.stdout.write(f'Created store: {store1.name}')

        store2, created = Store.objects.get_or_create(
            name='Mall Store',
            defaults={
                'address': '456 Mall Ave, Shopping Center',
                'phone_number': '555-0102'
            }
        )
        if created:
            self.stdout.write(f'Created store: {store2.name}')

        # Create store managers
        store_manager1, created = User.objects.get_or_create(
            username='store_manager1',
            defaults={
                'email': 'store_manager1@test.com',
                'role': 'store_manager',
                'store': store1,
                'is_first_login': False,
                'first_name': 'Store',
                'last_name': 'Manager One'
            }
        )
        if created:
            store_manager1.set_password('password123')
            store_manager1.save()
            self.stdout.write(f'Created store manager: {store_manager1.username}')

        store_manager2, created = User.objects.get_or_create(
            username='store_manager2',
            defaults={
                'email': 'store_manager2@test.com',
                'role': 'store_manager',
                'store': store2,
                'is_first_login': False,
                'first_name': 'Store',
                'last_name': 'Manager Two'
            }
        )
        if created:
            store_manager2.set_password('password123')
            store_manager2.save()
            self.stdout.write(f'Created store manager: {store_manager2.username}')

        # Assign store managers to stores
        store1.store_manager = store_manager1
        store1.save()
        store2.store_manager = store_manager2
        store2.save()

        # Create test products
        products_data = [
            {'name': 'PVC Pipe 2 inch', 'category': 'Pipes', 'price': Decimal('15.99'), 'description': 'Standard PVC pipe 2 inch diameter'},
            {'name': 'Copper Wire 12 AWG', 'category': 'Electric Wire', 'price': Decimal('89.99'), 'description': 'Copper electrical wire 12 AWG'},
            {'name': 'Portland Cement', 'category': 'Cement', 'price': Decimal('12.50'), 'description': 'High quality Portland cement'},
            {'name': 'Ceramic Floor Tiles', 'category': 'Ceramics', 'price': Decimal('3.25'), 'description': 'Premium ceramic floor tiles'},
            {'name': 'Tempered Glass Panel', 'category': 'Glass and Finishing Materials', 'price': Decimal('125.00'), 'description': 'Tempered safety glass panel'},
        ]

        products = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'category': product_data['category'],
                    'price': product_data['price'],
                    'description': product_data['description'],
                    'material': 'Standard material'
                }
            )
            products.append(product)
            if created:
                self.stdout.write(f'Created product: {product.name}')

        # Create stock for stores
        for i, product in enumerate(products):
            # Store 1 stock
            stock1, created = Stock.objects.get_or_create(
                product=product,
                store=store1,
                defaults={
                    'quantity': 50 - (i * 10),  # Varying quantities
                    'low_stock_threshold': 15,
                    'selling_price': product.price * Decimal('1.2')  # 20% markup
                }
            )
            if created:
                self.stdout.write(f'Created stock for {product.name} at {store1.name}: {stock1.quantity}')

            # Store 2 stock
            stock2, created = Stock.objects.get_or_create(
                product=product,
                store=store2,
                defaults={
                    'quantity': 30 + (i * 5),  # Different quantities
                    'low_stock_threshold': 15,
                    'selling_price': product.price * Decimal('1.2')  # 20% markup
                }
            )
            if created:
                self.stdout.write(f'Created stock for {product.name} at {store2.name}: {stock2.quantity}')

        # Create some sample restock requests
        if products:
            restock_request1, created = RestockRequest.objects.get_or_create(
                store=store1,
                product=products[0],
                defaults={
                    'requested_quantity': 100,
                    'current_stock': 10,
                    'priority': 'high',
                    'reason': 'Running low on inventory, high demand product',
                    'requested_by': store_manager1,
                    'status': 'pending'
                }
            )
            if created:
                self.stdout.write(f'Created restock request: {restock_request1.request_number}')

            # Create a transfer request
            transfer_request1, created = StoreStockTransferRequest.objects.get_or_create(
                product=products[1],
                from_store=store2,
                to_store=store1,
                defaults={
                    'requested_quantity': 20,
                    'priority': 'medium',
                    'reason': 'Store 1 needs more copper wire for upcoming project',
                    'requested_by': store_manager1,
                    'status': 'pending'
                }
            )
            if created:
                self.stdout.write(f'Created transfer request: {transfer_request1.request_number}')

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write('')
        self.stdout.write('Test accounts created:')
        self.stdout.write(f'Head Manager: head_manager_test / password123')
        self.stdout.write(f'Store Manager 1: store_manager1 / password123 (Downtown Store)')
        self.stdout.write(f'Store Manager 2: store_manager2 / password123 (Mall Store)')
        self.stdout.write('')
        self.stdout.write('You can now test the Store Manager functionality!')
