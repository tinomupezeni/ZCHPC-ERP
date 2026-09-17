"""
Unit tests for the PurchaseRequestCategory domain entity (Slice F11-A).

No database - pure construction/validation, mirroring how
modules.procurement.domain.entities.purchase_request is exercised (its own
behavior lives in the use-case/repository tests, not a standalone entity
test file); this one is small enough to warrant its own file rather than
being folded into the pre-existing, partly-broken test_entities.py (see
F09-PR's report for why those Supplier/InventoryItem/BudgetCenter/
PurchaseOrder failures are pre-existing and out of scope here).
"""

import pytest

from modules.procurement.domain.entities import PurchaseRequestCategory
from shared.domain.exceptions import ValidationError


class TestPurchaseRequestCategory:
    def test_valid_category(self):
        category = PurchaseRequestCategory(name="IT Consumables", account_chart_id=5)

        assert category.name == "IT Consumables"
        assert category.account_chart_id == 5
        assert category.is_active is True  # default
        assert category.id is None  # unpersisted

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            PurchaseRequestCategory(name="", account_chart_id=5)

    def test_whitespace_only_name_raises(self):
        with pytest.raises(ValidationError):
            PurchaseRequestCategory(name="   ", account_chart_id=5)

    def test_can_be_constructed_inactive(self):
        category = PurchaseRequestCategory(
            name="Discontinued Category", account_chart_id=5, is_active=False
        )

        assert category.is_active is False

    def test_id_is_settable_after_construction(self):
        """
        The repository-facing pattern: construct without an id, then set
        ._id directly - passing id= to the constructor is not supported by
        this entity's base class (AggregateRoot is not itself a dataclass).
        """
        category = PurchaseRequestCategory(name="IT Consumables", account_chart_id=5)
        category._id = 7

        assert category.id == 7
