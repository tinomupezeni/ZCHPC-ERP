"""
Approval workflow domain service.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional, Protocol

from shared.domain.exceptions import ValidationError
from modules.procurement.domain.entities import (
    PurchaseRequest,
    PurchaseOrder,
    BudgetCenter,
)
from modules.procurement.domain.value_objects import RequestStatus


class ApprovalAction(str, Enum):
    """Approval workflow actions."""

    APPROVE_LEVEL1 = "approve_level1"
    APPROVE_LEVEL2 = "approve_level2"
    REJECT = "reject"


@dataclass
class ApprovalResult:
    """Result of an approval action."""

    success: bool
    request: PurchaseRequest
    order: Optional[PurchaseOrder] = None
    message: str = ""

    @property
    def order_number(self) -> Optional[str]:
        """Get order number if order was created."""
        return self.order.order_number if self.order else None


class BudgetAllocator(Protocol):
    """Protocol for budget allocation."""

    def allocate(self, budget_center_id: int, amount: Decimal) -> None:
        """Allocate budget amount."""
        ...

    def release(self, budget_center_id: int, amount: Decimal) -> None:
        """Release allocated budget."""
        ...


class ApprovalWorkflow:
    """
    Domain service for purchase request approval workflow.

    Handles the multi-level approval process:
    - Level 1: Manager approval (validates budget)
    - Level 2: Finance approval (allocates budget, creates PO)
    - Reject: Can be done at any pending level
    """

    def __init__(self, budget_allocator: BudgetAllocator) -> None:
        self._budget_allocator = budget_allocator

    def approve_level1(
        self,
        request: PurchaseRequest,
        approver_id: int,
        budget_center: BudgetCenter
    ) -> ApprovalResult:
        """
        Process Level 1 approval.

        Validates that:
        - Request is in PENDING status
        - Budget center has sufficient funds

        Args:
            request: The purchase request to approve
            approver_id: ID of the approving manager
            budget_center: The budget center to check

        Returns:
            ApprovalResult with updated request

        Raises:
            ValidationError: If validation fails
        """
        # Validate request status
        if not request.status.can_approve_level1:
            return ApprovalResult(
                success=False,
                request=request,
                message=f"Cannot approve. Status: {request.status.value}"
            )

        # Validate budget
        if not budget_center.has_sufficient_budget(request.total_amount):
            return ApprovalResult(
                success=False,
                request=request,
                message=(
                    f"Insufficient budget. Required: {request.total_amount}, "
                    f"Available: {budget_center.remaining_amount}"
                )
            )

        # Approve
        request.approve_level1(approver_id)

        return ApprovalResult(
            success=True,
            request=request,
            message="Level 1 approval successful"
        )

    def approve_level2(
        self,
        request: PurchaseRequest,
        approver_id: int
    ) -> ApprovalResult:
        """
        Process Level 2 approval.

        This is the final approval that:
        - Allocates the budget
        - Creates a Purchase Order

        Args:
            request: The purchase request to approve
            approver_id: ID of the approving manager

        Returns:
            ApprovalResult with updated request and created PO

        Raises:
            ValidationError: If validation fails
        """
        # Validate request status
        if not request.status.can_approve_level2:
            return ApprovalResult(
                success=False,
                request=request,
                message=f"Cannot approve Level 2. Status: {request.status.value}"
            )

        # Allocate budget
        self._budget_allocator.allocate(
            budget_center_id=request.budget_center_id,
            amount=request.total_amount
        )

        # Approve the request
        request.approve_level2(approver_id)

        # Create Purchase Order
        order = PurchaseOrder.create_from_request(
            request_id=request.id,
            supplier_id=request.supplier_id,
            total_amount=request.total_amount
        )

        return ApprovalResult(
            success=True,
            request=request,
            order=order,
            message=f"Level 2 approval successful. PO: {order.order_number}"
        )

    def reject(
        self,
        request: PurchaseRequest,
        rejector_id: int,
        reason: Optional[str] = None
    ) -> ApprovalResult:
        """
        Reject a purchase request.

        If the request was at Level 1 approved, no budget release needed
        since budget wasn't allocated yet.

        Args:
            request: The purchase request to reject
            rejector_id: ID of the person rejecting
            reason: Optional rejection reason

        Returns:
            ApprovalResult with rejected request
        """
        # Validate request status
        if not request.status.can_reject:
            return ApprovalResult(
                success=False,
                request=request,
                message=f"Cannot reject. Status: {request.status.value}"
            )

        # Reject
        request.reject(rejector_id, reason)

        return ApprovalResult(
            success=True,
            request=request,
            message=f"Request rejected. Reason: {reason or 'No reason provided'}"
        )

    def can_user_approve_level1(
        self,
        request: PurchaseRequest,
        user_id: int
    ) -> bool:
        """
        Check if user can approve at Level 1.

        Basic check - in real implementation would check permissions.

        Args:
            request: The request to check
            user_id: The user attempting to approve

        Returns:
            True if user can approve
        """
        # Cannot approve own request
        if request.requester_id == user_id:
            return False

        return request.status.can_approve_level1

    def can_user_approve_level2(
        self,
        request: PurchaseRequest,
        user_id: int
    ) -> bool:
        """
        Check if user can approve at Level 2.

        Args:
            request: The request to check
            user_id: The user attempting to approve

        Returns:
            True if user can approve
        """
        # Cannot approve own request
        if request.requester_id == user_id:
            return False

        # Cannot be same as Level 1 approver
        if request.level1_approved_by == user_id:
            return False

        return request.status.can_approve_level2

    def get_pending_actions(
        self,
        request: PurchaseRequest
    ) -> list[ApprovalAction]:
        """
        Get available actions for a request.

        Args:
            request: The request to check

        Returns:
            List of available actions
        """
        actions = []

        if request.status.can_approve_level1:
            actions.append(ApprovalAction.APPROVE_LEVEL1)
            actions.append(ApprovalAction.REJECT)
        elif request.status.can_approve_level2:
            actions.append(ApprovalAction.APPROVE_LEVEL2)
            actions.append(ApprovalAction.REJECT)

        return actions
