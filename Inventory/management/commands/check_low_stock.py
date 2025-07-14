from django.core.management.base import BaseCommand
from django.db import transaction
from Inventory.models import WarehouseProduct
from users.notifications import NotificationManager
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check for low stock products and create notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force check even if notifications were recently sent',
        )

    def handle(self, *args, **options):
        self.stdout.write('Checking for low stock products...')
        
        # Get all low stock products
        low_stock_products = WarehouseProduct.get_low_stock_products()
        
        if not low_stock_products.exists():
            self.stdout.write(self.style.SUCCESS('No low stock products found.'))
            return
        
        self.stdout.write(f'Found {low_stock_products.count()} low stock products:')
        
        # Group products by category for better notification organization
        categories = {}
        for product in low_stock_products:
            category = product.category
            if category not in categories:
                categories[category] = []
            categories[category].append(product)
            
            self.stdout.write(
                f'  - {product.product_name}: {product.quantity_in_stock}/{product.minimum_stock_level} '
                f'(Supplier: {product.supplier.name})'
            )
        
        # Create notifications for each category
        with transaction.atomic():
            for category, products in categories.items():
                if len(products) == 1:
                    product = products[0]
                    title = f'Low Stock Alert: {product.product_name}'
                    message = (
                        f'{product.product_name} is running low. '
                        f'Current stock: {product.quantity_in_stock} units '
                        f'(Minimum: {product.minimum_stock_level}). '
                        f'Supplier: {product.supplier.name}'
                    )
                else:
                    title = f'Low Stock Alert: {len(products)} {category.title()} Products'
                    product_list = ', '.join([p.product_name for p in products[:3]])
                    if len(products) > 3:
                        product_list += f' and {len(products) - 3} more'
                    message = f'Multiple {category} products are running low: {product_list}'
                
                # Create notification for Head Managers and Store Managers
                NotificationManager.create_notification(
                    notification_type='low_stock_alert',
                    title=title,
                    message=message,
                    target_roles=['head_manager', 'store_manager'],
                    priority='high' if len(products) > 5 else 'medium',
                    action_url='/inventory/warehouse-products/',
                    action_text='View Inventory',
                    expires_hours=72  # 3 days
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created low stock notifications for {len(categories)} categories '
                f'covering {low_stock_products.count()} products.'
            )
        )
