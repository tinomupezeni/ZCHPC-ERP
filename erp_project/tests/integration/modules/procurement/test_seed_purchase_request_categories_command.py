"""
Integration tests for the seed_purchase_request_categories management command
(Slice F11-A).

Why a command and not a migration: see the module docstring of
modules.procurement.management.commands.seed_purchase_request_categories -
in short, a RunPython migration with the same "fail loudly if the code is
missing" behavior broke every django_db test in the repository, because
pytest-django's fresh test database has no AccountChart rows at migration
time (nothing in this repository's existing tests pre-loads the real chart).
"""

from django.core.management import call_command
from django.core.management.base import CommandError

import pytest

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory,
)
from modules.procurement.management.commands.seed_purchase_request_categories import (
    MVP_CATEGORIES,
)

pytestmark = pytest.mark.django_db


class TestSeedCommandAgainstTheRealChart:
    """
    Imports the actual committed ZCHPC chart of accounts (the same file
    test_import_chart_of_accounts.py pins values against), then seeds
    categories against it - proving the 14 mappings resolve against real,
    not synthetic, AccountChart data.
    """

    def test_all_14_mappings_resolve_to_the_expected_real_account(self):
        call_command("import_chart_of_accounts")

        call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.count() == len(MVP_CATEGORIES)
        for name, code in MVP_CATEGORIES:
            category = PurchaseRequestCategory.objects.select_related(
                "account_chart"
            ).get(name=name)
            assert category.account_chart.code == code
            assert category.is_active is True

    def test_no_seeded_category_points_to_a_nonexistent_account(self):
        """
        Not just "no orphaned FK" (the database enforces that structurally
        via account_chart being a required OneToOneField) - this confirms
        every seeded row's account_chart_id actually resolves to a real,
        currently-persisted AccountChart row.
        """
        call_command("import_chart_of_accounts")
        call_command("seed_purchase_request_categories")

        existing_account_ids = set(AccountChart.objects.values_list("id", flat=True))
        for category in PurchaseRequestCategory.objects.all():
            assert category.account_chart_id in existing_account_ids

    def test_rerunning_is_idempotent(self):
        call_command("import_chart_of_accounts")
        call_command("seed_purchase_request_categories")
        first_ids = set(PurchaseRequestCategory.objects.values_list("id", flat=True))

        call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.count() == len(MVP_CATEGORIES)
        assert set(PurchaseRequestCategory.objects.values_list("id", flat=True)) == first_ids

    def test_dry_run_saves_nothing(self):
        call_command("import_chart_of_accounts")

        call_command("seed_purchase_request_categories", dry_run=True)

        assert PurchaseRequestCategory.objects.count() == 0


class TestSeedCommandFailsLoudlyOnAMissingAccount:
    def test_missing_account_chart_data_raises_and_creates_nothing(self):
        """
        The chart has not been imported at all here - every one of the 14
        codes is missing. This must fail loudly (CommandError), not silently
        skip the unmappable categories or create partial/invalid rows.
        """
        with pytest.raises(CommandError):
            call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.count() == 0

    def test_one_missing_code_blocks_the_entire_run(self):
        """
        Import the real chart, then remove just one of the 14 required
        accounts - the run must fail before creating any of the other 13,
        rather than silently seeding everything it can.
        """
        call_command("import_chart_of_accounts")
        AccountChart.objects.filter(code="20000/01/101/021/300").delete()  # IT Consumables

        with pytest.raises(CommandError):
            call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.count() == 0
