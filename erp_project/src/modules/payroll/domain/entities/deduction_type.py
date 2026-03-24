"""
DeductionType and EmployeeDeduction entities.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot, Entity
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import Currency


@dataclass
class DeductionType(AggregateRoot[int]):
    """
    Aggregate root for deduction types.

    Defines types of deductions (Union Dues, Pension, Loans, etc.)
    with optional default amounts.
    """

    name: str
    description: Optional[str] = None
    default_amount: Decimal = Decimal("0")
    default_currency: Currency = Currency.USD
    is_percentage: bool = False  # If true, amount is percentage of gross
    is_pre_tax: bool = False  # If true, deducted before tax calculation
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate deduction type."""
        if not self.name or not self.name.strip():
            raise ValidationError("Deduction type name is required")
        if self.default_amount < 0:
            raise ValidationError("Default amount cannot be negative")
        if self.is_percentage and self.default_amount > 100:
            raise ValidationError("Percentage cannot exceed 100")

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_amount: Optional[Decimal] = None,
        default_currency: Optional[Currency] = None,
        is_percentage: Optional[bool] = None,
        is_pre_tax: Optional[bool] = None
    ) -> None:
        """Update deduction type details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Deduction type name cannot be empty")
            self.name = name.strip()
        if description is not None:
            self.description = description
        if default_amount is not None:
            if default_amount < 0:
                raise ValidationError("Default amount cannot be negative")
            self.default_amount = default_amount
        if default_currency is not None:
            self.default_currency = default_currency
        if is_percentage is not None:
            self.is_percentage = is_percentage
        if is_pre_tax is not None:
            self.is_pre_tax = is_pre_tax

    def deactivate(self) -> None:
        """Deactivate this deduction type."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this deduction type."""
        self.is_active = True


@dataclass
class EmployeeDeduction(Entity[int]):
    """
    Entity linking an employee to a deduction type.

    Stores the specific amount for this employee.
    """

    employee_id: int
    deduction_type_id: int
    deduction_type_name: str
    amount: Decimal
    currency: Currency
    is_percentage: bool = False

    def __post_init__(self) -> None:
        """Validate employee deduction."""
        if self.amount < 0:
            raise ValidationError("Deduction amount cannot be negative")
        if self.is_percentage and self.amount > 100:
            raise ValidationError("Percentage cannot exceed 100")

    def calculate_amount(self, gross_salary: Decimal) -> Decimal:
        """
        Calculate the actual deduction amount.

        If percentage, calculates based on gross salary.
        """
        if self.is_percentage:
            return (gross_salary * self.amount / Decimal("100")).quantize(
                Decimal("0.01")
            )
        return self.amount

    def update_amount(
        self,
        amount: Decimal,
        currency: Optional[Currency] = None,
        is_percentage: Optional[bool] = None
    ) -> None:
        """Update the deduction amount."""
        if amount < 0:
            raise ValidationError("Deduction amount cannot be negative")
        self.amount = amount
        if currency:
            self.currency = currency
        if is_percentage is not None:
            self.is_percentage = is_percentage

    @classmethod
    def create(
        cls,
        employee_id: int,
        deduction_type_id: int,
        deduction_type_name: str,
        amount: Decimal,
        currency: Currency = Currency.USD,
        is_percentage: bool = False
    ) -> "EmployeeDeduction":
        """Factory method to create an employee deduction."""
        return cls(
            id=None,
            employee_id=employee_id,
            deduction_type_id=deduction_type_id,
            deduction_type_name=deduction_type_name,
            amount=amount,
            currency=currency,
            is_percentage=is_percentage
        )
