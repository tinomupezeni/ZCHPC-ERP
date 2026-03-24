"""
Tests for procurement services.
"""

import pytest
from decimal import Decimal
from typing import List, Optional
from unittest.mock import MagicMock

from modules.procurement.domain.entities import (
    Supplier,
    InventoryItem,
    BudgetCenter,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseOrder,
)
from modules.procurement.domain.value_objects import RequestStatus, OrderStatus
from modules.procurement.domain.services import (
    BudgetChecker,
    ApprovalWorkflow,
)
from modules.procurement.application.interfaces import (
    ISupplierRepository,
    IInventoryItemRepository,
    IBudgetCenterRepository,
    IPurchaseRequestRepository,
    IPurchaseOrderRepository,
)
from modules.procurement.application.services import (
    ProcurementService,
    CreatePurchaseRequestDTO,
    RequestItemDTO,
)


# Test fixtures

@pytest.fixture
def sample_supplier():
    supplier = Supplier.create(
        name="Acme Corp",
        email="contact@acme.com"
    )
    supplier._id = 1
    return supplier


@pytest.fixture
def sample_item():
    item = InventoryItem.create(
        name="Widget",
        sku="WDG-001",
        quantity=100,
        price_per_unit=Decimal("10.00")
    )
    item._id = 1
    return item


@pytest.fixture
def sample_budget_center():
    center = BudgetCenter.create(
        name="IT Department",
        allocated_amount=Decimal("100000.00")
    )
    center._id = 1
    return center


@pytest.fixture
def sample_request(sample_item):
    request = PurchaseRequest.create(
        requester_id=1,
        requester_name="John Doe",
        supplier_id=1,
        budget_center_id=1
    )
    request._id = 1
    item = PurchaseRequestItem.create(
        item_id=1,
        item_name="Widget",
        quantity=10,
        price_per_unit=Decimal("10.00")
    )
    request.add_item(item)
    return request


# BudgetChecker Tests

class TestBudgetChecker:
    """Tests for BudgetChecker domain service."""

    def test_check_budget_sufficient(self, sample_budget_center):
        budget_repo = MagicMock(spec=IBudgetCenterRepository)
        budget_repo.get_by_id.return_value = sample_budget_center

        checker = BudgetChecker(budget_repo)
        result = checker.check_budget(
            budget_center_id=1,
            requested_amount=Decimal("50000.00")
        )

        assert result.has_sufficient_budget is True
        assert result.remaining_amount == Decimal("100000.00")

    def test_check_budget_insufficient(self, sample_budget_center):
        sample_budget_center.used_amount = Decimal("80000.00")

        budget_repo = MagicMock(spec=IBudgetCenterRepository)
        budget_repo.get_by_id.return_value = sample_budget_center

        checker = BudgetChecker(budget_repo)
        result = checker.check_budget(
            budget_center_id=1,
            requested_amount=Decimal("30000.00")
        )

        assert result.has_sufficient_budget is False
        assert result.remaining_amount == Decimal("20000.00")

    def test_check_budget_not_found(self):
        budget_repo = MagicMock(spec=IBudgetCenterRepository)
        budget_repo.get_by_id.return_value = None

        checker = BudgetChecker(budget_repo)
        result = checker.check_budget(
            budget_center_id=999,
            requested_amount=Decimal("1000.00")
        )

        assert result.has_sufficient_budget is False


# ApprovalWorkflow Tests

class TestApprovalWorkflow:
    """Tests for ApprovalWorkflow domain service."""

    def test_approve_level1_success(self, sample_request, sample_budget_center):
        allocator = MagicMock()
        workflow = ApprovalWorkflow(allocator)

        result = workflow.approve_level1(
            request=sample_request,
            approver_id=2,
            budget_center=sample_budget_center
        )

        assert result.success is True
        assert result.request.status == RequestStatus.LEVEL1_APPROVED

    def test_approve_level1_insufficient_budget(self, sample_request, sample_budget_center):
        sample_budget_center.used_amount = Decimal("99950.00")

        allocator = MagicMock()
        workflow = ApprovalWorkflow(allocator)

        result = workflow.approve_level1(
            request=sample_request,
            approver_id=2,
            budget_center=sample_budget_center
        )

        assert result.success is False
        assert "Insufficient budget" in result.message

    def test_approve_level2_success(self, sample_request):
        sample_request.approve_level1(approver_id=2)

        allocator = MagicMock()
        workflow = ApprovalWorkflow(allocator)

        result = workflow.approve_level2(
            request=sample_request,
            approver_id=3
        )

        assert result.success is True
        assert result.request.status == RequestStatus.LEVEL2_APPROVED
        assert result.order is not None
        assert result.order.status == OrderStatus.DRAFT
        allocator.allocate.assert_called_once()

    def test_approve_level2_wrong_status(self, sample_request):
        allocator = MagicMock()
        workflow = ApprovalWorkflow(allocator)

        result = workflow.approve_level2(
            request=sample_request,
            approver_id=3
        )

        assert result.success is False

    def test_reject_request(self, sample_request):
        allocator = MagicMock()
        workflow = ApprovalWorkflow(allocator)

        result = workflow.reject(
            request=sample_request,
            rejector_id=2,
            reason="Over budget"
        )

        assert result.success is True
        assert result.request.status == RequestStatus.REJECTED
        assert result.request.rejection_reason == "Over budget"


# ProcurementService Tests

class MockSupplierRepository(ISupplierRepository):
    """Mock supplier repository for testing."""

    def __init__(self):
        self._suppliers = {}

    def save(self, supplier: Supplier) -> Supplier:
        if supplier.id is None:
            supplier._id = len(self._suppliers) + 1
        self._suppliers[supplier.id] = supplier
        return supplier

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        return self._suppliers.get(supplier_id)

    def get_all(self, include_inactive: bool = False) -> List[Supplier]:
        return list(self._suppliers.values())

    def get_active(self) -> List[Supplier]:
        return [s for s in self._suppliers.values() if s.is_active]

    def search(self, query: str) -> List[Supplier]:
        return [s for s in self._suppliers.values() if query.lower() in s.name.lower()]

    def delete(self, supplier_id: int) -> bool:
        if supplier_id in self._suppliers:
            del self._suppliers[supplier_id]
            return True
        return False


class MockItemRepository(IInventoryItemRepository):
    """Mock inventory item repository for testing."""

    def __init__(self):
        self._items = {}

    def save(self, item: InventoryItem) -> InventoryItem:
        if item.id is None:
            item._id = len(self._items) + 1
        self._items[item.id] = item
        return item

    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        return self._items.get(item_id)

    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        for item in self._items.values():
            if item.sku == sku:
                return item
        return None

    def get_all(self, include_inactive: bool = False) -> List[InventoryItem]:
        return list(self._items.values())

    def get_low_stock(self) -> List[InventoryItem]:
        return [i for i in self._items.values() if i.needs_reorder]

    def delete(self, item_id: int) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False


class MockBudgetCenterRepository(IBudgetCenterRepository):
    """Mock budget center repository for testing."""

    def __init__(self):
        self._centers = {}

    def save(self, center: BudgetCenter) -> BudgetCenter:
        if center.id is None:
            center._id = len(self._centers) + 1
        self._centers[center.id] = center
        return center

    def get_by_id(self, center_id: int) -> Optional[BudgetCenter]:
        return self._centers.get(center_id)

    def get_by_code(self, code: str) -> Optional[BudgetCenter]:
        for center in self._centers.values():
            if center.code == code:
                return center
        return None

    def get_all(self, include_inactive: bool = False) -> List[BudgetCenter]:
        return list(self._centers.values())

    def get_by_fiscal_year(self, year: int) -> List[BudgetCenter]:
        return [c for c in self._centers.values() if c.fiscal_year == year]

    def allocate_budget(self, center_id: int, amount: Decimal) -> BudgetCenter:
        center = self._centers.get(center_id)
        if center:
            center.allocate(amount)
        return center

    def release_budget(self, center_id: int, amount: Decimal) -> BudgetCenter:
        center = self._centers.get(center_id)
        if center:
            center.release(amount)
        return center

    def delete(self, center_id: int) -> bool:
        if center_id in self._centers:
            del self._centers[center_id]
            return True
        return False


class MockRequestRepository(IPurchaseRequestRepository):
    """Mock purchase request repository for testing."""

    def __init__(self):
        self._requests = {}

    def save(self, request: PurchaseRequest) -> PurchaseRequest:
        if request.id is None:
            request._id = len(self._requests) + 1
        self._requests[request.id] = request
        return request

    def get_by_id(self, request_id: int) -> Optional[PurchaseRequest]:
        return self._requests.get(request_id)

    def get_all(self) -> List[PurchaseRequest]:
        return list(self._requests.values())

    def get_by_status(self, status: RequestStatus) -> List[PurchaseRequest]:
        return [r for r in self._requests.values() if r.status == status]

    def get_pending(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING)

    def get_pending_level1(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING)

    def get_pending_level2(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.LEVEL1_APPROVED)

    def get_by_requester(self, requester_id: int) -> List[PurchaseRequest]:
        return [r for r in self._requests.values() if r.requester_id == requester_id]

    def get_by_budget_center(self, center_id: int) -> List[PurchaseRequest]:
        return [r for r in self._requests.values() if r.budget_center_id == center_id]

    def update_status(self, request_id: int, status: RequestStatus) -> PurchaseRequest:
        request = self._requests.get(request_id)
        if request:
            request._status = status
        return request

    def delete(self, request_id: int) -> bool:
        request = self._requests.get(request_id)
        if request and request.status == RequestStatus.PENDING:
            del self._requests[request_id]
            return True
        return False


class MockOrderRepository(IPurchaseOrderRepository):
    """Mock purchase order repository for testing."""

    def __init__(self):
        self._orders = {}

    def save(self, order: PurchaseOrder) -> PurchaseOrder:
        if order.id is None:
            order._id = len(self._orders) + 1
        self._orders[order.id] = order
        return order

    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        return self._orders.get(order_id)

    def get_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        for order in self._orders.values():
            if order.order_number == order_number:
                return order
        return None

    def get_by_request_id(self, request_id: int) -> Optional[PurchaseOrder]:
        for order in self._orders.values():
            if order.request_id == request_id:
                return order
        return None

    def get_all(self) -> List[PurchaseOrder]:
        return list(self._orders.values())

    def get_by_status(self, status: OrderStatus) -> List[PurchaseOrder]:
        return [o for o in self._orders.values() if o.status == status]

    def get_by_supplier(self, supplier_id: int) -> List[PurchaseOrder]:
        return [o for o in self._orders.values() if o.supplier_id == supplier_id]

    def get_pending_delivery(self) -> List[PurchaseOrder]:
        return [o for o in self._orders.values() if not o.delivered]

    def delete(self, order_id: int) -> bool:
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.DRAFT:
            del self._orders[order_id]
            return True
        return False


class TestProcurementService:
    """Tests for ProcurementService application service."""

    @pytest.fixture
    def service(self):
        supplier_repo = MockSupplierRepository()
        item_repo = MockItemRepository()
        budget_repo = MockBudgetCenterRepository()
        request_repo = MockRequestRepository()
        order_repo = MockOrderRepository()

        # Create test data
        supplier = Supplier.create(name="Acme Corp", email="contact@acme.com")
        supplier_repo.save(supplier)

        item = InventoryItem.create(
            name="Widget",
            sku="WDG-001",
            quantity=100,
            price_per_unit=Decimal("10.00")
        )
        item_repo.save(item)

        center = BudgetCenter.create(
            name="IT Department",
            allocated_amount=Decimal("100000.00")
        )
        budget_repo.save(center)

        service = ProcurementService(
            supplier_repo=supplier_repo,
            item_repo=item_repo,
            budget_repo=budget_repo,
            request_repo=request_repo,
            order_repo=order_repo,
        )

        return service

    def test_create_purchase_request(self, service):
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1,
            items=[
                RequestItemDTO(item_id=1, quantity=5)
            ]
        )

        request = service.create_purchase_request(dto)

        assert request.id is not None
        assert request.requester_name == "John Doe"
        assert len(request.items) == 1
        assert request.total_amount == Decimal("50.00")

    def test_approve_level1(self, service):
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1,
            items=[
                RequestItemDTO(item_id=1, quantity=5)
            ]
        )
        request = service.create_purchase_request(dto)

        approved_request = service.approve_level1(
            request_id=request.id,
            approver_id=2
        )

        assert approved_request.status == RequestStatus.LEVEL1_APPROVED

    def test_approve_level2_creates_order(self, service):
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1,
            items=[
                RequestItemDTO(item_id=1, quantity=5)
            ]
        )
        request = service.create_purchase_request(dto)
        service.approve_level1(request_id=request.id, approver_id=2)

        approved_request, order = service.approve_level2(
            request_id=request.id,
            approver_id=3
        )

        assert approved_request.status == RequestStatus.LEVEL2_APPROVED
        assert order is not None
        assert order.total_amount == Decimal("50.00")

    def test_reject_request(self, service):
        dto = CreatePurchaseRequestDTO(
            requester_id=1,
            requester_name="John Doe",
            supplier_id=1,
            budget_center_id=1,
            items=[
                RequestItemDTO(item_id=1, quantity=5)
            ]
        )
        request = service.create_purchase_request(dto)

        rejected = service.reject_request(
            request_id=request.id,
            rejector_id=2,
            reason="Not approved"
        )

        assert rejected.status == RequestStatus.REJECTED
        assert rejected.rejection_reason == "Not approved"
