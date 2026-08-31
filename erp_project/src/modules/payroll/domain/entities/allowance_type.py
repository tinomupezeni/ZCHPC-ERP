"""
AllowanceType and EmployeeAllowance entities.
"""

from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot, Entity
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import Currency


class AllowanceType(AggregateRoot[int]):
    """
    Aggregate root for allowance types.

    Defines types of allowances (Housing, Transport, etc.)
    with optional default amounts.

    Plain class with an explicit __init__ (not @dataclass) - AggregateRoot's
    own __init__(self, id) sets up identity/domain-event bookkeeping and a
    dataclass on a subclass generates its own __init__ that never calls it,
    so `id` (an inherited read-only property) can't even be added as a
    dataclass field. See LeaveRequest for the same working pattern.
    """

    def __init__(
        self,
        id: Optional[int],
        name: str,
        description: Optional[str] = None,
        default_amount: Decimal = Decimal("0"),
        default_currency: Currency = Currency.USD,
        is_taxable: bool = True,
        is_active: bool = True,
    ) -> None:
        if not name or not name.strip():
            raise ValidationError("Allowance type name is required")
        if default_amount < 0:
            raise ValidationError("Default amount cannot be negative")
        super().__init__(id)
        self.name = name
        self.description = description
        self.default_amount = default_amount
        self.default_currency = default_currency
        self.is_taxable = is_taxable
        self.is_active = is_active

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_amount: Optional[Decimal] = None,
        default_currency: Optional[Currency] = None,
        is_taxable: Optional[bool] = None
    ) -> None:
        """Update allowance type details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Allowance type name cannot be empty")
            self.name = name.strip()
        if description is not None:
            self.description = description
        if default_amount is not None:
            if default_amount < 0:
                raise ValidationError("Default amount cannot be negative")
            self.default_amount = default_amount
        if default_currency is not None:
            self.default_currency = default_currency
        if is_taxable is not None:
            self.is_taxable = is_taxable

    def deactivate(self) -> None:
        """Deactivate this allowance type."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this allowance type."""
        self.is_active = True


class EmployeeAllowance(Entity[int]):
    """
    Entity linking an employee to an allowance type.

    Stores the specific amount for this employee.

    Plain class with an explicit __init__ (not @dataclass) - see
    AllowanceType above for why.
    """

    def __init__(
        self,
        id: Optional[int],
        employee_id: int,
        allowance_type_id: int,
        allowance_type_name: str,
        amount: Decimal,
        currency: Currency,
    ) -> None:
        if amount < 0:
            raise ValidationError("Allowance amount cannot be negative")
        super().__init__(id)
        self.employee_id = employee_id
        self.allowance_type_id = allowance_type_id
        self.allowance_type_name = allowance_type_name
        self.amount = amount
        self.currency = currency

    def update_amount(self, amount: Decimal, currency: Optional[Currency] = None) -> None:
        """Update the allowance amount."""
        if amount < 0:
            raise ValidationError("Allowance amount cannot be negative")
        self.amount = amount
        if currency:
            self.currency = currency

    @classmethod
    def create(
        cls,
        employee_id: int,
        allowance_type_id: int,
        allowance_type_name: str,
        amount: Decimal,
        currency: Currency = Currency.USD
    ) -> "EmployeeAllowance":
        """Factory method to create an employee allowance."""
        return cls(
            id=None,
            employee_id=employee_id,
            allowance_type_id=allowance_type_id,
            allowance_type_name=allowance_type_name,
            amount=amount,
            currency=currency
        )
