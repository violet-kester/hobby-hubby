"""
Management command to activate all inactive users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):
    help = 'Activate all inactive users (useful after disabling email verification)'

    def handle(self, *args, **options):
        """Activate all inactive users."""
        inactive_users = User.objects.filter(is_active=False)
        count = inactive_users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No inactive users found.'))
            return

        # Activate all inactive users
        inactive_users.update(is_active=True)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated {count} user(s).')
        )

        # Show which users were activated
        for user in User.objects.filter(pk__in=inactive_users.values_list('pk', flat=True)):
            self.stdout.write(f'  - {user.email} (ID: {user.pk})')
