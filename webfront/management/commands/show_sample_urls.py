from django.core.management.base import BaseCommand
from store.models import Store
from Inventory.models import Stock


class Command(BaseCommand):
    help = 'Show sample URLs for testing webfront app'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔗 SAMPLE WEBFRONT URLs FOR TESTING:\n'))

        # Get sample data
        store = Store.objects.first()
        stock = Stock.objects.first()

        if not store or not stock:
            self.stdout.write(self.style.ERROR('No test data found. Run: python manage.py generate_test_data'))
            return

        base_url = 'http://127.0.0.1:8000'

        self.stdout.write('📋 Main Views:')
        self.stdout.write(f'  Stock Overview: {base_url}/webfront/')
        self.stdout.write('')

        self.stdout.write('🏪 Store-Specific Views:')
        for i, store in enumerate(Store.objects.all()[:3], 1):
            self.stdout.write(f'  {store.name}: {base_url}/webfront/store/{store.id}/')

        self.stdout.write('')
        self.stdout.write('📦 Stock Detail Views:')
        for i, stock in enumerate(Stock.objects.all()[:3], 1):
            self.stdout.write(f'  {stock.product.name} at {stock.store.name}: {base_url}/webfront/stock/{stock.id}/')

        self.stdout.write('')
        self.stdout.write('🔍 Product Across Stores:')
        for i, stock in enumerate(Stock.objects.all()[:3], 1):
            self.stdout.write(f'  {stock.product.name}: {base_url}/webfront/product/{stock.product.id}/stores/')

        self.stdout.write('')
        self.stdout.write('🔐 Login first at: http://127.0.0.1:8000/')
        self.stdout.write('Then navigate using the sidebar "Stock Overview" link')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Copy and paste these URLs to test different views!'))
