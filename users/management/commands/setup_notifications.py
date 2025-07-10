from django.core.management.base import BaseCommand
from Inventory.models import NotificationCategory
from users.notifications import NotificationTriggers


class Command(BaseCommand):
    help = 'Setup notification categories and trigger initial notifications'

    def handle(self, *args, **options):
        self.stdout.write('Setting up notification system...')

        # Create notification categories
        categories = [
            {
                'name': 'user_management',
                'display_name': 'User Management',
                'icon': 'bi-people',
                'color': 'warning',
                'priority': 1
            },
            {
                'name': 'requests',
                'display_name': 'Requests',
                'icon': 'bi-inbox',
                'color': 'primary',
                'priority': 2
            },
            {
                'name': 'suppliers',
                'display_name': 'Suppliers',
                'icon': 'bi-shop',
                'color': 'info',
                'priority': 3
            },
            {
                'name': 'inventory',
                'display_name': 'Inventory',
                'icon': 'bi-box-seam',
                'color': 'success',
                'priority': 4
            },
            {
                'name': 'system',
                'display_name': 'System',
                'icon': 'bi-gear',
                'color': 'secondary',
                'priority': 5
            },
            {
                'name': 'general',
                'display_name': 'General',
                'icon': 'bi-bell',
                'color': 'primary',
                'priority': 6
            }
        ]

        for cat_data in categories:
            category, created = NotificationCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'display_name': cat_data['display_name'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'priority': cat_data['priority']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.display_name}')
            else:
                self.stdout.write(f'Category exists: {category.display_name}')

        # Trigger initial notification checks
        self.stdout.write('\nTriggering initial notification checks...')
        
        try:
            NotificationTriggers.check_unassigned_store_managers()
            self.stdout.write('✓ Checked for unassigned store managers')
        except Exception as e:
            self.stdout.write(f'✗ Error checking unassigned store managers: {e}')

        self.stdout.write(self.style.SUCCESS('\nNotification system setup complete!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('1. View notifications in the top navigation bar')
        self.stdout.write('2. Submit restock/transfer requests to generate notifications')
        self.stdout.write('3. Check notification API at /api/notifications/')
        self.stdout.write('4. Trigger manual checks at /api/notifications/trigger-check/')
