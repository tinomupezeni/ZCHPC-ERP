"""
Management command to create or rotate a dedicated automation/test account.
"""
import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


def _generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = (
        "Create or rotate the dedicated automation/test account used by automated "
        "testing (e.g. scripts/smoke_test_employees.py), so tests don't depend on a "
        "real admin's personal credentials."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="automation@zchpc.ac.zw",
            help="Email for the test account (default: automation@zchpc.ac.zw)",
        )
        parser.add_argument(
            "--password",
            default=None,
            help="Password to set. If omitted, a random one is generated and printed once.",
        )
        parser.add_argument(
            "--rotate",
            action="store_true",
            help="If the account already exists, reset its password instead of leaving it untouched.",
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        rotate = options["rotate"]

        generated = password is None
        if generated:
            password = _generate_password()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Automation",
                "last_name": "Test Account",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created test account: {email}"))
        elif rotate:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Rotated password for existing test account: {email}"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Test account {email} already exists and --rotate was not passed - "
                    f"leaving its password unchanged."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'=' * 60}\n"
                f"Email:    {email}\n"
                f"Password: {password}\n"
                f"{'=' * 60}\n"
                f"{'Generated - ' if generated else ''}save this now; it will not be shown again.\n"
                f"This account is a superuser - RBACMiddleware (see\n"
                f"modules/identity/infrastructure/middleware.py) only bypasses its\n"
                f"role check for is_superuser, not is_staff alone, so anything less\n"
                f"can't exercise most authenticated endpoints. It's a dedicated,\n"
                f"rotatable account for testing - not tied to a real admin's identity.\n"
            )
        )
