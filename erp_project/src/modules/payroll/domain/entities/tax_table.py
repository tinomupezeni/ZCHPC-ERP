"""
TaxTable aggregate root for managing tax brackets.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import Currency, TaxBracket


class TaxTable(AggregateRoot[int]):
    """
    Aggregate root for tax tables containing brackets.

    Each tax table is currency-specific and has an effective date.
    Supports Zimbabwe's progressive PAYE tax system.

    Plain class with an explicit __init__ (not @dataclass) - AggregateRoot's
    own __init__(self, id) sets up identity/domain-event bookkeeping and a
    dataclass on a subclass generates its own __init__ that never calls it,
    so `id` (an inherited read-only property) can't even be added as a
    dataclass field. See LeaveRequest for the same working pattern.
    """

    def __init__(
        self,
        id: Optional[int],
        currency: Currency,
        effective_from: date,
        brackets: Optional[List[TaxBracket]] = None,
        provider: Optional[str] = None,  # Source of tax rates (e.g., "ZIMRA")
        is_active: bool = True,
    ) -> None:
        super().__init__(id)
        self.currency = currency
        self.effective_from = effective_from
        self.brackets = brackets if brackets is not None else []
        self.provider = provider
        self.is_active = is_active
        self._validate_brackets()
        self._sort_brackets()

    def _validate_brackets(self) -> None:
        """Ensure brackets don't overlap and are valid."""
        if not self.brackets:
            return

        # Check all brackets have the same currency
        for bracket in self.brackets:
            if bracket.currency != self.currency:
                raise ValidationError(
                    f"Bracket currency {bracket.currency} doesn't match "
                    f"table currency {self.currency}"
                )

    def _sort_brackets(self) -> None:
        """Sort brackets by min_income ascending."""
        self.brackets = sorted(self.brackets, key=lambda b: b.min_income)

    def add_bracket(
        self,
        min_income: Decimal,
        max_income: Optional[Decimal],
        rate: Decimal,
        deduction: Decimal
    ) -> None:
        """
        Add a new tax bracket.

        Args:
            min_income: Minimum income for this bracket
            max_income: Maximum income (None for highest bracket)
            rate: Tax rate as decimal (0.20 = 20%)
            deduction: Fixed deduction amount for this bracket
        """
        bracket = TaxBracket(
            min_income=min_income,
            max_income=max_income,
            rate=rate,
            deduction=deduction,
            currency=self.currency
        )
        self.brackets.append(bracket)
        self._sort_brackets()

    def remove_bracket(self, min_income: Decimal) -> bool:
        """Remove a bracket by its minimum income."""
        for i, bracket in enumerate(self.brackets):
            if bracket.min_income == min_income:
                self.brackets.pop(i)
                return True
        return False

    def get_applicable_bracket(self, income: Decimal) -> Optional[TaxBracket]:
        """
        Find the bracket that applies to the given income.

        Uses the highest bracket where income > min_income.
        """
        if income <= 0:
            return None

        applicable = None
        for bracket in self.brackets:
            if income > bracket.min_income:
                applicable = bracket
        return applicable

    def calculate_tax(self, income: Decimal) -> Decimal:
        """
        Calculate PAYE tax for the given income.

        Formula: tax = (income * rate) - deduction

        Args:
            income: Gross taxable income

        Returns:
            Calculated tax amount (never negative)
        """
        bracket = self.get_applicable_bracket(income)
        if not bracket:
            return Decimal("0")
        return bracket.calculate_tax(income).quantize(Decimal("0.01"))

    def deactivate(self) -> None:
        """Deactivate this tax table."""
        self.is_active = False

    def activate(self) -> None:
        """Activate this tax table."""
        self.is_active = True

    @property
    def bracket_count(self) -> int:
        """Number of brackets in this table."""
        return len(self.brackets)

    @classmethod
    def create_empty(cls, currency: Currency, effective_from: date) -> "TaxTable":
        """Create an empty tax table."""
        return cls(
            id=None,
            currency=currency,
            effective_from=effective_from,
            brackets=[],
            is_active=True
        )
