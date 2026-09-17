"""
Tests for procurement value objects.
"""

import pytest
from decimal import Decimal

from modules.procurement.domain.value_objects import (
    RequestStatus,
    DecisionStage,
    DecisionType,
    OrderStatus,
    Money,
    VendorRating,
    OrderNumber,
    SKU,
    BudgetAllocation,
)


class TestRequestStatus:
    """Tests for RequestStatus enum."""

    def test_draft_status(self):
        status = RequestStatus.DRAFT
        assert status.value == "DRAFT"

    def test_pending_department_head_status(self):
        status = RequestStatus.PENDING_DEPARTMENT_HEAD
        assert status.value == "PENDING_DEPARTMENT_HEAD"

    def test_pending_accounts_status(self):
        status = RequestStatus.PENDING_ACCOUNTS
        assert status.value == "PENDING_ACCOUNTS"

    def test_pending_gm_status(self):
        status = RequestStatus.PENDING_GM
        assert status.value == "PENDING_GM"

    def test_pending_director_status(self):
        status = RequestStatus.PENDING_DIRECTOR
        assert status.value == "PENDING_DIRECTOR"

    def test_pending_procurement_status(self):
        status = RequestStatus.PENDING_PROCUREMENT
        assert status.value == "PENDING_PROCUREMENT"

    def test_processed_status(self):
        status = RequestStatus.PROCESSED
        assert status.value == "PROCESSED"

    def test_rejected_status(self):
        status = RequestStatus.REJECTED
        assert status.value == "REJECTED"

    def test_all_statuses_present(self):
        expected = {
            "DRAFT", "PENDING_DEPARTMENT_HEAD", "PENDING_ACCOUNTS",
            "PENDING_GM", "PENDING_DIRECTOR", "PENDING_PROCUREMENT",
            "PROCESSED", "REJECTED",
        }
        assert {s.value for s in RequestStatus} == expected


class TestDecisionStage:
    """Tests for DecisionStage enum."""

    def test_all_stages(self):
        assert DecisionStage.DEPARTMENT_HEAD.value == "DEPARTMENT_HEAD"
        assert DecisionStage.ACCOUNTS.value == "ACCOUNTS"
        assert DecisionStage.GM.value == "GM"
        assert DecisionStage.DIRECTOR.value == "DIRECTOR"

    def test_stage_count(self):
        assert len(DecisionStage) == 4


class TestDecisionType:
    """Tests for DecisionType enum."""

    def test_all_types(self):
        assert DecisionType.APPROVED.value == "APPROVED"
        assert DecisionType.VERIFIED.value == "VERIFIED"
        assert DecisionType.RECOMMENDED.value == "RECOMMENDED"
        assert DecisionType.REJECTED.value == "REJECTED"

    def test_type_count(self):
        assert len(DecisionType) == 4


class TestOrderStatus:
    """Tests for OrderStatus enum."""

    def test_draft_status(self):
        status = OrderStatus.DRAFT
        assert status.value == "Draft"
        assert status.is_draft

    def test_sent_status(self):
        status = OrderStatus.SENT
        assert status.is_sent

    def test_received_status(self):
        status = OrderStatus.RECEIVED
        assert status.is_received

    def test_cancelled_status(self):
        status = OrderStatus.CANCELLED
        assert status.is_cancelled


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self):
        money = Money(amount=Decimal("100.00"))
        assert money.amount == Decimal("100.00")
        assert money.currency == "USD"

    def test_money_with_currency(self):
        money = Money(amount=Decimal("100.00"), currency="EUR")
        assert money.currency == "EUR"

    def test_money_negative_raises_error(self):
        with pytest.raises(ValueError):
            Money(amount=Decimal("-10.00"))

    def test_money_addition(self):
        m1 = Money(amount=Decimal("100.00"))
        m2 = Money(amount=Decimal("50.00"))
        result = m1 + m2
        assert result.amount == Decimal("150.00")

    def test_money_subtraction(self):
        m1 = Money(amount=Decimal("100.00"))
        m2 = Money(amount=Decimal("30.00"))
        result = m1 - m2
        assert result.amount == Decimal("70.00")

    def test_money_multiplication(self):
        money = Money(amount=Decimal("100.00"))
        result = money * 3
        assert result.amount == Decimal("300.00")

    def test_money_different_currency_raises(self):
        m1 = Money(amount=Decimal("100.00"), currency="USD")
        m2 = Money(amount=Decimal("50.00"), currency="EUR")
        with pytest.raises(ValueError):
            m1 + m2


class TestVendorRating:
    """Tests for VendorRating value object."""

    def test_create_rating(self):
        rating = VendorRating(value=Decimal("4.5"))
        assert rating.value == Decimal("4.5")

    def test_rating_out_of_range_raises(self):
        with pytest.raises(ValueError):
            VendorRating(value=Decimal("5.5"))
        with pytest.raises(ValueError):
            VendorRating(value=Decimal("-1.0"))

    def test_rating_descriptor(self):
        assert VendorRating(Decimal("4.5")).descriptor == "Excellent"
        assert VendorRating(Decimal("3.5")).descriptor == "Good"
        assert VendorRating(Decimal("2.5")).descriptor == "Average"
        assert VendorRating(Decimal("1.5")).descriptor == "Below Average"
        assert VendorRating(Decimal("0.5")).descriptor == "Poor"


class TestOrderNumber:
    """Tests for OrderNumber value object."""

    def test_create_order_number(self):
        order_num = OrderNumber(value="PO-2024-0001")
        assert order_num.value == "PO-2024-0001"

    def test_generate_order_number(self):
        order_num = OrderNumber.generate(123)
        assert order_num.value.startswith("PO-")
        assert "0123" in order_num.value

    def test_empty_order_number_raises(self):
        with pytest.raises(ValueError):
            OrderNumber(value="")


class TestSKU:
    """Tests for SKU value object."""

    def test_create_sku(self):
        sku = SKU(value="ITEM-001")
        assert sku.value == "ITEM-001"

    def test_empty_sku_raises(self):
        with pytest.raises(ValueError):
            SKU(value="")


class TestBudgetAllocation:
    """Tests for BudgetAllocation value object."""

    def test_create_allocation(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("3000.00")
        )
        assert allocation.allocated_amount == Decimal("10000.00")
        assert allocation.used_amount == Decimal("3000.00")

    def test_remaining_amount(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("3000.00")
        )
        assert allocation.remaining_amount == Decimal("7000.00")

    def test_utilization_rate(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("3000.00")
        )
        assert allocation.utilization_rate == Decimal("30.00")

    def test_is_exhausted(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("10000.00")
        )
        assert allocation.is_exhausted

    def test_can_allocate(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("3000.00")
        )
        assert allocation.can_allocate(Decimal("5000.00"))
        assert not allocation.can_allocate(Decimal("8000.00"))

    def test_allocate(self):
        allocation = BudgetAllocation(
            allocated_amount=Decimal("10000.00"),
            used_amount=Decimal("3000.00")
        )
        new_allocation = allocation.allocate(Decimal("2000.00"))
        assert new_allocation.used_amount == Decimal("5000.00")
        assert allocation.used_amount == Decimal("3000.00")  # Immutable
