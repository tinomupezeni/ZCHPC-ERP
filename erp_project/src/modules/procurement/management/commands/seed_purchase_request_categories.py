"""
Management command to seed the F11-A MVP Purchase Request categories.

Why a command, not a migration
-------------------------------
This was originally written as a RunPython data migration (matching
modules.hr.migrations.0017_seed_role_permissions /
0018_seed_purchase_request_permissions). It was changed to a management
command after that migration was found, empirically, to break every
django_db test in the repository: pytest-django builds its test database by
running the full migration chain, and this seed's dependency on
accounts.AccountChart already containing the imported ZCHPC chart cannot be
satisfied at that point - nothing in the existing test suite pre-loads the
real chart (every existing procurement test creates its own single
AccountChart row directly, e.g. AccountChart.objects.create(code="1001",
...) - never relying on the real 103-row chart being present). A migration
that hard-fails when that dependency is missing therefore hard-fails on
every fresh database, test or otherwise, before a single test runs.

modules.accounts.management.commands.import_chart_of_accounts already
establishes this project's actual convention for exactly this situation -
real-world reference data that depends on external state, keyed by a stable
natural code, safe to re-run - as a management command rather than a
migration. This command follows that same convention and, where reasonable,
the same shape (idempotent, --dry-run, validates everything before writing
anything, reports what changed).

What this seeds, and why only this
------------------------------------
Exactly the 14 categories the F11 investigation identified as having a
single, unambiguous AccountChart mapping (its section 10, "Proposed MVP
employee categories"). Deliberately excluded, because each is still a
pending Finance decision, not an engineering one:

    - Fuel & Lubricants, General Maintenance, Advertising & Promotions:
      each has an unresolved Government/Internal-Resources funding-source
      variant.
    - The 11 "possible candidate" categories (training, consultancy,
      gifts, memberships, wellness, ...): eligibility not yet confirmed.
    - PP&E/capital accounts: separate treatment not yet approved.
    - Centrally-managed accounts (rent, insurance, audit fees, utilities):
      not intended as an employee Purchase Request category at all.

Do not extend MVP_CATEGORIES to "complete" the chart without that decision
having actually been made and recorded - see the F11 investigation report.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# (employee-facing name, AccountChart code) - F11 investigation section 10,
# verbatim.
MVP_CATEGORIES = [
    ("Stationery & Printing", "20000/01/101/010/300"),
    ("Travel & Subsistence", "20000/01/101/012/300"),
    ("Motor Vehicle Repairs", "20000/01/101/013/300"),
    ("Protective Clothing", "20000/01/101/020/301"),
    ("IT Consumables", "20000/01/101/021/300"),
    ("Software Subscriptions", "20000/01/101/022/300"),
    ("Catering / Refreshments", "20000/01/101/025/300"),
    ("Mobile Data & Airtime", "20000/02/100/005/301"),
    ("Cleaning Supplies & Materials", "20000/02/101/009/300"),
    ("Telephone & Internet", "20000/02/101/011/300"),
    ("IT Support Services", "20000/02/101/037/300"),
    ("Software / Operating Licences", "20000/02/101/040/300"),
    ("Equipment Repairs", "20000/02/101/043/301"),
    ("First Aid Consumables", "20000/02/101/055/301"),
]


class Command(BaseCommand):
    help = (
        "Seed the F11-A MVP Purchase Request categories, mapping each to its "
        "AccountChart row by code. Idempotent; never deletes or overwrites an "
        "existing category. Requires the ZCHPC chart of accounts to already "
        "be imported (see import_chart_of_accounts) - fails loudly, before "
        "writing anything, if a required code is missing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change, then roll back without saving.",
        )

    def handle(self, *args, **options):
        from modules.accounts.infrastructure.persistence.models import AccountChart
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequestCategory,
        )

        dry_run: bool = options["dry_run"]

        # Validate every code up front so a problem partway through the list
        # is reported in full, not discovered one create() at a time.
        missing_codes = [code for _name, code in MVP_CATEGORIES if not AccountChart.objects.filter(code=code).exists()]
        if missing_codes:
            raise CommandError(
                "The following AccountChart codes do not exist - import the "
                "chart of accounts first (see import_chart_of_accounts):\n  " + "\n  ".join(missing_codes)
            )

        created: list[str] = []
        skipped: list[str] = []

        with transaction.atomic():
            for name, code in MVP_CATEGORIES:
                if PurchaseRequestCategory.objects.filter(name=name).exists():
                    skipped.append(name)
                    continue

                account = AccountChart.objects.get(code=code)
                PurchaseRequestCategory.objects.create(name=name, account_chart=account, is_active=True)
                created.append(name)

            if dry_run:
                transaction.set_rollback(True)

        prefix = "[dry run - nothing saved] " if dry_run else ""
        self.stdout.write(f"{prefix}Source: {len(MVP_CATEGORIES)} MVP categories")
        for name in created:
            self.stdout.write(f"  created   {name}")
        for name in skipped:
            self.stdout.write(f"  unchanged {name} (already exists)")
        self.stdout.write(self.style.SUCCESS(f"{prefix}created: {len(created)}, unchanged: {len(skipped)}"))
