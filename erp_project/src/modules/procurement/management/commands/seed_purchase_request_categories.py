"""
Management command that installs the employee-facing Purchase Request
category set (F25 category redesign).

These categories are purely descriptive: they tell Accounts what the
employee needs. They are NOT accounting classifications and carry no GL
mapping - Accounts alone assigns PurchaseRequestItem.budget_code_id. New
categories are therefore created with no AccountChart link.

What it does (idempotent, safe to re-run):
    - creates each category in EMPLOYEE_CATEGORIES that does not exist yet,
      active and unmapped; re-activates one that exists but is inactive;
    - deactivates exactly the F11-A categories in LEGACY_CATEGORY_NAMES that
      are not part of the new set. Nothing is ever deleted: items keep their
      category, and inactive categories are still shown on historical
      requests - they just can no longer be chosen;
    - never touches a category it does not know about, and never modifies an
      existing row's account_chart (two legacy rows share a name with the new
      set and simply stay active as they are).

Why a command and not a migration: see the project's other reference-data
commands (e.g. import_chart_of_accounts) - this follows the same convention.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

# The employee-facing set, in the order it was specified.
EMPLOYEE_CATEGORIES = [
    "Office & Stationery Supplies",
    "Fuel & Lubricants",
    "Travel & Subsistence",
    "Cleaning & Hygiene Supplies",
    "Protective Clothing & Safety Equipment",
    "IT Hardware & Accessories",
    "IT Software & Subscriptions",
    "IT & Technical Services",
    "Mobile Data & Airtime",
    "Telephone & Internet Services",
    "Vehicle Maintenance & Repairs",
    "Equipment Maintenance & Repairs",
    "Catering & Refreshments",
    "Training & Development",
    "Conferences, Exhibitions & Seminars",
    "Advertising & Promotions",
    "Consultancy & Professional Services",
    "Staff Welfare & Wellness",
    "General Maintenance & Facilities",
    "Other / Not Listed",
]

# The 14 categories seeded by F11-A, which the new set replaces.
LEGACY_CATEGORY_NAMES = [
    "Stationery & Printing",
    "Travel & Subsistence",
    "Motor Vehicle Repairs",
    "Protective Clothing",
    "IT Consumables",
    "Software Subscriptions",
    "Catering / Refreshments",
    "Mobile Data & Airtime",
    "Cleaning Supplies & Materials",
    "Telephone & Internet",
    "IT Support Services",
    "Software / Operating Licences",
    "Equipment Repairs",
    "First Aid Consumables",
]

_NEW = set(EMPLOYEE_CATEGORIES)
# Legacy names that the new set does not reuse - these get deactivated.
RETIRED_CATEGORY_NAMES = [name for name in LEGACY_CATEGORY_NAMES if name not in _NEW]


class Command(BaseCommand):
    help = (
        "Install the employee-facing Purchase Request categories (no GL "
        "mapping) and deactivate the retired F11-A ones. Idempotent; never "
        "deletes a category."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change, then roll back without saving.",
        )

    def handle(self, *args, **options):
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequestCategory,
        )

        dry_run: bool = options["dry_run"]
        created: list[str] = []
        reactivated: list[str] = []
        unchanged: list[str] = []
        deactivated: list[str] = []

        with transaction.atomic():
            for name in EMPLOYEE_CATEGORIES:
                category = PurchaseRequestCategory.objects.filter(name=name).first()
                if category is None:
                    PurchaseRequestCategory.objects.create(
                        name=name, account_chart=None, is_active=True
                    )
                    created.append(name)
                elif not category.is_active:
                    category.is_active = True
                    category.save(update_fields=["is_active", "updated_at"])
                    reactivated.append(name)
                else:
                    unchanged.append(name)

            for name in RETIRED_CATEGORY_NAMES:
                updated = PurchaseRequestCategory.objects.filter(
                    name=name, is_active=True
                ).update(is_active=False)
                if updated:
                    deactivated.append(name)

            if dry_run:
                transaction.set_rollback(True)

        prefix = "[dry run - nothing saved] " if dry_run else ""
        for name in created:
            self.stdout.write(f"  created     {name}")
        for name in reactivated:
            self.stdout.write(f"  reactivated {name}")
        for name in deactivated:
            self.stdout.write(f"  deactivated {name}")
        for name in unchanged:
            self.stdout.write(f"  unchanged   {name}")
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}created: {len(created)}, reactivated: {len(reactivated)}, "
                f"deactivated: {len(deactivated)}, unchanged: {len(unchanged)}"
            )
        )
