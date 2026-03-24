"""
Supplier (Vendor) aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.procurement.domain.value_objects import VendorRating


@dataclass
class Supplier(AggregateRoot[int]):
    """
    Aggregate root for suppliers (vendors).

    Represents an external vendor/supplier that provides goods or services.
    """

    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    rating: Decimal = Decimal("0")
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate supplier."""
        if not self.name or not self.name.strip():
            raise ValidationError("Supplier name is required")
        if not self.email or not self.email.strip():
            raise ValidationError("Supplier email is required")
        if "@" not in self.email:
            raise ValidationError("Invalid email format")

    @property
    def vendor_rating(self) -> VendorRating:
        """Get as VendorRating value object."""
        return VendorRating(value=self.rating)

    @property
    def is_good_rated(self) -> bool:
        """Check if supplier has good rating (3+)."""
        return self.rating >= Decimal("3")

    @property
    def is_excellent_rated(self) -> bool:
        """Check if supplier has excellent rating (4+)."""
        return self.rating >= Decimal("4")

    def update_details(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> None:
        """Update supplier details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Supplier name cannot be empty")
            self.name = name.strip()
        if email is not None:
            if not email.strip() or "@" not in email:
                raise ValidationError("Invalid email format")
            self.email = email.strip()
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
        self.updated_at = datetime.now()

    def update_rating(self, new_rating: Decimal) -> None:
        """Update supplier rating."""
        if new_rating < Decimal("0") or new_rating > Decimal("5"):
            raise ValidationError("Rating must be between 0 and 5")
        self.rating = new_rating
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate this supplier."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this supplier."""
        self.is_active = True
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        name: str,
        email: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        rating: Decimal = Decimal("0")
    ) -> "Supplier":
        """Factory method to create a supplier."""
        now = datetime.now()
        return cls(
            id=None,
            name=name.strip(),
            email=email.strip(),
            phone=phone,
            address=address,
            rating=rating,
            is_active=True,
            created_at=now,
            updated_at=now
        )
