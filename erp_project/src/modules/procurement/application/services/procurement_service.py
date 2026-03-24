"""
Application service for procurement operations.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.procurement.domain.entities import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseOrder,
)
from modules.procurement.domain.value_objects import RequestStatus
from modules.procurement.domain.services import (
    BudgetChecker,
    ApprovalWorkflow,
    ApprovalResult,
)
from modules.procurement.application.interfaces import (
    ISupplierRepository,
    IInventoryItemRepository,
    IBudgetCenterRepository,
    IPurchaseRequestRepository,
    IPurchaseOrderRepository,
)


@dataclass
class RequestItemDTO:
    """DTO for a purchase request item."""

    item_id: int
    quantity: int


@dataclass
class CreatePurchaseRequestDTO:
    """DTO for creating a purchase request."""

    requester_id: int
    requester_name: str
    supplier_id: int
    budget_center_id: int
    items: List[RequestItemDTO] = field(default_factory=list)


class BudgetAllocatorAdapter:
    """Adapter to provide BudgetAllocator interface for domain service."""

    def __init__(self, budget_repo: IBudgetCenterRepository) -> None:
        self._budget_repo = budget_repo

    def allocate(self, budget_center_id: int, amount: Decimal) -> None:
        """Allocate budget amount."""
        self._budget_repo.allocate_budget(budget_center_id, amount)

    def release(self, budget_center_id: int, amount: Decimal) -> None:
        """Release allocated budget."""
        self._budget_repo.release_budget(budget_center_id, amount)


class ProcurementService:
    """
    Application service for procurement operations.

    Coordinates purchase request creation and approval workflow.
    """

    def __init__(
        self,
        supplier_repo: ISupplierRepository,
        item_repo: IInventoryItemRepository,
        budget_repo: IBudgetCenterRepository,
        request_repo: IPurchaseRequestRepository,
        order_repo: IPurchaseOrderRepository
    ) -> None:
        self._supplier_repo = supplier_repo
        self._item_repo = item_repo
        self._budget_repo = budget_repo
        self._request_repo = request_repo
        self._order_repo = order_repo

        # Initialize domain services
        self._budget_checker = BudgetChecker(budget_repo)
        self._budget_allocator = BudgetAllocatorAdapter(budget_repo)
        self._approval_workflow = ApprovalWorkflow(self._budget_allocator)

    def create_purchase_request(
        self,
        dto: CreatePurchaseRequestDTO
    ) -> PurchaseRequest:
        """
        Create a new purchase request.

        Args:
            dto: Request creation data

        Returns:
            Created purchase request

        Raises:
            NotFoundError: If supplier, budget center, or items not found
            ValidationError: If validation fails
        """
        # Validate supplier exists
        supplier = self._supplier_repo.get_by_id(dto.supplier_id)
        if supplier is None:
            raise NotFoundError(f"Supplier {dto.supplier_id} not found")
        if not supplier.is_active:
            raise ValidationError("Supplier is not active")

        # Validate budget center exists
        budget_center = self._budget_repo.get_by_id(dto.budget_center_id)
        if budget_center is None:
            raise NotFoundError(f"Budget center {dto.budget_center_id} not found")
        if not budget_center.is_active:
            raise ValidationError("Budget center is not active")

        # Create request
        request = PurchaseRequest.create(
            requester_id=dto.requester_id,
            requester_name=dto.requester_name,
            supplier_id=dto.supplier_id,
            budget_center_id=dto.budget_center_id
        )

        # Add items
        for item_dto in dto.items:
            item = self._item_repo.get_by_id(item_dto.item_id)
            if item is None:
                raise NotFoundError(f"Item {item_dto.item_id} not found")

            request_item = PurchaseRequestItem.create(
                item_id=item.id,
                item_name=item.name,
                quantity=item_dto.quantity,
                price_per_unit=item.price_per_unit
            )
            request.add_item(request_item)

        # Validate request
        request.validate()

        # Save and return
        return self._request_repo.save(request)

    def approve_level1(
        self,
        request_id: int,
        approver_id: int
    ) -> PurchaseRequest:
        """
        Approve a request at Level 1 (manager approval).

        Validates budget availability but doesn't allocate yet.

        Args:
            request_id: ID of the request to approve
            approver_id: ID of the approving manager

        Returns:
            Updated purchase request

        Raises:
            NotFoundError: If request not found
            ValidationError: If approval fails
        """
        request = self._request_repo.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        budget_center = self._budget_repo.get_by_id(request.budget_center_id)
        if budget_center is None:
            raise NotFoundError(
                f"Budget center {request.budget_center_id} not found"
            )

        # Process approval
        result = self._approval_workflow.approve_level1(
            request=request,
            approver_id=approver_id,
            budget_center=budget_center
        )

        if not result.success:
            raise ValidationError(result.message)

        return self._request_repo.save(result.request)

    def approve_level2(
        self,
        request_id: int,
        approver_id: int
    ) -> tuple[PurchaseRequest, PurchaseOrder]:
        """
        Approve a request at Level 2 (finance approval).

        Allocates budget and creates Purchase Order.

        Args:
            request_id: ID of the request to approve
            approver_id: ID of the approving manager

        Returns:
            Tuple of (updated request, created order)

        Raises:
            NotFoundError: If request not found
            ValidationError: If approval fails
        """
        request = self._request_repo.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        # Process approval
        result = self._approval_workflow.approve_level2(
            request=request,
            approver_id=approver_id
        )

        if not result.success:
            raise ValidationError(result.message)

        # Save both request and order
        saved_request = self._request_repo.save(result.request)
        saved_order = self._order_repo.save(result.order)

        return saved_request, saved_order

    def reject_request(
        self,
        request_id: int,
        rejector_id: int,
        reason: Optional[str] = None
    ) -> PurchaseRequest:
        """
        Reject a purchase request.

        Args:
            request_id: ID of the request to reject
            rejector_id: ID of the person rejecting
            reason: Optional rejection reason

        Returns:
            Updated purchase request

        Raises:
            NotFoundError: If request not found
            ValidationError: If rejection fails
        """
        request = self._request_repo.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")

        result = self._approval_workflow.reject(
            request=request,
            rejector_id=rejector_id,
            reason=reason
        )

        if not result.success:
            raise ValidationError(result.message)

        return self._request_repo.save(result.request)

    def get_request(self, request_id: int) -> PurchaseRequest:
        """Get a purchase request by ID."""
        request = self._request_repo.get_by_id(request_id)
        if request is None:
            raise NotFoundError(f"Purchase request {request_id} not found")
        return request

    def list_requests(
        self,
        status: Optional[str] = None,
        requester_id: Optional[int] = None,
        budget_center_id: Optional[int] = None
    ) -> List[PurchaseRequest]:
        """
        List purchase requests with optional filtering.

        Args:
            status: Optional status filter
            requester_id: Optional requester filter
            budget_center_id: Optional budget center filter

        Returns:
            List of purchase requests
        """
        if status:
            try:
                parsed_status = RequestStatus(status)
                return self._request_repo.get_by_status(parsed_status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")

        if requester_id:
            return self._request_repo.get_by_requester(requester_id)

        if budget_center_id:
            return self._request_repo.get_by_budget_center(budget_center_id)

        return self._request_repo.get_all()

    def get_pending_approvals(
        self,
        level: int = 1
    ) -> List[PurchaseRequest]:
        """
        Get requests pending approval at a specific level.

        Args:
            level: Approval level (1 or 2)

        Returns:
            List of pending requests
        """
        if level == 1:
            return self._request_repo.get_pending_level1()
        elif level == 2:
            return self._request_repo.get_pending_level2()
        else:
            raise ValidationError("Level must be 1 or 2")

    def send_order_to_supplier(self, order_id: int) -> PurchaseOrder:
        """
        Send a purchase order to the supplier.

        Args:
            order_id: ID of the order to send

        Returns:
            Updated purchase order
        """
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Purchase order {order_id} not found")

        order.send_to_supplier()
        return self._order_repo.save(order)

    def mark_goods_received(
        self,
        order_id: int,
        is_partial: bool = False
    ) -> PurchaseOrder:
        """
        Mark goods as received for an order.

        Args:
            order_id: ID of the order
            is_partial: True if partial delivery

        Returns:
            Updated purchase order
        """
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Purchase order {order_id} not found")

        if is_partial:
            order.mark_partially_received()
        else:
            order.mark_fully_received()

        return self._order_repo.save(order)

    def cancel_order(
        self,
        order_id: int,
        reason: Optional[str] = None
    ) -> PurchaseOrder:
        """
        Cancel a purchase order.

        Releases allocated budget back to budget center.

        Args:
            order_id: ID of the order to cancel
            reason: Optional cancellation reason

        Returns:
            Cancelled purchase order
        """
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Purchase order {order_id} not found")

        # Get associated request to find budget center
        request = self._request_repo.get_by_id(order.request_id)
        if request:
            # Release the allocated budget
            self._budget_repo.release_budget(
                request.budget_center_id,
                order.total_amount
            )

        order.cancel(reason)
        return self._order_repo.save(order)

    def get_order(self, order_id: int) -> PurchaseOrder:
        """Get a purchase order by ID."""
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Purchase order {order_id} not found")
        return order

    def get_order_by_number(self, order_number: str) -> PurchaseOrder:
        """Get a purchase order by order number."""
        order = self._order_repo.get_by_order_number(order_number)
        if order is None:
            raise NotFoundError(
                f"Purchase order with number '{order_number}' not found"
            )
        return order

    def list_orders(
        self,
        supplier_id: Optional[int] = None,
        pending_delivery: bool = False
    ) -> List[PurchaseOrder]:
        """
        List purchase orders with optional filtering.

        Args:
            supplier_id: Optional supplier filter
            pending_delivery: Only show orders pending delivery

        Returns:
            List of purchase orders
        """
        if pending_delivery:
            return self._order_repo.get_pending_delivery()

        if supplier_id:
            return self._order_repo.get_by_supplier(supplier_id)

        return self._order_repo.get_all()
