"""
Partner aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.accounts.domain.value_objects import PartnerType


@dataclass
class Partner(AggregateRoot[int]):
    """
    Aggregate root for partners (customers, suppliers, employees).

    Used for AR/AP reconciliation and reporting.
    """

    name: str
    partner_type: PartnerType
    vat_number: Optional[str] = None
    currency_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate partner."""
        if not self.name or not self.name.strip():
            raise ValidationError("Partner name is required")

    @property
    def is_customer(self) -> bool:
        """Check if this is a customer."""
        return self.partner_type == PartnerType.CUSTOMER

    @property
    def is_supplier(self) -> bool:
        """Check if this is a supplier."""
        return self.partner_type == PartnerType.SUPPLIER

    @property
    def is_employee(self) -> bool:
        """Check if this is an employee."""
        return self.partner_type == PartnerType.EMPLOYEE

    def update_details(
        self,
        name: Optional[str] = None,
        vat_number: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        currency_id: Optional[int] = None
    ) -> None:
        """Update partner details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Partner name cannot be empty")
            self.name = name.strip()
        if vat_number is not None:
            self.vat_number = vat_number
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
        if currency_id is not None:
            self.currency_id = currency_id
        self.updated_at = datetime.now()

    def change_type(self, new_type: PartnerType) -> None:
        """Change the partner type."""
        self.partner_type = new_type
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate this partner."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this partner."""
        self.is_active = True
        self.updated_at = datetime.now()

    @classmethod
    def create_customer(
        cls,
        name: str,
        vat_number: Optional[str] = None,
        currency_id: Optional[int] = None
    ) -> "Partner":
        """Create a customer partner."""
        return cls.create(
            name=name,
            partner_type=PartnerType.CUSTOMER,
            vat_number=vat_number,
            currency_id=currency_id
        )

    @classmethod
    def create_supplier(
        cls,
        name: str,
        vat_number: Optional[str] = None,
        currency_id: Optional[int] = None
    ) -> "Partner":
        """Create a supplier partner."""
        return cls.create(
            name=name,
            partner_type=PartnerType.SUPPLIER,
            vat_number=vat_number,
            currency_id=currency_id
        )

    @classmethod
    def create(
        cls,
        name: str,
        partner_type: PartnerType,
        vat_number: Optional[str] = None,
        currency_id: Optional[int] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> "Partner":
        """Factory method to create a partner."""
        now = datetime.now()
        return cls(
            id=None,
            name=name,
            partner_type=partner_type,
            vat_number=vat_number,
            currency_id=currency_id,
            email=email,
            phone=phone,
            address=address,
            is_active=True,
            created_at=now,
            updated_at=now
        )
