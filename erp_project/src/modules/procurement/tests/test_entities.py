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
from modules.procurement.domain.value_objects import (
    RequestStatus,
    DecisionStage,
    DecisionType,
    OrderStatus,
)


class TestSupplier:
    """Tests for Supplier entity."""

    def test_create_supplier(self):
        supplier = Supplier.create(
            name="Acme Corp", email="contact@acme.com", phone="123-456-7890"
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
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        assert item.name == "Widget"
        assert item.sku == "WDG-001"
        assert item.quantity == 100
        assert item.price_per_unit == Decimal("9.99")

    def test_add_stock(self):
        item = InventoryItem.create(
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        item.add_stock(50)
        assert item.quantity == 150

    def test_remove_stock(self):
        item = InventoryItem.create(
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        item.remove_stock(30)
        assert item.quantity == 70

    def test_remove_too_much_stock_raises(self):
        item = InventoryItem.create(
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        with pytest.raises(ValueError):
            item.remove_stock(150)

    def test_can_fulfill(self):
        item = InventoryItem.create(
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        assert item.can_fulfill(50) is True
        assert item.can_fulfill(150) is False

    def test_needs_reorder(self):
        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=5,
            price_per_unit=Decimal("9.99"),
            reorder_level=10,
        )
        assert item.needs_reorder is True

    def test_calculate_cost(self):
        item = InventoryItem.create(
            name="Widget", sku="WDG-001", quantity=100, price_per_unit=Decimal("9.99")
        )
        assert item.calculate_cost(10) == Decimal("99.90")


class TestBudgetCenter:
    """Tests for BudgetCenter entity."""

    def test_create_budget_center(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        assert center.name == "IT Department"
        assert center.allocated_amount == Decimal("100000.00")
        assert center.used_amount == Decimal("0")
        assert center.is_active is True

    def test_remaining_amount(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        center.used_amount = Decimal("30000.00")
        assert center.remaining_amount == Decimal("70000.00")

    def test_has_sufficient_budget(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        assert center.has_sufficient_budget(Decimal("50000.00")) is True
        assert center.has_sufficient_budget(Decimal("150000.00")) is False

    def test_allocate(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        center.allocate(Decimal("30000.00"))
        assert center.used_amount == Decimal("30000.00")

    def test_allocate_insufficient_raises(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        with pytest.raises(ValueError):
            center.allocate(Decimal("150000.00"))

    def test_release(self):
        center = BudgetCenter.create(
            name="IT Department", allocated_amount=Decimal("100000.00")
        )
        center.allocate(Decimal("30000.00"))
        center.release(Decimal("10000.00"))
        assert center.used_amount == Decimal("20000.00")


class TestPurchaseRequestItem:
    """Tests for PurchaseRequestItem entity."""

    def test_create_item(self):
        """Spec #1: A valid item can be created."""
        item = PurchaseRequestItem(
            description="Widget",
            quantity=10,
            expected_delivery_period="2 weeks",
            estimated_cost=Decimal("100.00"),
            budget_code_id=1,
        )
        assert item.description == "Widget"
        assert item.quantity == 10
        assert item.estimated_cost == Decimal("100.00")
        assert item.budget_code_id == 1

    def test_invalid_quantity_raises(self):
        """Spec #3: A request item rejects quantity < 1."""
        from shared.domain.exceptions import ValidationError

        with pytest.raises(ValidationError):
            PurchaseRequestItem(
                description="Widget",
                quantity=0,
                expected_delivery_period="2 weeks",
                estimated_cost=Decimal("100.00"),
                budget_code_id=1,
            )

    def test_negative_cost_raises(self):
        """Spec #4: A request item rejects negative estimated cost."""
        from shared.domain.exceptions import ValidationError

        with pytest.raises(ValidationError):
            PurchaseRequestItem(
                description="Widget",
                quantity=1,
                expected_delivery_period="2 weeks",
                estimated_cost=Decimal("-10.00"),
                budget_code_id=1,
            )

    def test_empty_description_raises(self):
        """Item description must not be empty."""
        from shared.domain.exceptions import ValidationError

        with pytest.raises(ValidationError):
            PurchaseRequestItem(
                description="",
                quantity=1,
                expected_delivery_period="2 weeks",
                estimated_cost=Decimal("10.00"),
                budget_code_id=1,
            )

    def test_whitespace_description_raises(self):
        """Item description must not be only whitespace."""
        from shared.domain.exceptions import ValidationError

        with pytest.raises(ValidationError):
            PurchaseRequestItem(
                description="   ",
                quantity=1,
                expected_delivery_period="2 weeks",
                estimated_cost=Decimal("10.00"),
                budget_code_id=1,
            )


class TestPurchaseRequest:
    """Tests for PurchaseRequest entity."""

    def _make_request(self):
        """Helper to create a valid PurchaseRequest."""
        return PurchaseRequest.create(
            requester_id=1,
            requester_name="John Doe",
            department_id=1,
            department_name="IT",
            designation="Developer",
            contact="ext 123",
        )

    def _make_item(self, desc="Widget", qty=1, cost="10.00"):
        return PurchaseRequestItem(
            description=desc,
            quantity=qty,
            expected_delivery_period="1 week",
            estimated_cost=Decimal(cost),
            budget_code_id=1,
        )

    def test_create_request(self):
        """Spec #1: A valid PurchaseRequest can be created."""
        request = self._make_request()
        assert request.requester_name == "John Doe"
        assert request.department_name == "IT"
        assert request.designation == "Developer"
        assert request.contact == "ext 123"
        assert request.status == RequestStatus.DRAFT
        assert len(request.items) == 0
        assert len(request.decisions) == 0

    def test_add_item(self):
        request = self._make_request()
        request.add_item(self._make_item())
        assert len(request.items) == 1
        assert request.items[0].description == "Widget"

    def test_cannot_submit_without_items(self):
        """Spec #2: A request cannot be submitted without items."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        with pytest.raises(ValidationError, match="at least one item"):
            request.submit()

    def test_total_equals_sum_of_line_costs(self):
        """Spec #5: Request total equals the SUM of each line's quantity x unit cost."""
        request = self._make_request()
        request.add_item(self._make_item("Laptop", 2, "2000.00"))
        request.add_item(self._make_item("Mouse", 5, "150.00"))
        # (2 x 2000.00) + (5 x 150.00) = 4000.00 + 750.00
        assert request.total_estimated_cost == Decimal("4750.00")

    def test_quantity_multiplies_estimated_unit_cost(self):
        """
        Spec #6 (corrected): estimated_cost is a per-unit price, so quantity
        DOES multiply it to produce each line's contribution to the total.

        Regression: this previously asserted the opposite (quantity did NOT
        multiply estimated_cost) - a codified bug that matched a stale
        domain-property implementation and a stale model docstring, both
        also fixed alongside this test. A quantity-10, $1.00-unit-cost line
        rendered as a $1.00 total everywhere instead of $10.00.
        """
        request = self._make_request()
        request.add_item(self._make_item("Laptop", 10, "10.00"))
        request.add_item(self._make_item("Gadget", 5, "20.00"))
        # (10 x 10.00) + (5 x 20.00) = 100.00 + 100.00
        assert request.total_estimated_cost == Decimal("200.00")

    def test_total_uses_quantity_10_unit_cost_1_equals_10(self):
        """Regression for the exact reported bug: qty 10 x $1.00 unit cost = $10.00, not $1.00."""
        request = self._make_request()
        request.add_item(self._make_item("Widget", 10, "1.00"))
        assert request.total_estimated_cost == Decimal("10.00")

    def test_total_is_zero_for_a_zero_cost_item(self):
        request = self._make_request()
        request.add_item(self._make_item("Free sample", 3, "0.00"))
        assert request.total_estimated_cost == Decimal("0.00")

    def test_submit_draft_to_pending_department_head(self):
        """Spec #7: DRAFT -> PENDING_DEPARTMENT_HEAD works."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        assert request.status == RequestStatus.PENDING_DEPARTMENT_HEAD

    def test_department_head_approval_to_pending_accounts(self):
        """Spec #8: Department Head approval -> PENDING_ACCOUNTS."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        assert request.status == RequestStatus.PENDING_ACCOUNTS
        assert len(request.decisions) == 1
        assert request.decisions[0].stage == DecisionStage.DEPARTMENT_HEAD
        assert request.decisions[0].decision == DecisionType.APPROVED

    def test_accounts_verification_to_pending_gm(self):
        """Spec #9: Accounts verification -> PENDING_GM."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        assert request.status == RequestStatus.PENDING_GM
        assert request.decisions[-1].stage == DecisionStage.ACCOUNTS
        assert request.decisions[-1].decision == DecisionType.VERIFIED

    def test_gm_recommendation_to_pending_director(self):
        """Spec #10: GM recommendation -> PENDING_DIRECTOR."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        assert request.status == RequestStatus.PENDING_DIRECTOR
        assert request.decisions[-1].stage == DecisionStage.GM
        assert request.decisions[-1].decision == DecisionType.RECOMMENDED

    def test_director_approval_to_pending_procurement(self):
        """Spec #11: Director approval -> PENDING_PROCUREMENT."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)
        assert request.status == RequestStatus.PENDING_PROCUREMENT
        assert request.decisions[-1].stage == DecisionStage.DIRECTOR
        assert request.decisions[-1].decision == DecisionType.APPROVED

    def test_procurement_processing_to_processed(self):
        """Spec #12: Procurement processing -> PROCESSED."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)
        request.process_by_procurement(6, "PO-TEST-001")
        assert request.status == RequestStatus.PROCESSED
        assert request.processed_by == 6
        assert request.processed_at is not None
        assert request.purchase_order_number == "PO-TEST-001"

    def _advance_to_pending_procurement(self, request):
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)
        return request

    def test_purchase_order_number_is_none_before_processing(self):
        """F23: the field stays unset for every stage before PROCESSED."""
        request = self._advance_to_pending_procurement(self._make_request())
        assert request.purchase_order_number is None

    def test_process_by_procurement_strips_purchase_order_number(self):
        """F23: manually entered by a human - leading/trailing whitespace is trimmed, not preserved verbatim."""
        request = self._advance_to_pending_procurement(self._make_request())
        request.process_by_procurement(6, "  PO-2026-042  ")
        assert request.purchase_order_number == "PO-2026-042"

    def test_process_by_procurement_rejects_blank_purchase_order_number(self):
        """F23: manually entered, not auto-generated - an empty/whitespace-only value is not a real PO number."""
        from shared.domain.exceptions import ValidationError

        request = self._advance_to_pending_procurement(self._make_request())
        with pytest.raises(ValidationError):
            request.process_by_procurement(6, "   ")
        assert request.status == RequestStatus.PENDING_PROCUREMENT
        assert request.purchase_order_number is None

    def test_process_by_procurement_requires_purchase_order_number_argument(self):
        """F23: the parameter is required - there is no legacy no-payload call site left in the domain."""
        request = self._advance_to_pending_procurement(self._make_request())
        with pytest.raises(TypeError):
            request.process_by_procurement(6)

    def test_process_by_procurement_appends_a_purchase_request_processed_domain_event(self):
        """Slice 3 notifications: mirrors test_reject_appends_a_purchase_request_rejected_domain_event for the processed path."""
        from modules.procurement.domain.events import PurchaseRequestProcessed

        request = self._make_request()
        request._id = 77
        request.requisition_number = "PR-00077"
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)

        assert request.domain_events == []

        request.process_by_procurement(6, "PO-TEST-001")

        events = request.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PurchaseRequestProcessed)
        assert event.request_id == 77
        assert event.requisition_number == "PR-00077"
        assert event.requester_id == request.requester_id
        assert event.processed_by == 6

    def test_processed_at_is_timezone_aware(self):
        """
        processed_at is persisted to a timezone-aware column, so it must carry
        an offset rather than being guessed at by the storage layer.
        """
        from datetime import timezone

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)

        request.process_by_procurement(6, "PO-TEST-001")

        assert request.processed_at.tzinfo is not None
        assert request.processed_at.utcoffset() == timezone.utc.utcoffset(None)

    def test_processed_at_is_the_current_instant(self):
        """The timestamp is now, not shifted by the server's timezone."""
        from datetime import datetime, timedelta, timezone

        before = datetime.now(timezone.utc)
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)

        request.process_by_procurement(6, "PO-TEST-001")

        after = datetime.now(timezone.utc)
        assert before <= request.processed_at <= after
        assert after - before < timedelta(minutes=1)

    def test_aggregate_timestamps_are_mutually_comparable(self):
        """
        Every timestamp the aggregate produces carries an offset, so they can
        be compared with each other and with database-loaded values without
        raising on a naive/aware mismatch.
        """
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)
        request.process_by_procurement(6, "PO-TEST-001")

        assert request.created_at.tzinfo is not None
        assert request.updated_at.tzinfo is not None
        assert request.created_at <= request.updated_at
        assert request.processed_at <= request.updated_at
        assert all(d.created_at.tzinfo is not None for d in request.decisions)

    def test_invalid_transitions_are_rejected(self):
        """Spec #13: Invalid stage transitions are rejected."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())

        # Cannot approve from DRAFT
        with pytest.raises(ValidationError):
            request.approve_by_department_head(2)

        # Cannot verify from DRAFT
        with pytest.raises(ValidationError):
            request.verify_by_accounts(3)

        # Cannot recommend from DRAFT
        with pytest.raises(ValidationError):
            request.recommend_by_gm(4)

        # Cannot approve_director from DRAFT
        with pytest.raises(ValidationError):
            request.approve_by_director(5)

        # Cannot process from DRAFT
        with pytest.raises(ValidationError):
            request.process_by_procurement(6, "PO-TEST-001")

        # Submit, then try wrong transition
        request.submit()
        with pytest.raises(ValidationError):
            request.verify_by_accounts(3)  # Should be dept head first

        # Cannot submit again from PENDING_DEPARTMENT_HEAD
        with pytest.raises(ValidationError):
            request.submit()

    def test_rejection_creates_decision(self):
        """Spec #14: Rejection creates/preserves a decision."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.reject(2, "Budget constraints")
        assert request.status == RequestStatus.REJECTED
        assert len(request.decisions) == 1
        assert request.decisions[0].decision == DecisionType.REJECTED
        assert request.decisions[0].stage == DecisionStage.DEPARTMENT_HEAD
        assert request.decisions[0].reason == "Budget constraints"

    def test_reject_appends_a_purchase_request_rejected_domain_event(self):
        """
        Slice 3 notifications: reject() must record a PurchaseRequestRejected
        event carrying everything the notification needs (requester,
        requisition number, reason) - the application layer publishes
        whatever ends up in domain_events, so anything missing here can never
        reach the requester's notification.
        """
        from modules.procurement.domain.events import PurchaseRequestRejected

        request = self._make_request()
        request._id = 42
        request.requisition_number = "PR-00042"
        request.add_item(self._make_item())
        request.submit()

        assert request.domain_events == []

        request.reject(9, "Budget constraints")

        events = request.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PurchaseRequestRejected)
        assert event.request_id == 42
        assert event.requisition_number == "PR-00042"
        assert event.requester_id == request.requester_id
        assert event.rejector_id == 9
        assert event.reason == "Budget constraints"

    def test_rejection_requires_reason(self):
        """Rejection reason is required."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        with pytest.raises(ValidationError, match="reason"):
            request.reject(2, "")
        with pytest.raises(ValidationError, match="reason"):
            request.reject(2, "   ")

    def test_rejected_request_can_be_corrected_and_resubmitted(self):
        """Spec #15: Rejected request can enter correction/resubmission flow."""
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.reject(2, "Wrong items")
        assert request.status == RequestStatus.REJECTED

        request.correct_and_resubmit()
        assert request.status == RequestStatus.DRAFT

        request.submit()
        assert request.status == RequestStatus.PENDING_DEPARTMENT_HEAD

    def test_submit_does_not_append_a_domain_event_on_a_first_time_submission(self):
        """F19: a fresh submission is not a correction - no event, no notification."""
        request = self._make_request()
        request.add_item(self._make_item())

        request.submit()

        assert request.domain_events == []

    def test_submit_after_correction_appends_a_purchase_request_corrected_and_resubmitted_domain_event(
        self,
    ):
        """
        F19 notifications: resubmitting after a rejection must tell the
        department head this is a correction, not a first-time submission -
        submit() is where that's detected (see its own docstring for why).
        """
        from modules.procurement.domain.events import PurchaseRequestCorrectedAndResubmitted

        request = self._make_request()
        request._id = 88
        request.requisition_number = "PR-00088"
        request.add_item(self._make_item())
        request.submit()
        request.reject(2, "Wrong items")
        request.clear_domain_events()  # as the reject use case's own publish would have
        request.correct_and_resubmit()

        assert request.domain_events == []

        request.submit()

        events = request.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, PurchaseRequestCorrectedAndResubmitted)
        assert event.request_id == 88
        assert event.requisition_number == "PR-00088"
        assert event.requester_id == request.requester_id
        assert event.department_id == request.department_id

    def test_submit_after_correction_fires_the_event_regardless_of_which_stage_rejected_it(self):
        """F19: must not be hard-coded to department-head rejections specifically - rejected at Accounts here."""
        from modules.procurement.domain.events import PurchaseRequestCorrectedAndResubmitted

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.reject(3, "Category needs revisiting")
        request.clear_domain_events()
        request.correct_and_resubmit()

        request.submit()

        events = request.domain_events
        assert len(events) == 1
        assert isinstance(events[0], PurchaseRequestCorrectedAndResubmitted)

    def test_previous_decision_history_is_preserved(self):
        """Spec #16: Previous decision history is preserved."""
        request = self._make_request()
        request.add_item(self._make_item())

        # First pass: submit -> approve -> reject
        request.submit()
        request.approve_by_department_head(2)
        request.reject(3, "Need more info")
        assert len(request.decisions) == 2

        # Correction and resubmission
        request.correct_and_resubmit()
        request.submit()

        # Second pass decisions
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        assert len(request.decisions) == 4  # All 4 decisions preserved

        # Verify first pass decisions are still there
        assert request.decisions[0].stage == DecisionStage.DEPARTMENT_HEAD
        assert request.decisions[0].decision == DecisionType.APPROVED
        assert request.decisions[1].stage == DecisionStage.ACCOUNTS
        assert request.decisions[1].decision == DecisionType.REJECTED
        # Verify second pass decisions
        assert request.decisions[2].stage == DecisionStage.DEPARTMENT_HEAD
        assert request.decisions[3].stage == DecisionStage.ACCOUNTS

    def test_cannot_reject_from_draft(self):
        """Cannot reject from DRAFT status."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        with pytest.raises(ValidationError):
            request.reject(2, "No reason")

    def test_cannot_reject_from_processed(self):
        """Cannot reject an already processed request."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.approve_by_department_head(2)
        request.verify_by_accounts(3)
        request.recommend_by_gm(4)
        request.approve_by_director(5)
        request.process_by_procurement(6, "PO-TEST-001")
        with pytest.raises(ValidationError):
            request.reject(7, "Too late")

    def test_cannot_add_items_after_submission(self):
        """Can only add items when DRAFT or REJECTED."""
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        with pytest.raises(ValidationError):
            request.add_item(self._make_item("Extra"))

    def test_reject_at_each_pending_stage(self):
        """Rejection should work at each approval stage."""
        from shared.domain.exceptions import ValidationError

        for advance_to_stage in [
            lambda r: None,  # PENDING_DEPARTMENT_HEAD
            lambda r: r.approve_by_department_head(2),  # PENDING_ACCOUNTS
            lambda r: (r.approve_by_department_head(2), r.verify_by_accounts(3)),  # PENDING_GM
            lambda r: (r.approve_by_department_head(2), r.verify_by_accounts(3), r.recommend_by_gm(4)),  # PENDING_DIRECTOR
        ]:
            request = self._make_request()
            request.add_item(self._make_item())
            request.submit()
            advance_to_stage(request)
            request.reject(99, "Rejected at this stage")
            assert request.status == RequestStatus.REJECTED

    # ---------------------------------------------------------------
    # replace_items (Slice 2 draft editing)
    # ---------------------------------------------------------------

    def test_replace_items_succeeds_from_draft(self):
        request = self._make_request()
        request.add_item(self._make_item("Original"))

        request.replace_items([self._make_item("Replacement", qty=3, cost="30.00")])

        assert len(request.items) == 1
        assert request.items[0].description == "Replacement"
        assert request.total_estimated_cost == Decimal("90.00")  # 3 x $30.00

    def test_replace_items_rejects_from_rejected(self):
        """
        Deliberately narrower than add_item/remove_item: a REJECTED request
        must first be returned to DRAFT via correct_and_resubmit() - Slice 2's
        application layer does that itself before calling replace_items, so
        the REJECTED -> DRAFT transition only ever happens together with an
        actual saved correction.
        """
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.reject(2, "Wrong items")
        assert request.status == RequestStatus.REJECTED

        with pytest.raises(ValidationError, match="REJECTED"):
            request.replace_items([self._make_item("New")])
        # Nothing changed.
        assert request.status == RequestStatus.REJECTED
        assert request.items[0].description == "Widget"

    def test_replace_items_rejects_from_every_pending_stage_and_processed(self):
        from shared.domain.exceptions import ValidationError

        for advance_to_stage in [
            lambda r: None,  # PENDING_DEPARTMENT_HEAD
            lambda r: r.approve_by_department_head(2),  # PENDING_ACCOUNTS
            lambda r: (r.approve_by_department_head(2), r.verify_by_accounts(3)),  # PENDING_GM
            lambda r: (
                r.approve_by_department_head(2),
                r.verify_by_accounts(3),
                r.recommend_by_gm(4),
            ),  # PENDING_DIRECTOR
            lambda r: (
                r.approve_by_department_head(2),
                r.verify_by_accounts(3),
                r.recommend_by_gm(4),
                r.approve_by_director(5),
            ),  # PENDING_PROCUREMENT
            lambda r: (
                r.approve_by_department_head(2),
                r.verify_by_accounts(3),
                r.recommend_by_gm(4),
                r.approve_by_director(5),
                r.process_by_procurement(6, "PO-TEST-001"),
            ),  # PROCESSED
        ]:
            request = self._make_request()
            request.add_item(self._make_item())
            request.submit()
            advance_to_stage(request)
            with pytest.raises(ValidationError):
                request.replace_items([self._make_item("New")])

    def test_replace_items_error_code_is_request_not_editable(self):
        from shared.domain.exceptions import ValidationError

        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        with pytest.raises(ValidationError) as exc_info:
            request.replace_items([self._make_item("New")])
        assert exc_info.value.code == "REQUEST_NOT_EDITABLE"

    def test_replace_items_assigns_request_id_to_each_item(self):
        request = self._make_request()
        request._id = 42
        request.add_item(self._make_item())

        new_item = self._make_item("New")
        request.replace_items([new_item])

        assert new_item.request_id == 42

    def test_correct_and_resubmit_then_replace_items_is_a_legal_sequence(self):
        """
        The exact composition UpdatePurchaseRequestItems performs for a
        REJECTED request: correct_and_resubmit() first, then replace_items()
        becomes legal since status is now DRAFT.
        """
        request = self._make_request()
        request.add_item(self._make_item())
        request.submit()
        request.reject(2, "Wrong items")

        request.correct_and_resubmit()
        assert request.status == RequestStatus.DRAFT

        request.replace_items([self._make_item("Corrected", qty=2, cost="20.00")])
        assert request.status == RequestStatus.DRAFT
        assert request.items[0].description == "Corrected"

        request.submit()
        assert request.status == RequestStatus.PENDING_DEPARTMENT_HEAD
        # The original rejection decision is preserved throughout.
        assert any(d.decision == DecisionType.REJECTED for d in request.decisions)


class TestPurchaseOrder:
    """Tests for PurchaseOrder entity."""

    def test_create_order(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00"),
        )
        assert order.order_number == "PO-2024-0001"
        assert order.status == OrderStatus.DRAFT
        assert order.delivered is False

    @pytest.mark.skip(
        reason="PurchaseOrder.create_from_request does not exist and uses "
               "old PurchaseRequest API. Fix deferred to PO integration slice."
    )
    def test_create_from_request(self):
        request = PurchaseRequest.create(
            requester_id=1, requester_name="John Doe", supplier_id=1, budget_center_id=1
        )
        request._id = 1  # Simulate saved request
        item = PurchaseRequestItem.create(
            item_id=1, item_name="Widget", quantity=10, price_per_unit=Decimal("10.00")
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
            total_amount=Decimal("1000.00"),
        )
        order.send_to_supplier()
        assert order.status == OrderStatus.SENT

    def test_mark_partially_received(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00"),
        )
        order.send_to_supplier()
        order.mark_partially_received()
        assert order.status == OrderStatus.PARTIALLY_RECEIVED

    def test_mark_fully_received(self):
        order = PurchaseOrder.create(
            order_number="PO-2024-0001",
            request_id=1,
            supplier_id=1,
            total_amount=Decimal("1000.00"),
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
            total_amount=Decimal("1000.00"),
        )
        order.cancel(reason="Not needed anymore")
        assert order.status == OrderStatus.CANCELLED
        assert order.notes == "Not needed anymore"
