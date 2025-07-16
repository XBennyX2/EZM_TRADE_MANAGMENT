from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from store.models import Store

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for webfront app testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test users before creating new ones'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test users...')
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing test users cleared.'))

        with transaction.atomic():
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@ezm.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write('Created admin user (username: admin, password: admin123)')

            # Create head manager
            head_manager, created = User.objects.get_or_create(
                username='headmanager',
                defaults={
                    'email': 'headmanager@ezm.com',
                    'first_name': 'Head',
                    'last_name': 'Manager',
                    'role': 'head_manager',
                    'is_staff': True,
                }
            )
            if created:
                head_manager.set_password('manager123')
                head_manager.save()
                self.stdout.write('Created head manager (username: headmanager, password: manager123)')

            # Create store managers for each store
            stores = Store.objects.all()[:5]  # Get first 5 stores
            for i, store in enumerate(stores, 1):
                store_manager, created = User.objects.get_or_create(
                    username=f'storemanager{i}',
                    defaults={
                        'email': f'storemanager{i}@ezm.com',
                        'first_name': f'Store{i}',
                        'last_name': 'Manager',
                        'role': 'store_manager',
                        'is_staff': False,
                    }
                )
                if created:
                    store_manager.set_password('store123')
                    store_manager.save()
                    
                    # Assign manager to store
                    store.store_manager = store_manager
                    store.save()
                    
                    self.stdout.write(f'Created store manager for {store.name} (username: storemanager{i}, password: store123)')

            # Create some cashiers
            for i in range(1, 6):
                cashier, created = User.objects.get_or_create(
                    username=f'cashier{i}',
                    defaults={
                        'email': f'cashier{i}@ezm.com',
                        'first_name': f'Cashier{i}',
                        'last_name': 'User',
                        'role': 'cashier',
                        'is_staff': False,
                    }
                )
                if created:
                    cashier.set_password('cashier123')
                    cashier.save()
                    self.stdout.write(f'Created cashier{i} (username: cashier{i}, password: cashier123)')

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created test users. You can now login with:'
                '\n- Admin: admin/admin123'
                '\n- Head Manager: headmanager/manager123'
                '\n- Store Managers: storemanager1-5/store123'
                '\n- Cashiers: cashier1-5/cashier123'
            )
        )
