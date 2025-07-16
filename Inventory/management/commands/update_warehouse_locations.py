from django.core.management.base import BaseCommand
from Inventory.models import WarehouseProduct


class Command(BaseCommand):
    help = 'Update warehouse locations for products that have empty locations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all products, even those with existing locations',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        if force:
            products = WarehouseProduct.objects.all()
            self.stdout.write('Updating ALL warehouse products...')
        else:
            products = WarehouseProduct.objects.filter(warehouse_location__in=['', None])
            self.stdout.write('Updating products with empty/null locations...')
        
        updated_count = 0
        
        # Define location mapping based on category
        location_mapping = {
            'cement': 'Aisle A, Section {}',
            'steel': 'Aisle B, Section {}',
            'tiles': 'Aisle C, Section {}',
            'paint': 'Aisle D, Shelf {}',
            'electrical': 'Aisle E, Shelf {}',
            'plumbing': 'Aisle F, Shelf {}',
            'bricks': 'Yard Area {}',
            'blocks': 'Aisle C, Stack {}',
        }
        
        for i, product in enumerate(products, 1):
            category = product.category.lower()
            
            # Find appropriate location based on category
            location = None
            for key, template in location_mapping.items():
                if key in category:
                    location = template.format(i % 5 + 1)  # Cycle through sections 1-5
                    break
            
            # Default location if category doesn't match
            if not location:
                location = f"Aisle G, Section {i % 5 + 1}"
            
            # Update the product
            if force or not product.warehouse_location:
                old_location = product.warehouse_location
                product.warehouse_location = location
                product.save()
                updated_count += 1
                
                self.stdout.write(
                    f'Updated {product.product_name}: "{old_location}" -> "{location}"'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} products')
        )
