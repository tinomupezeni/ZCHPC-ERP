"""
Django repository implementation for PurchaseOrder.
"""

from decimal import Decimal
from typing import List, Optional

from modules.procurement.infrastructure.persistence.models import (
    PurchaseOrder as PurchaseOrderModel,
    PurchaseRequest as PurchaseRequestModel,
)

from modules.procurement.domain.entities import PurchaseOrder
from modules.procurement.domain.value_objects import OrderStatus
from modules.procurement.application.interfaces import IPurchaseOrderRepository


class DjangoPurchaseOrderRepository(IPurchaseOrderRepository):
    """Django implementation of purchase order repository."""

    def _to_domain(self, model: PurchaseOrderModel) -> PurchaseOrder:
        """Convert Django model to domain entity."""
        # Determine status based on delivered flag
        if model.delivered:
            status = OrderStatus.RECEIVED
        else:
            status = OrderStatus.SENT

        # Get total from request
        total = Decimal(str(model.purchase_request.total_amount))

        return PurchaseOrder(
            id=model.id,
            order_number=model.order_number,
            request_id=model.purchase_request_id,
            supplier_id=model.purchase_request.vendor_id,
            total_amount=total,
            status=status,
            delivered=model.delivered,
            notes=None,  # Not in legacy model
        )

    def _to_model(self, entity: PurchaseOrder) -> PurchaseOrderModel:
        """Convert domain entity to Django model."""
        if entity.id:
            model = PurchaseOrderModel.objects.get(pk=entity.id)
        else:
            model = PurchaseOrderModel()
            model.purchase_request_id = entity.request_id

        model.order_number = entity.order_number
        model.delivered = entity.delivered or entity.status == OrderStatus.RECEIVED
        return model

    def save(self, order: PurchaseOrder) -> PurchaseOrder:
        """Save a purchase order."""
        model = self._to_model(order)
        model.save()
        return self._to_domain(model)

    def get_by_id(self, order_id: int) -> Optional[PurchaseOrder]:
        """Get an order by ID."""
        try:
            model = PurchaseOrderModel.objects.select_related(
                "purchase_request"
            ).get(pk=order_id)
            return self._to_domain(model)
        except PurchaseOrderModel.DoesNotExist:
            return None

    def get_by_order_number(self, order_number: str) -> Optional[PurchaseOrder]:
        """Get an order by order number."""
        try:
            model = PurchaseOrderModel.objects.select_related(
                "purchase_request"
            ).get(order_number=order_number)
            return self._to_domain(model)
        except PurchaseOrderModel.DoesNotExist:
            return None

    def get_by_request_id(self, request_id: int) -> Optional[PurchaseOrder]:
        """Get order by request ID."""
        try:
            model = PurchaseOrderModel.objects.select_related(
                "purchase_request"
            ).get(purchase_request_id=request_id)
            return self._to_domain(model)
        except PurchaseOrderModel.DoesNotExist:
            return None

    def get_all(self) -> List[PurchaseOrder]:
        """Get all orders."""
        queryset = PurchaseOrderModel.objects.select_related(
            "purchase_request"
        ).order_by("-approved_at")
        return [self._to_domain(m) for m in queryset]

    def get_by_status(self, status: OrderStatus) -> List[PurchaseOrder]:
        """Get orders by status."""
        if status == OrderStatus.RECEIVED:
            queryset = PurchaseOrderModel.objects.filter(
                delivered=True
            ).select_related("purchase_request")
        else:
            queryset = PurchaseOrderModel.objects.filter(
                delivered=False
            ).select_related("purchase_request")
        return [self._to_domain(m) for m in queryset]

    def get_by_supplier(self, supplier_id: int) -> List[PurchaseOrder]:
        """Get orders by supplier."""
        queryset = PurchaseOrderModel.objects.filter(
            purchase_request__vendor_id=supplier_id
        ).select_related("purchase_request")
        return [self._to_domain(m) for m in queryset]

    def get_pending_delivery(self) -> List[PurchaseOrder]:
        """Get orders pending delivery."""
        queryset = PurchaseOrderModel.objects.filter(
            delivered=False
        ).select_related("purchase_request")
        return [self._to_domain(m) for m in queryset]

    def delete(self, order_id: int) -> bool:
        """Delete an order (only if draft)."""
        try:
            model = PurchaseOrderModel.objects.get(
                pk=order_id,
                delivered=False
            )
            model.delete()
            return True
        except PurchaseOrderModel.DoesNotExist:
            return False
