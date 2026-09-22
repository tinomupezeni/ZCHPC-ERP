"""
Integration tests for the seed_purchase_request_categories management command
(F25 category redesign): installs the 20 employee-facing categories with no GL
mapping and retires the 12 F11-A categories the new set does not reuse.
"""

from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework import status

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory,
    PurchaseRequestItem,
)
from modules.procurement.management.commands.seed_purchase_request_categories import (
    EMPLOYEE_CATEGORIES,
    LEGACY_CATEGORY_NAMES,
    RETIRED_CATEGORY_NAMES,
)

pytestmark = pytest.mark.django_db


def _legacy_category(name, code, active=True):
    # Reuse a row a shared fixture already created under this name.
    existing = PurchaseRequestCategory.objects.filter(name=name).first()
    if existing:
        return existing
    account = AccountChart.objects.create(code=code, name=name, account_type="regular")
    return PurchaseRequestCategory.objects.create(
        name=name, account_chart=account, is_active=active
    )


def _seed_legacy():
    return {
        name: _legacy_category(name, f"LEG/{i:02d}")
        for i, name in enumerate(LEGACY_CATEGORY_NAMES)
    }


class TestSpecifiedSet:
    def test_exactly_the_20_specified_categories(self):
        assert len(EMPLOYEE_CATEGORIES) == 20
        assert len(set(EMPLOYEE_CATEGORIES)) == 20
        assert EMPLOYEE_CATEGORIES[0] == "Office & Stationery Supplies"
        assert EMPLOYEE_CATEGORIES[-1] == "Other / Not Listed"

    def test_two_legacy_names_are_reused_and_twelve_are_retired(self):
        assert set(LEGACY_CATEGORY_NAMES) & set(EMPLOYEE_CATEGORIES) == {
            "Travel & Subsistence",
            "Mobile Data & Airtime",
        }
        assert len(RETIRED_CATEGORY_NAMES) == 12


class TestSeedOnAFreshDatabase:
    def test_creates_all_20_active_with_no_gl_mapping(self):
        call_command("seed_purchase_request_categories")

        categories = PurchaseRequestCategory.objects.all()
        assert categories.count() == 20
        assert {c.name for c in categories} == set(EMPLOYEE_CATEGORIES)
        assert all(c.is_active for c in categories)
        assert all(c.account_chart_id is None for c in categories)

    def test_needs_no_chart_of_accounts(self):
        assert AccountChart.objects.count() == 0

        call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.count() == 20

    def test_rerunning_is_idempotent(self):
        call_command("seed_purchase_request_categories")
        first = set(PurchaseRequestCategory.objects.values_list("id", flat=True))

        call_command("seed_purchase_request_categories")

        assert set(PurchaseRequestCategory.objects.values_list("id", flat=True)) == first

    def test_dry_run_saves_nothing(self):
        call_command("seed_purchase_request_categories", dry_run=True)

        assert PurchaseRequestCategory.objects.count() == 0


class TestSeedOnADatabaseWithLegacyCategories:
    def test_retired_categories_are_deactivated_not_deleted(self):
        legacy = _seed_legacy()

        call_command("seed_purchase_request_categories")

        for name in RETIRED_CATEGORY_NAMES:
            row = PurchaseRequestCategory.objects.get(pk=legacy[name].pk)
            assert row.is_active is False
        # Nothing was deleted: 14 legacy rows + 18 brand-new ones.
        assert PurchaseRequestCategory.objects.count() == 14 + 18

    def test_reused_names_keep_their_existing_row_and_stay_active(self):
        legacy = _seed_legacy()

        call_command("seed_purchase_request_categories")

        for name in ("Travel & Subsistence", "Mobile Data & Airtime"):
            row = PurchaseRequestCategory.objects.get(name=name)
            assert row.pk == legacy[name].pk
            assert row.is_active is True
            # The seed never modifies an existing row's legacy mapping.
            assert row.account_chart_id == legacy[name].account_chart_id

    def test_new_categories_get_no_gl_mapping_even_with_a_chart_present(self):
        _seed_legacy()

        call_command("seed_purchase_request_categories")

        new_only = PurchaseRequestCategory.objects.exclude(name__in=LEGACY_CATEGORY_NAMES)
        assert new_only.count() == 18
        assert all(c.account_chart_id is None for c in new_only)

    def test_active_set_is_exactly_the_specified_20(self):
        _seed_legacy()

        call_command("seed_purchase_request_categories")

        active = set(
            PurchaseRequestCategory.objects.filter(is_active=True).values_list(
                "name", flat=True
            )
        )
        assert active == set(EMPLOYEE_CATEGORIES)

    def test_historical_items_keep_their_retired_category(
        self, requester, make_request_record
    ):
        legacy = _seed_legacy()
        retired = legacy["IT Consumables"]
        record = make_request_record(requester, status="PROCESSED")
        item = record.items.get()
        item.category = retired
        item.save()

        call_command("seed_purchase_request_categories")

        item.refresh_from_db()
        assert item.category_id == retired.pk
        retired.refresh_from_db()
        assert retired.is_active is False

    def test_an_unknown_manually_added_category_is_left_alone(self):
        custom = PurchaseRequestCategory.objects.create(name="Custom Thing", is_active=True)
        _seed_legacy()

        call_command("seed_purchase_request_categories")

        custom.refresh_from_db()
        assert custom.is_active is True

    def test_an_inactive_category_in_the_new_set_is_reactivated(self):
        PurchaseRequestCategory.objects.create(name="Fuel & Lubricants", is_active=False)

        call_command("seed_purchase_request_categories")

        assert PurchaseRequestCategory.objects.get(name="Fuel & Lubricants").is_active is True

    def test_rerunning_after_legacy_data_is_idempotent(self):
        _seed_legacy()
        call_command("seed_purchase_request_categories")
        first = set(PurchaseRequestCategory.objects.values_list("id", "is_active"))

        call_command("seed_purchase_request_categories")

        assert set(PurchaseRequestCategory.objects.values_list("id", "is_active")) == first


class TestEmployeeFacingBehaviourAfterSeeding:
    def _item(self, category_id):
        return {
            "description": "Something",
            "quantity": 1,
            "expected_delivery_period": "1 week",
            "estimated_cost": "10.00",
            "category_id": category_id,
        }

    def test_active_list_shows_only_the_new_set_and_only_id_and_name(
        self, client_for, category_url, requester
    ):
        _seed_legacy()
        call_command("seed_purchase_request_categories")

        response = client_for(requester).get(category_url)

        assert response.status_code == status.HTTP_200_OK
        assert {row["name"] for row in response.data} == set(EMPLOYEE_CATEGORIES)
        assert all(set(row) == {"id", "name"} for row in response.data)
        assert not ({row["name"] for row in response.data} & set(RETIRED_CATEGORY_NAMES))

    def test_request_can_be_raised_with_a_new_unmapped_category(
        self, client_for, api_url, requester
    ):
        call_command("seed_purchase_request_categories")
        fuel = PurchaseRequestCategory.objects.get(name="Fuel & Lubricants")

        response = client_for(requester).post(
            api_url, {"items": [self._item(fuel.id)]}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED, response.data
        row = PurchaseRequestItem.objects.get(pk=response.data["items"][0]["id"])
        assert row.category_id == fuel.id
        assert row.budget_code_id is None  # a category never sets the code

    def test_retired_category_can_no_longer_be_chosen(
        self, client_for, api_url, requester
    ):
        legacy = _seed_legacy()
        call_command("seed_purchase_request_categories")

        response = client_for(requester).post(
            api_url,
            {"items": [self._item(legacy["IT Consumables"].pk)]},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "CATEGORY_INACTIVE"

    def test_historical_request_still_reports_its_retired_category(
        self, client_for, api_url, requester, make_request_record
    ):
        legacy = _seed_legacy()
        record = make_request_record(requester, status="PROCESSED")
        item = record.items.get()
        item.category = legacy["Stationery & Printing"]
        item.save()
        call_command("seed_purchase_request_categories")

        response = client_for(requester).get(f"{api_url}{record.id}/")

        assert response.data["items"][0]["category"] == {
            "id": legacy["Stationery & Printing"].pk,
            "name": "Stationery & Printing",
            "is_active": False,
        }

    def test_seeding_does_not_touch_budget_code_assignments(
        self, requester, make_request_record, budget_code
    ):
        _seed_legacy()
        record = make_request_record(requester, status="PROCESSED")
        assert record.items.get().budget_code_id == budget_code.id

        call_command("seed_purchase_request_categories")

        assert record.items.get().budget_code_id == budget_code.id
        assert Decimal(record.items.get().estimated_cost) == Decimal("1500.00")
