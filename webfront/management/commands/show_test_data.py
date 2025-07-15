from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg, F
from store.models import Store
from Inventory.models import Product, Stock
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Show summary of test data in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== TEST DATA SUMMARY ===\n'))

        # Users summary
        users = CustomUser.objects.all()
        self.stdout.write(f'👥 USERS ({users.count()} total):')
        for role in ['admin', 'head_manager', 'store_manager', 'cashier']:
            count = users.filter(role=role).count()
            self.stdout.write(f'  - {role.replace("_", " ").title()}: {count}')
        self.stdout.write('')

        # Stores summary
        stores = Store.objects.all()
        self.stdout.write(f'🏪 STORES ({stores.count()} total):')
        for store in stores:
            stock_count = Stock.objects.filter(store=store).count()
            manager = store.store_manager.username if store.store_manager else 'No manager'
            self.stdout.write(f'  - {store.name}: {stock_count} products (Manager: {manager})')
        self.stdout.write('')

        # Products summary
        products = Product.objects.all()
        self.stdout.write(f'📦 PRODUCTS ({products.count()} total):')
        categories = products.values('category').annotate(count=Count('id')).order_by('-count')
        for cat in categories:
            self.stdout.write(f'  - {cat["category"]}: {cat["count"]} products')
        self.stdout.write('')

        # Stock summary
        stocks = Stock.objects.all()
        self.stdout.write(f'📊 STOCK ENTRIES ({stocks.count()} total):')
        
        # Low stock items
        low_stock = stocks.filter(quantity__lte=F('low_stock_threshold')).count()
        self.stdout.write(f'  - Low stock items: {low_stock}')

        # Stock statistics
        stock_stats = stocks.aggregate(
            total_quantity=Sum('quantity'),
            avg_quantity=Avg('quantity'),
            total_value=Sum(F('quantity') * F('selling_price'))
        )
        
        self.stdout.write(f'  - Total quantity across all stores: {stock_stats["total_quantity"]}')
        self.stdout.write(f'  - Average quantity per item: {stock_stats["avg_quantity"]:.1f}')
        self.stdout.write(f'  - Total inventory value: ETB {stock_stats["total_value"]:.2f}')
        self.stdout.write('')

        # Test URLs
        self.stdout.write(self.style.SUCCESS('🌐 TEST THE WEBFRONT APP:'))
        self.stdout.write('  Main stock overview: http://127.0.0.1:8000/webfront/')
        self.stdout.write('  Login page: http://127.0.0.1:8000/')
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('👤 TEST USERS:'))
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Head Manager: headmanager / manager123')
        self.stdout.write('  Store Manager 1: storemanager1 / store123')
        self.stdout.write('  Store Manager 2: storemanager2 / store123')
        self.stdout.write('  Cashier 1: cashier1 / cashier123')
        self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('✅ Ready for testing! Login and navigate to Stock Overview in the sidebar.'))
