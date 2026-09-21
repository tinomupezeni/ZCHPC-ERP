"""
PurchaseRequest aggregate root with line items.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot, Entity
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.events import (
    PurchaseRequestCorrectedAndResubmitted,
    PurchaseRequestProcessed,
    PurchaseRequestRejected,
)
from modules.procurement.domain.value_objects import (
    RequestStatus,
    DecisionStage,
    DecisionType,
)


def _utc_now() -> datetime:
    """
    Current instant as a timezone-aware UTC datetime.

    Timestamps produced here are persisted against timezone-aware columns, so
    they must carry an offset - a naive value would be guessed at by the
    storage layer and silently shifted by the server's timezone.

    Uses the standard library rather than django.utils.timezone so the domain
    layer stays free of framework imports.
    """
    return datetime.now(timezone.utc)


@dataclass
class PurchaseRequestDecision(Entity[int]):
    """Immutable decision record for a purchase request."""

    stage: DecisionStage
    decision: DecisionType
    actor_id: int
    reason: str = ""
    purchase_request_id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not hasattr(self, "_id"):
            self._id = None


@dataclass
class PurchaseRequestItem(Entity[int]):
    """Entity representing a line item in a purchase request."""

    description: str
    quantity: int
    expected_delivery_period: str
    estimated_cost: Decimal
    budget_code_id: int
    request_id: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate request item."""
        if not hasattr(self, "_id"):
            self._id = None
        if not self.description or not self.description.strip():
            raise ValidationError("Item description must not be empty")
        if self.quantity < 1:
            raise ValidationError("Quantity must be >= 1")
        if self.estimated_cost < 0:
            raise ValidationError("Estimated cost must be >= 0")


@dataclass
class PurchaseRequest(AggregateRoot[int]):
    """
    Aggregate root for purchase requests.
    """

    requester_id: int
    requester_name: str
    department_id: int
    department_name: str
    designation: str
    contact: str
    requisition_number: str = ""
    status: RequestStatus = RequestStatus.DRAFT
    items: List[PurchaseRequestItem] = field(default_factory=list)
    decisions: List[PurchaseRequestDecision] = field(default_factory=list)
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    purchase_order_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate purchase request initialization."""
        if not hasattr(self, "_id"):
            self._id = None
        if not hasattr(self, "_domain_events"):
            self._domain_events = []
        if not self.requester_name or not self.requester_name.strip():
            raise ValidationError("Requester name must not be empty")
        if not self.designation or not self.designation.strip():
            raise ValidationError("Designation must not be empty")

    @property
    def total_estimated_cost(self) -> Decimal:
        """Sum of each line's quantity x estimated unit cost - estimated_cost is a per-unit price, not a line total."""
        return sum(
            (item.quantity * item.estimated_cost for item in self.items), Decimal("0")
        )

    def validate_for_submission(self) -> None:
        if not self.items:
            raise ValidationError("Purchase request must have at least one item")
        if self.total_estimated_cost < 0:
            raise ValidationError("Total estimated cost must be non-negative")

    def _append_decision(
        self,
        stage: DecisionStage,
        decision: DecisionType,
        actor_id: int,
        reason: str = "",
    ):
        now = _utc_now()
        decision_obj = PurchaseRequestDecision(
            purchase_request_id=self.id,
            stage=stage,
            decision=decision,
            actor_id=actor_id,
            reason=reason,
            created_at=now,
        )
        decision_obj._id = None
        self.decisions.append(decision_obj)

    def submit(self) -> None:
        """
        DRAFT -> PENDING_DEPARTMENT_HEAD.

        F19: DRAFT is reached two ways - a brand-new request that has never
        had a decision made on it, or a REJECTED request returned to DRAFT by
        correct_and_resubmit() (which never touches `decisions`). Decisions
        only ever accumulate via approve/verify/recommend/reject, none of
        which can run while DRAFT - so a non-empty `decisions` here can only
        mean this DRAFT came from a correction, regardless of which stage
        rejected it or how many times. That is what distinguishes a
        first-time submission (no event) from a corrected resubmission
        (PurchaseRequestCorrectedAndResubmitted), without hard-coding any
        particular stage.
        """
        if self.status != RequestStatus.DRAFT:
            raise ValidationError(f"Cannot submit from status {self.status.value}")
        self.validate_for_submission()
        is_corrected_resubmission = bool(self.decisions)
        self.status = RequestStatus.PENDING_DEPARTMENT_HEAD
        self.updated_at = _utc_now()
        if is_corrected_resubmission:
            self.add_domain_event(
                PurchaseRequestCorrectedAndResubmitted(
                    request_id=self.id,
                    requisition_number=self.requisition_number,
                    requester_id=self.requester_id,
                    department_id=self.department_id,
                )
            )

    def approve_by_department_head(self, actor_id: int) -> None:
        if self.status != RequestStatus.PENDING_DEPARTMENT_HEAD:
            raise ValidationError(
                f"Invalid status for department head approval: {self.status.value}"
            )
        self.status = RequestStatus.PENDING_ACCOUNTS
        self._append_decision(
            DecisionStage.DEPARTMENT_HEAD, DecisionType.APPROVED, actor_id
        )
        self.updated_at = _utc_now()

    def verify_by_accounts(self, actor_id: int) -> None:
        if self.status != RequestStatus.PENDING_ACCOUNTS:
            raise ValidationError(
                f"Invalid status for accounts verification: {self.status.value}"
            )
        self.status = RequestStatus.PENDING_GM
        self._append_decision(DecisionStage.ACCOUNTS, DecisionType.VERIFIED, actor_id)
        self.updated_at = _utc_now()

    def recommend_by_gm(self, actor_id: int) -> None:
        if self.status != RequestStatus.PENDING_GM:
            raise ValidationError(
                f"Invalid status for GM recommendation: {self.status.value}"
            )
        self.status = RequestStatus.PENDING_DIRECTOR
        self._append_decision(DecisionStage.GM, DecisionType.RECOMMENDED, actor_id)
        self.updated_at = _utc_now()

    def approve_by_director(self, actor_id: int) -> None:
        if self.status != RequestStatus.PENDING_DIRECTOR:
            raise ValidationError(
                f"Invalid status for director approval: {self.status.value}"
            )
        self.status = RequestStatus.PENDING_PROCUREMENT
        self._append_decision(DecisionStage.DIRECTOR, DecisionType.APPROVED, actor_id)
        self.updated_at = _utc_now()

    def process_by_procurement(self, actor_id: int, purchase_order_number: str) -> None:
        """
        PENDING_PROCUREMENT -> PROCESSED.

        purchase_order_number is manually entered by the Procurement Officer
        (F23) - never auto-generated, unlike requisition_number. It is
        recorded exactly once, here, at the same moment the request becomes
        PROCESSED; nothing else in the aggregate ever assigns or clears it,
        so once set it is effectively immutable - there is no domain method
        that transitions a PROCESSED request anywhere else.
        """
        if self.status != RequestStatus.PENDING_PROCUREMENT:
            raise ValidationError(
                f"Invalid status for procurement processing: {self.status.value}"
            )
        if not purchase_order_number or not purchase_order_number.strip():
            raise ValidationError("Purchase order number is required")
        self.status = RequestStatus.PROCESSED
        self.processed_by = actor_id
        self.processed_at = _utc_now()
        self.purchase_order_number = purchase_order_number.strip()
        self.updated_at = _utc_now()
        self.add_domain_event(
            PurchaseRequestProcessed(
                request_id=self.id,
                requisition_number=self.requisition_number,
                requester_id=self.requester_id,
                processed_by=actor_id,
            )
        )

    def reject(self, actor_id: int, reason: str) -> None:
        if not reason or not reason.strip():
            raise ValidationError("Rejection reason is required")

        stage = None
        if self.status == RequestStatus.PENDING_DEPARTMENT_HEAD:
            stage = DecisionStage.DEPARTMENT_HEAD
        elif self.status == RequestStatus.PENDING_ACCOUNTS:
            stage = DecisionStage.ACCOUNTS
        elif self.status == RequestStatus.PENDING_GM:
            stage = DecisionStage.GM
        elif self.status == RequestStatus.PENDING_DIRECTOR:
            stage = DecisionStage.DIRECTOR
        else:
            raise ValidationError(f"Cannot reject from status {self.status.value}")

        self.status = RequestStatus.REJECTED
        self._append_decision(stage, DecisionType.REJECTED, actor_id, reason)
        self.updated_at = _utc_now()
        self.add_domain_event(
            PurchaseRequestRejected(
                request_id=self.id,
                requisition_number=self.requisition_number,
                requester_id=self.requester_id,
                rejector_id=actor_id,
                reason=reason,
            )
        )

    def correct_and_resubmit(self) -> None:
        if self.status != RequestStatus.REJECTED:
            raise ValidationError(
                f"Can only correct and resubmit rejected requests. Current: {self.status.value}"
            )
        self.status = RequestStatus.DRAFT
        self.updated_at = _utc_now()

    def add_item(self, item: PurchaseRequestItem) -> None:
        if self.status not in (RequestStatus.DRAFT, RequestStatus.REJECTED):
            raise ValidationError("Can only add items when DRAFT or REJECTED")
        item.request_id = self.id
        self.items.append(item)
        self.updated_at = _utc_now()

    def remove_item(self, index: int) -> bool:
        if self.status not in (RequestStatus.DRAFT, RequestStatus.REJECTED):
            raise ValidationError("Can only remove items when DRAFT or REJECTED")
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.updated_at = _utc_now()
            return True
        return False

    def replace_items(self, items: List[PurchaseRequestItem]) -> None:
        """
        Replace the entire item collection (Slice 2 draft editing).

        DRAFT only - deliberately narrower than add_item/remove_item's
        DRAFT-or-REJECTED guard. A REJECTED request must first be returned to
        DRAFT via correct_and_resubmit(); UpdatePurchaseRequestItems (the
        application layer) does exactly that immediately before calling this,
        as one atomic save, so the REJECTED -> DRAFT transition only ever
        happens together with an actual saved correction - never merely
        because an employee opened the editor and then walked away.
        """
        if self.status != RequestStatus.DRAFT:
            raise ValidationError(
                f"Cannot edit items from status {self.status.value}",
                code="REQUEST_NOT_EDITABLE",
            )
        for item in items:
            item.request_id = self.id
        self.items = items
        self.updated_at = _utc_now()

    @classmethod
    def create(
        cls,
        requester_id: int,
        requester_name: str,
        department_id: int,
        department_name: str,
        designation: str,
        contact: str,
    ) -> "PurchaseRequest":
        now = _utc_now()
        pr = cls(
            requester_id=requester_id,
            requester_name=requester_name,
            department_id=department_id,
            department_name=department_name,
            designation=designation,
            contact=contact,
            status=RequestStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        pr._id = None
        return pr
