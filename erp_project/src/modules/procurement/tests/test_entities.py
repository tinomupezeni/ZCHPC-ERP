"""
Tests for procurement entities.
"""

import pytest
from decimal import Decimal

from modules.procurement.domain.entities import (
    Supplier,
    InventoryItem,
    BudgetCenter,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseOrder,
)
from modules.procurement.domain.value_objects import RequestStatus, OrderStatus


class TestSupplier:
    """Tests for Supplier entity."""

    def test_create_supplier(self):
        supplier = Supplier.create(
            name="Acme Corp",
            email="contact@acme.com",
            phone="123-456-7890"
        )
        assert supplier.name == "Acme Corp"
        assert supplier.email == "contact@acme.com"
        assert supplier.is_active is True
        assert supplier.rating == Decimal("0")

    def test_update_details(self):
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        supplier.update_details(name="Acme Corporation", phone="555-1234")
        assert supplier.name == "Acme Corporation"
        assert supplier.phone == "555-1234"

    def test_update_rating(self):
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        supplier.update_rating(Decimal("4.5"))
        assert supplier.rating == Decimal("4.5")

    def test_update_rating_invalid_raises(self):
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        with pytest.raises(ValueError):
            supplier.update_rating(Decimal("6.0"))

    def test_deactivate_supplier(self):
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        supplier.deactivate()
        assert supplier.is_active is False

    def test_activate_supplier(self):
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        supplier.deactivate()
        supplier.activate()
        assert supplier.is_active is True


class TestInventoryItem:
    """Tests for InventoryItem entity."""

    def test_create_item(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        assert item.name == "Widget"
        assert item.sku == "WDG-001"
        assert item.quantity == 100
        assert item.price_per_unit == Decimal("9.99")

    def test_add_stock(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        item.add_stock(50)
        assert item.quantity == 150

    def test_remove_stock(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        item.remove_stock(30)
        assert item.quantity == 70

    def test_remove_too_much_stock_raises(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        with pytest.raises(ValueError):
            item.remove_stock(150)

    def test_can_fulfill(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        assert item.can_fulfill(50) is True
        assert item.can_fulfill(150) is False

    def test_needs_reorder(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=5,
            price_per_unit=Decimal("9.99"),
            reorder_level=10
        )
        assert item.needs_reorder is True

    def test_calculate_cost(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("9.99")
        )
        assert item.calculate_cost(10) == Decimal("99.90")


class TestBudgetCenter:
    """Tests for BudgetCenter entity."""

    def test_create_budget_center(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        assert center.name == "IT Department"
        assert center.allocated_amount == Decimal("100000.00")
        assert center.used_amount == Decimal("0")
        assert center.is_active is True

    def test_remaining_amount(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        center.used_amount = Decimal("30000.00")
        assert center.remaining_amount == Decimal("70000.00")

    def test_has_sufficient_budget(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        assert center.has_sufficient_budget(Decimal("50000.00")) is True
        assert center.has_sufficient_budget(Decimal("150000.00")) is False

    def test_allocate(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        center.allocate(Decimal("30000.00"))
        assert center.used_amount == Decimal("30000.00")

    def test_allocate_insufficient_raises(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        with pytest.raises(ValueError):
            center.allocate(Decimal("150000.00"))

    def test_release(self):
        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        center.allocate(Decimal("30000.00"))
        center.release(Decimal("10000.00"))
        assert center.used_amount == Decimal("20000.00")


class TestPurchaseRequestItem:
    """Tests for PurchaseRequestItem entity."""

    def test_create_item(self):
        item = PurchaseRequestItem.create(
            item_id=1,
            item_name="Widget",
            quantity=10,
            price_per_unit=Decimal("9.99")
        )
        assert item.item_id == 1
        assert item.item_name == "Widget"
        assert item.quantity == 10
        assert item.price_per_unit == Decimal("9.99")

    def test_total_cost(self):
        item = PurchaseRequestItem.create(
            item_id=1,
            item_name="Widget",
            quantity=10,
            price_per_unit=Decimal("9.99")
        )
        assert item.total_cost == Decimal("99.90")


class TestPurchaseRequest:
    """Tests for PurchaseRequest entity."""

    def test_create_request(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        assert request.requester_name == "John Doe"
        assert request.status == RequestStatus.PENDING
        assert len(request.items) == 0

    def test_add_item(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        item = PurchaseRequestItem.create(
            item_id=1,
            item_name="Widget",
            quantity=10,
            price_per_unit=Decimal("9.99")
        )
        request.add_item(item)
        assert len(request.items) == 1
        assert request.items[0].item_name == "Widget"

    def test_total_amount(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        item1 = PurchaseRequestItem.create(
            item_id=1,
            item_name="Widget",
            quantity=10,
            price_per_unit=Decimal("10.00")
        )
        item2 = PurchaseRequestItem.create(
            item_id=2,
            item_name="Gadget",
            quantity=5,
            price_per_unit=Decimal("20.00")
        )
        request.add_item(item1)
        request.add_item(item2)
        assert request.total_amount == Decimal("200.00")

    def test_approve_level1(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        request.approve_level1(approver_id=2)
        assert request.status == RequestStatus.LEVEL1_APPROVED
        assert request.level1_approver_id == 2

    def test_approve_level1_invalid_status_raises(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        request.approve_level1(approver_id=2)
        with pytest.raises(ValueError):
            request.approve_level1(approver_id=3)

    def test_approve_level2(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        request.approve_level1(approver_id=2)
        request.approve_level2(approver_id=3)
        assert request.status == RequestStatus.LEVEL2_APPROVED
        assert request.level2_approver_id == 3

    def test_reject(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        request.reject(rejector_id=2, reason="Budget constraints")
        assert request.status == RequestStatus.REJECTED
        assert request.rejection_reason == "Budget constraints"


class TestPurchaseOrder:
    """Tests for PurchaseOrder entity."""

    def test_create_order(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00")
        )
        assert order.order_number == "PO-2024-0001"
        assert order.status == OrderStatus.DRAFT
        assert order.delivered is False

    def test_create_from_request(self):
        request = PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1
        )
        request._id = 1  # Simulate saved request
        item = PurchaseRequestItem.create(
            item_id=1,
            item_name="Widget",
            quantity=10,
            price_per_unit=Decimal("10.00")
        )
        request.add_item(item)

        order = PurchaseOrder.create_from_request(request, "PO-2024-0001")
        assert order.request_id == 1
        assert order.supplier_id == 1
        assert order.total_amount == Decimal("100.00")

    def test_send_to_supplier(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00")
        )
        order.send_to_supplier()
        assert order.status == OrderStatus.SENT

    def test_mark_partially_received(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00")
        )
        order.send_to_supplier()
        order.mark_partially_received()
        assert order.status == OrderStatus.PARTIALLY_RECEIVED

    def test_mark_fully_received(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00")
        )
        order.send_to_supplier()
        order.mark_fully_received()
        assert order.status == OrderStatus.RECEIVED
        assert order.delivered is True

    def test_cancel(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00")
        )
        order.cancel(reason="Not needed anymore")
        assert order.status == OrderStatus.CANCELLED
        assert order.notes == "Not needed anymore"
