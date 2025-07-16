from django.core.management.base import BaseCommand
from Inventory.models import WarehouseProduct


class Command(BaseCommand):
    help = 'Check warehouse location data for products'

    def handle(self, *args, **options):
        products = WarehouseProduct.objects.all()
        
        self.stdout.write(f'Total warehouse products: {products.count()}')
        self.stdout.write('')
        
        for product in products:
            location = product.warehouse_location
            warehouse = product.warehouse
            
            self.stdout.write(f'Product: {product.product_name}')
            self.stdout.write(f'  - Warehouse: {warehouse.name if warehouse else "None"}')
            self.stdout.write(f'  - Location: "{location}" (length: {len(location) if location else 0})')
            self.stdout.write(f'  - Location is empty: {not location}')
            self.stdout.write(f'  - Location is None: {location is None}')
            self.stdout.write('')
            
        # Check for products with empty locations
        empty_locations = products.filter(warehouse_location__in=['', None])
        self.stdout.write(f'Products with empty/null locations: {empty_locations.count()}')
        
        # Check for products with locations
        with_locations = products.exclude(warehouse_location__in=['', None])
        self.stdout.write(f'Products with locations: {with_locations.count()}')
        
        if with_locations.exists():
            self.stdout.write('\nProducts with locations:')
            for product in with_locations[:5]:
                self.stdout.write(f'  - {product.product_name}: "{product.warehouse_location}"')
