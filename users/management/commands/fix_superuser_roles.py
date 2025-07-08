from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Ensures all superusers have the admin role assigned'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Find all superusers without admin role
        superusers_without_role = User.objects.filter(
            is_superuser=True
        ).exclude(role='admin')
        
        updated_count = 0
        for user in superusers_without_role:
            old_role = user.role
            user.role = 'admin'
            user.save()
            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated superuser "{user.username}" role from "{old_role}" to "admin"'
                )
            )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All superusers already have admin role assigned')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} superuser(s)')
            )
