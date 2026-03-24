"""
Django repository implementation for InventoryItem.
"""

from decimal import Decimal
from typing import List, Optional

from modules.procurement.infrastructure.persistence.models import InventoryItem as InventoryItemModel

from modules.procurement.domain.entities import InventoryItem
from modules.procurement.application.interfaces import IInventoryItemRepository


class DjangoInventoryItemRepository(IInventoryItemRepository):
    """Django implementation of inventory item repository."""

    def _to_domain(self, model: InventoryItemModel) -> InventoryItem:
        """Convert Django model to domain entity."""
        return InventoryItem(
            id=model.id,
            name=model.name,
            sku=model.sku,
            quantity=model.quantity,
            price_per_unit=Decimal(str(model.price_per_unit)),
            reorder_level=0,  # Not in legacy model
            is_active=True,   # Not in legacy model
        )

    def _to_model(self, entity: InventoryItem) -> InventoryItemModel:
        """Convert domain entity to Django model."""
        if entity.id:
            model = InventoryItemModel.objects.get(pk=entity.id)
        else:
            model = InventoryItemModel()

        model.name = entity.name
        model.sku = entity.sku
        model.quantity = entity.quantity
        model.price_per_unit = entity.price_per_unit
        return model

    def save(self, item: InventoryItem) -> InventoryItem:
        """Save an inventory item."""
        model = self._to_model(item)
        model.save()
        return self._to_domain(model)

    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        """Get an item by ID."""
        try:
            model = InventoryItemModel.objects.get(pk=item_id)
            return self._to_domain(model)
        except InventoryItemModel.DoesNotExist:
            return None

    def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """Get an item by SKU."""
        try:
            model = InventoryItemModel.objects.get(sku=sku)
            return self._to_domain(model)
        except InventoryItemModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[InventoryItem]:
        """Get all items."""
        # Legacy model doesn't have is_active, return all
        queryset = InventoryItemModel.objects.all()
        return [self._to_domain(m) for m in queryset]

    def get_low_stock(self) -> List[InventoryItem]:
        """Get items that need reordering."""
        # Legacy model doesn't have reorder_level, use a default threshold
        queryset = InventoryItemModel.objects.filter(quantity__lt=10)
        return [self._to_domain(m) for m in queryset]

    def delete(self, item_id: int) -> bool:
        """Delete an item."""
        try:
            model = InventoryItemModel.objects.get(pk=item_id)
            model.delete()
            return True
        except InventoryItemModel.DoesNotExist:
            return False
