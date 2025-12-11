import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = (
        "Create or update a Django superuser from environment variables.\n"
        "Uses ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD. If username exists, ensures it is superuser/staff and updates password if provided."
    )

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.NOTICE(
                    "ADMIN_USERNAME/ADMIN_PASSWORD not set; skipping superuser creation."
                )
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email or "",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
            return

        # Ensure flags and password are set
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if not user.is_staff:
            user.is_staff = True
            updated = True
        if not user.is_superuser:
            user.is_superuser = True
            updated = True
        if password:
            user.set_password(password)
            updated = True
        if updated:
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' updated."))
        else:
            self.stdout.write(
                self.style.NOTICE(f"Superuser '{username}' already up-to-date.")
            )
