"""
Django repository implementation for PurchaseRequest.
"""

from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest as PurchaseRequestModel,
    PurchaseRequestItem as PurchaseRequestItemModel,
    InventoryItem as InventoryItemModel,
)

from modules.procurement.domain.entities import PurchaseRequest, PurchaseRequestItem
from modules.procurement.domain.value_objects import RequestStatus
from modules.procurement.application.interfaces import IPurchaseRequestRepository


class DjangoPurchaseRequestRepository(IPurchaseRequestRepository):
    """Django implementation of purchase request repository."""

    # Map domain status to model status
    _STATUS_TO_MODEL = {
        RequestStatus.PENDING: "PENDING",
        RequestStatus.LEVEL1_APPROVED: "LEVEL1_APPROVED",
        RequestStatus.LEVEL2_APPROVED: "LEVEL2_APPROVED",
        RequestStatus.REJECTED: "REJECTED",
        RequestStatus.CANCELLED: "REJECTED",  # Legacy has no CANCELLED
    }

    _STATUS_FROM_MODEL = {
        "PENDING": RequestStatus.PENDING,
        "LEVEL1_APPROVED": RequestStatus.LEVEL1_APPROVED,
        "LEVEL2_APPROVED": RequestStatus.LEVEL2_APPROVED,
        "REJECTED": RequestStatus.REJECTED,
    }

    def _item_to_domain(
        self,
        model: PurchaseRequestItemModel,
        request_id: int
    ) -> PurchaseRequestItem:
        """Convert item model to domain entity."""
        return PurchaseRequestItem(
            id=model.id,
            request_id=request_id,
            item_id=model.item.id,
            item_name=model.item.name,
            quantity=model.quantity,
            price_per_unit=Decimal(str(model.item.price_per_unit)),
        )

    def _to_domain(self, model: PurchaseRequestModel) -> PurchaseRequest:
        """Convert Django model to domain entity."""
        # Load items
        item_models = PurchaseRequestItemModel.objects.filter(
            purchase_request=model
        ).select_related("item")

        items = [
            self._item_to_domain(item_model, model.id)
            for item_model in item_models
        ]

        return PurchaseRequest(
            id=model.id,
            requester_id=0,  # Not in legacy model
            requester_name=model.requester,
            supplier_id=model.vendor_id,
            budget_center_id=model.budget_center_id,
            status=self._STATUS_FROM_MODEL.get(
                model.status,
                RequestStatus.PENDING
            ),
            items=items,
            rejection_reason=None,  # Not in legacy model
            level1_approver_id=None,  # Not in legacy model
            level2_approver_id=None,  # Not in legacy model
        )

    @transaction.atomic
    def save(self, request: PurchaseRequest) -> PurchaseRequest:
        """Save a purchase request with its items."""
        # Save or update the request
        if request.id:
            model = PurchaseRequestModel.objects.get(pk=request.id)
        else:
            model = PurchaseRequestModel()

        model.requester = request.requester_name
        model.vendor_id = request.supplier_id
        model.budget_center_id = request.budget_center_id
        model.status = self._STATUS_TO_MODEL.get(
            request.status,
            "PENDING"
        )
        model.total_amount = request.total_amount
        model.save()

        # Delete existing items and recreate
        if request.id:
            PurchaseRequestItemModel.objects.filter(
                purchase_request=model
            ).delete()

        # Save items
        for item in request.items:
            item_model = PurchaseRequestItemModel(
                purchase_request=model,
                item_id=item.item_id,
                quantity=item.quantity,
            )
            item_model.save()

        return self._to_domain(model)

    def get_by_id(self, request_id: int) -> Optional[PurchaseRequest]:
        """Get a request by ID with all items."""
        try:
            model = PurchaseRequestModel.objects.get(pk=request_id)
            return self._to_domain(model)
        except PurchaseRequestModel.DoesNotExist:
            return None

    def get_all(self) -> List[PurchaseRequest]:
        """Get all requests."""
        queryset = PurchaseRequestModel.objects.all().order_by("-created_at")
        return [self._to_domain(m) for m in queryset]

    def get_by_status(self, status: RequestStatus) -> List[PurchaseRequest]:
        """Get requests by status."""
        model_status = self._STATUS_TO_MODEL.get(status, "PENDING")
        queryset = PurchaseRequestModel.objects.filter(
            status=model_status
        ).order_by("-created_at")
        return [self._to_domain(m) for m in queryset]

    def get_pending(self) -> List[PurchaseRequest]:
        """Get pending requests."""
        return self.get_by_status(RequestStatus.PENDING)

    def get_pending_level1(self) -> List[PurchaseRequest]:
        """Get requests pending Level 1 approval."""
        return self.get_by_status(RequestStatus.PENDING)

    def get_pending_level2(self) -> List[PurchaseRequest]:
        """Get requests pending Level 2 approval."""
        return self.get_by_status(RequestStatus.LEVEL1_APPROVED)

    def get_by_requester(self, requester_id: int) -> List[PurchaseRequest]:
        """Get requests by requester."""
        # Legacy model doesn't have requester_id, return all
        return self.get_all()

    def get_by_budget_center(
        self,
        budget_center_id: int
    ) -> List[PurchaseRequest]:
        """Get requests by budget center."""
        queryset = PurchaseRequestModel.objects.filter(
            budget_center_id=budget_center_id
        ).order_by("-created_at")
        return [self._to_domain(m) for m in queryset]

    def update_status(
        self,
        request_id: int,
        status: RequestStatus
    ) -> PurchaseRequest:
        """Update request status."""
        model = PurchaseRequestModel.objects.get(pk=request_id)
        model.status = self._STATUS_TO_MODEL.get(status, "PENDING")
        model.save()
        return self._to_domain(model)

    def delete(self, request_id: int) -> bool:
        """Delete a request (only if pending)."""
        try:
            model = PurchaseRequestModel.objects.get(
                pk=request_id,
                status="PENDING"
            )
            model.delete()
            return True
        except PurchaseRequestModel.DoesNotExist:
            return False
