"""
Integration tests for DjangoPurchaseRequestCategoryRepository (Slice F11-A).
"""

from django.db import IntegrityError, transaction
from django.test import TestCase

import pytest

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.procurement.domain.entities import PurchaseRequestCategory
from modules.procurement.infrastructure.persistence.django_purchase_request_category_repository import (
    DjangoPurchaseRequestCategoryRepository,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequestCategory as PurchaseRequestCategoryModel,
)


@pytest.mark.django_db
class TestDjangoPurchaseRequestCategoryRepository(TestCase):
    def setUp(self):
        self.it_consumables_account = AccountChart.objects.create(
            code="20000/01/101/021/300", name="IT Consumables", account_type="regular"
        )
        self.discontinued_account = AccountChart.objects.create(
            code="99999/00", name="Discontinued Line", account_type="regular"
        )
        self.active_category = PurchaseRequestCategoryModel.objects.create(
            name="IT Consumables", account_chart=self.it_consumables_account, is_active=True
        )
        self.inactive_category = PurchaseRequestCategoryModel.objects.create(
            name="Discontinued Category", account_chart=self.discontinued_account, is_active=False
        )
        self.repository = DjangoPurchaseRequestCategoryRepository()

    def test_get_by_id_returns_the_matching_category(self):
        result = self.repository.get_by_id(self.active_category.id)

        assert isinstance(result, PurchaseRequestCategory)
        assert result.id == self.active_category.id
        assert result.name == "IT Consumables"
        assert result.account_chart_id == self.it_consumables_account.id
        assert result.is_active is True

    def test_get_by_id_returns_an_inactive_category_too(self):
        """
        get_by_id does not filter by active state - CreatePurchaseRequest
        needs to distinguish "not found" from "found but inactive" to give
        each its own error code, which requires the inactive row itself.
        """
        result = self.repository.get_by_id(self.inactive_category.id)

        assert result is not None
        assert result.is_active is False

    def test_get_by_id_returns_none_for_an_unknown_id(self):
        assert self.repository.get_by_id(999999) is None

    def test_get_all_active_excludes_inactive_categories(self):
        results = self.repository.get_all_active()

        names = [category.name for category in results]
        assert "IT Consumables" in names
        assert "Discontinued Category" not in names

    def test_get_all_active_is_ordered_by_name(self):
        AccountChart.objects.create(code="11111/00", name="A", account_type="regular")
        PurchaseRequestCategoryModel.objects.create(
            name="AAA First Alphabetically",
            account_chart=AccountChart.objects.get(code="11111/00"),
            is_active=True,
        )

        results = self.repository.get_all_active()

        assert [c.name for c in results] == sorted(c.name for c in results)


@pytest.mark.django_db
class TestPurchaseRequestCategoryModelConstraints(TestCase):
    """
    Django-model-level constraints: 'duplicate name' and 'duplicate mapping'
    from F11-A's Section 2/10 requirements ("employee-facing name is unique",
    "duplicate mappings are prevented where appropriate").
    """

    def setUp(self):
        self.account_a = AccountChart.objects.create(
            code="20000/01/101/021/300", name="IT Consumables", account_type="regular"
        )
        self.account_b = AccountChart.objects.create(
            code="20000/01/101/010/300", name="Stationery and Printing", account_type="regular"
        )
        PurchaseRequestCategoryModel.objects.create(
            name="IT Consumables", account_chart=self.account_a, is_active=True
        )

    def test_duplicate_name_is_rejected(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            PurchaseRequestCategoryModel.objects.create(
                name="IT Consumables",  # same name, different account
                account_chart=self.account_b,
                is_active=True,
            )

    def test_two_categories_cannot_map_to_the_same_account_chart_row(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            PurchaseRequestCategoryModel.objects.create(
                name="A Different Name",
                account_chart=self.account_a,  # already mapped above
                is_active=True,
            )
