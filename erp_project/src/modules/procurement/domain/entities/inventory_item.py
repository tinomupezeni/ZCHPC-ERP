"""
InventoryItem aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.value_objects import SKU


@dataclass
class InventoryItem(AggregateRoot[int]):
    """
    Aggregate root for inventory items.

    Represents an item that can be purchased and stocked.
    """

    name: str
    sku: str
    quantity: int = 0
    price_per_unit: Decimal = Decimal("0")
    reorder_level: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate inventory item."""
        if not self.name or not self.name.strip():
            raise ValidationError("Item name is required")
        if not self.sku or not self.sku.strip():
            raise ValidationError("SKU is required")
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if self.price_per_unit < 0:
            raise ValidationError("Price cannot be negative")

    @property
    def sku_value(self) -> SKU:
        """Get as SKU value object."""
        return SKU(value=self.sku)

    @property
    def is_in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.quantity > 0

    @property
    def needs_reorder(self) -> bool:
        """Check if item needs reordering."""
        return self.quantity <= self.reorder_level

    @property
    def total_value(self) -> Decimal:
        """Get total value of inventory."""
        return self.quantity * self.price_per_unit

    def update_details(
        self,
        name: Optional[str] = None,
        price_per_unit: Optional[Decimal] = None,
        reorder_level: Optional[int] = None
    ) -> None:
        """Update item details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Item name cannot be empty")
            self.name = name.strip()
        if price_per_unit is not None:
            if price_per_unit < 0:
                raise ValidationError("Price cannot be negative")
            self.price_per_unit = price_per_unit
        if reorder_level is not None:
            if reorder_level < 0:
                raise ValidationError("Reorder level cannot be negative")
            self.reorder_level = reorder_level
        self.updated_at = datetime.now()

    def add_stock(self, quantity: int) -> None:
        """Add stock to inventory."""
        if quantity <= 0:
            raise ValidationError("Quantity to add must be positive")
        self.quantity += quantity
        self.updated_at = datetime.now()

    def remove_stock(self, quantity: int) -> None:
        """Remove stock from inventory."""
        if quantity <= 0:
            raise ValidationError("Quantity to remove must be positive")
        if quantity > self.quantity:
            raise ValidationError(
                f"Cannot remove {quantity} items. Only {self.quantity} in stock"
            )
        self.quantity -= quantity
        self.updated_at = datetime.now()

    def can_fulfill(self, quantity: int) -> bool:
        """Check if requested quantity can be fulfilled."""
        return self.quantity >= quantity

    def calculate_cost(self, quantity: int) -> Decimal:
        """Calculate cost for a given quantity."""
        return self.price_per_unit * quantity

    def deactivate(self) -> None:
        """Deactivate this item."""
        self.is_active = False
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        name: str,
        sku: str,
        price_per_unit: Decimal,
        quantity: int = 0,
        reorder_level: int = 0
    ) -> "InventoryItem":
        """Factory method to create an inventory item."""
        now = datetime.now()
        return cls(
            id=None,
            name=name.strip(),
            sku=sku.strip().upper(),
            quantity=quantity,
            price_per_unit=price_per_unit,
            reorder_level=reorder_level,
            is_active=True,
            created_at=now,
            updated_at=now
        )
