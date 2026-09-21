"""
Django repository implementation for PurchaseRequest.
"""

from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestItem as PurchaseRequestItemModel,
    PurchaseRequestDecision as PurchaseRequestDecisionModel,
)

from modules.procurement.domain.entities import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestDecision,
)
from modules.procurement.domain.value_objects import (
    RequestStatus,
    DecisionStage,
    DecisionType,
)
from modules.procurement.application.interfaces import IPurchaseRequestRepository


class DjangoPurchaseRequestRepository(IPurchaseRequestRepository):
    """Django implementation of purchase request repository."""

    def _item_to_domain(
        self, model: PurchaseRequestItemModel, request_id: int
    ) -> PurchaseRequestItem:
        """Convert item model to domain entity."""
        item = PurchaseRequestItem(
            request_id=request_id,
            description=model.description,
            quantity=model.quantity,
            expected_delivery_period=model.expected_delivery_period,
            estimated_cost=Decimal(str(model.estimated_cost)),
            budget_code_id=model.budget_code_id,
        )
        item._id = model.id
        return item

    def _to_domain(self, model: PurchaseRequestModel) -> PurchaseRequest:
        """Convert Django model to domain entity."""

        # Load items
        item_models = PurchaseRequestItemModel.objects.filter(purchase_request=model)
        items = [
            self._item_to_domain(item_model, model.id) for item_model in item_models
        ]

        # Load decisions
        decision_models = PurchaseRequestDecisionModel.objects.filter(
            purchase_request=model
        ).order_by("created_at")
        decisions = []
        for d in decision_models:
            dec = PurchaseRequestDecision(
                purchase_request_id=model.id,
                stage=DecisionStage(d.stage),
                decision=DecisionType(d.decision),
                actor_id=d.actor_id,
                reason=d.reason,
                created_at=d.created_at,
            )
            dec._id = d.id
            decisions.append(dec)

        requester_name = (
            f"{model.requester.first_name} {model.requester.surname}".strip()
        )
        department_name = model.department.name

        pr = PurchaseRequest(
            requester_id=model.requester_id,
            requester_name=requester_name,
            department_id=model.department_id,
            department_name=department_name,
            designation=model.designation,
            contact=model.contact,
            requisition_number=model.requisition_number,
            status=RequestStatus(model.status),
            items=items,
            decisions=decisions,
            processed_by=model.processed_by_id,
            processed_at=model.processed_at,
            purchase_order_number=model.purchase_order_number,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        pr._id = model.id
        return pr

    @transaction.atomic
    def save(self, request: PurchaseRequest) -> PurchaseRequest:
        """Save a purchase request with its items and decisions."""
        # Save or update the request
        if request.id:
            model = PurchaseRequestModel.objects.get(pk=request.id)
        else:
            model = PurchaseRequestModel()

        model.requester_id = request.requester_id
        model.department_id = request.department_id
        model.designation = request.designation
        model.contact = request.contact
        model.status = request.status.value
        model.total_estimated_cost = request.total_estimated_cost
        model.processed_by_id = request.processed_by
        model.processed_at = request.processed_at
        model.purchase_order_number = request.purchase_order_number
        model.save()

        # Pull the auto-generated requisition_number back into the domain
        request.requisition_number = model.requisition_number
        request._id = model.id

        # Save items safely without losing IDs
        current_item_ids = {item.id for item in request.items if item.id is not None}

        # Delete removed items
        PurchaseRequestItemModel.objects.filter(purchase_request=model).exclude(
            id__in=current_item_ids
        ).delete()

        # Update or create items
        for item in request.items:
            if item.id:
                item_model = PurchaseRequestItemModel.objects.get(id=item.id)
                item_model.description = item.description
                item_model.quantity = item.quantity
                item_model.expected_delivery_period = item.expected_delivery_period
                item_model.estimated_cost = item.estimated_cost
                item_model.budget_code_id = item.budget_code_id
                item_model.save()
            else:
                item_model = PurchaseRequestItemModel.objects.create(
                    purchase_request=model,
                    description=item.description,
                    quantity=item.quantity,
                    expected_delivery_period=item.expected_delivery_period,
                    estimated_cost=item.estimated_cost,
                    budget_code_id=item.budget_code_id,
                )
                item._id = item_model.id

        # Append-only for decisions: only insert decisions that don't exist yet
        existing_decision_ids = set(
            PurchaseRequestDecisionModel.objects.filter(
                purchase_request=model
            ).values_list("id", flat=True)
        )
        for decision in request.decisions:
            if decision.id not in existing_decision_ids:
                PurchaseRequestDecisionModel.objects.create(
                    purchase_request=model,
                    stage=decision.stage.value,
                    decision=decision.decision.value,
                    actor_id=decision.actor_id,
                    reason=decision.reason,
                    # created_at is auto_now_add on the Django model
                )

        return self._to_domain(model)

    def _get_queryset(self):
        return PurchaseRequestModel.objects.select_related("requester", "department")

    def get_by_id(self, request_id: int) -> Optional[PurchaseRequest]:
        """Get a request by ID with all items and decisions."""
        try:
            model = self._get_queryset().get(pk=request_id)
            return self._to_domain(model)
        except PurchaseRequestModel.DoesNotExist:
            return None

    def get_all(self) -> List[PurchaseRequest]:
        """Get all requests."""
        queryset = self._get_queryset().order_by("-created_at")
        return [self._to_domain(m) for m in queryset]

    def get_by_status(self, status: RequestStatus) -> List[PurchaseRequest]:
        """Get requests by status."""
        queryset = (
            self._get_queryset().filter(status=status.value).order_by("-created_at")
        )
        return [self._to_domain(m) for m in queryset]

    def get_pending_department_head(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING_DEPARTMENT_HEAD)

    def get_pending_accounts(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING_ACCOUNTS)

    def get_pending_gm(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING_GM)

    def get_pending_director(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING_DIRECTOR)

    def get_pending_procurement(self) -> List[PurchaseRequest]:
        return self.get_by_status(RequestStatus.PENDING_PROCUREMENT)

    def get_by_requester(self, requester_id: int) -> List[PurchaseRequest]:
        """Get requests by requester."""
        queryset = (
            self._get_queryset()
            .filter(requester_id=requester_id)
            .order_by("-created_at")
        )
        return [self._to_domain(m) for m in queryset]

    def exists_by_purchase_order_number(self, purchase_order_number: str) -> bool:
        return PurchaseRequestModel.objects.filter(
            purchase_order_number=purchase_order_number
        ).exists()

    def delete(self, request_id: int) -> bool:
        """Delete a request (only if draft)."""
        try:
            model = PurchaseRequestModel.objects.get(
                pk=request_id, status=RequestStatus.DRAFT.value
            )
            model.delete()
            return True
        except PurchaseRequestModel.DoesNotExist:
            return False
