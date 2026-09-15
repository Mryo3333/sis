import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from students.models import UserProfile


class Command(BaseCommand):
    help = "Create or update the deployment administrator from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        email = os.environ.get("ADMIN_EMAIL", "").strip()

        if not username and not password and not email:
            self.stdout.write("Admin bootstrap skipped: ADMIN_* variables are not set.")
            return

        if not username or not password:
            raise CommandError("ADMIN_USERNAME and ADMIN_PASSWORD must both be set.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": "Admin",
                "registration_status": "Approved",
            },
        )

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Deployment admin {action}: {username}"))
