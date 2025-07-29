"""
Management command to check for low stock products and send notifications to suppliers
Can be run manually or scheduled as a cron job
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from Inventory.models import Supplier
from Inventory.stock_notification_service import StockNotificationService


class Command(BaseCommand):
    help = 'Check for low stock products and send notifications to suppliers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--supplier-id',
            type=int,
            help='Check specific supplier by ID (optional)',
        )
        parser.add_argument(
            '--supplier-name',
            type=str,
            help='Check specific supplier by name (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without sending notifications',
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=10,
            help='Low stock threshold (default: 10)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting supplier stock check at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        # Update threshold if provided
        if options['threshold']:
            StockNotificationService.LOW_STOCK_THRESHOLD = options['threshold']
            self.stdout.write(f'Using low stock threshold: {options["threshold"]}')

        # Determine which supplier(s) to check
        supplier = None
        if options['supplier_id']:
            try:
                supplier = Supplier.objects.get(id=options['supplier_id'])
                self.stdout.write(f'Checking specific supplier: {supplier.name}')
            except Supplier.DoesNotExist:
                raise CommandError(f'Supplier with ID {options["supplier_id"]} does not exist')
        
        elif options['supplier_name']:
            try:
                supplier = Supplier.objects.get(name__icontains=options['supplier_name'])
                self.stdout.write(f'Checking specific supplier: {supplier.name}')
            except Supplier.DoesNotExist:
                raise CommandError(f'Supplier with name containing "{options["supplier_name"]}" does not exist')
            except Supplier.MultipleObjectsReturned:
                suppliers = Supplier.objects.filter(name__icontains=options['supplier_name'])
                supplier_names = [s.name for s in suppliers]
                raise CommandError(f'Multiple suppliers found: {", ".join(supplier_names)}. Please be more specific.')

        # Get stock summary before processing
        summary = StockNotificationService.get_low_stock_summary(supplier)
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUPPLIER STOCK SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total products: {summary["total_products"]}')
        self.stdout.write(f'Low stock products: {summary["low_stock_count"]}')
        self.stdout.write(f'Critical stock products: {summary["critical_stock_count"]}')
        self.stdout.write(f'Out of stock products: {summary["out_of_stock_count"]}')

        if options['dry_run']:
            self.stdout.write('\n' + self.style.WARNING('DRY RUN MODE - No notifications will be sent'))
            
            # Show what would be notified
            if summary['low_stock_count'] > 0 or summary['out_of_stock_count'] > 0:
                self.stdout.write('\nProducts that would trigger notifications:')
                
                for product in summary['out_of_stock_products']:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  OUT OF STOCK: {product.product_name} ({product.supplier.name})'
                        )
                    )
                
                for product in summary['critical_stock_products']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  CRITICAL: {product.product_name} - {product.stock_quantity} units ({product.supplier.name})'
                        )
                    )
                
                for product in summary['low_stock_products']:
                    if product not in summary['critical_stock_products']:
                        self.stdout.write(
                            f'  LOW STOCK: {product.product_name} - {product.stock_quantity} units ({product.supplier.name})'
                        )
            else:
                self.stdout.write(self.style.SUCCESS('\nNo low stock products found!'))
            
            return

        # Send notifications
        if summary['low_stock_count'] > 0 or summary['out_of_stock_count'] > 0:
            self.stdout.write('\n' + '='*50)
            self.stdout.write('SENDING NOTIFICATIONS')
            self.stdout.write('='*50)
            
            result = StockNotificationService.check_and_send_low_stock_alerts(supplier)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Notifications sent: {result["notifications_sent"]}'
                    )
                )
                self.stdout.write(
                    f'📊 Suppliers checked: {result["suppliers_checked"]}'
                )
                self.stdout.write(
                    f'⚠️  Total low stock products: {result["total_low_stock_products"]}'
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error sending notifications: {result["error"]}')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ No low stock products found - no notifications needed!')
            )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Supplier stock check completed at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )
