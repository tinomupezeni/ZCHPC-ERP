"""
Budget checking domain service.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from shared.domain.exceptions import ValidationError
from modules.procurement.domain.entities import BudgetCenter


class BudgetCenterReader(Protocol):
    """Protocol for reading budget centers."""

    def get_by_id(self, budget_center_id: int) -> BudgetCenter | None:
        """Get a budget center by ID."""
        ...


@dataclass
class BudgetCheckResult:
    """Result of a budget check."""

    is_sufficient: bool
    requested_amount: Decimal
    available_amount: Decimal
    deficit: Decimal = Decimal("0")

    @property
    def message(self) -> str:
        """Get a human-readable message."""
        if self.is_sufficient:
            return (
                f"Budget check passed. Requested: {self.requested_amount}, "
                f"Available: {self.available_amount}"
            )
        else:
            return (
                f"Insufficient budget. Requested: {self.requested_amount}, "
                f"Available: {self.available_amount}, Deficit: {self.deficit}"
            )


class BudgetChecker:
    """
    Domain service for checking budget availability.

    Validates that a budget center has sufficient funds
    for a purchase request.
    """

    def __init__(self, budget_reader: BudgetCenterReader) -> None:
        self._budget_reader = budget_reader

    def check_budget(
        self,
        budget_center_id: int,
        requested_amount: Decimal
    ) -> BudgetCheckResult:
        """
        Check if a budget center has sufficient funds.

        Args:
            budget_center_id: ID of the budget center
            requested_amount: Amount to check

        Returns:
            BudgetCheckResult with details

        Raises:
            ValidationError: If budget center not found
        """
        budget_center = self._budget_reader.get_by_id(budget_center_id)
        if budget_center is None:
            raise ValidationError(f"Budget center {budget_center_id} not found")

        available = budget_center.remaining_amount
        is_sufficient = available >= requested_amount

        deficit = Decimal("0")
        if not is_sufficient:
            deficit = requested_amount - available

        return BudgetCheckResult(
            is_sufficient=is_sufficient,
            requested_amount=requested_amount,
            available_amount=available,
            deficit=deficit
        )

    def validate_budget(
        self,
        budget_center_id: int,
        requested_amount: Decimal
    ) -> None:
        """
        Validate budget and raise if insufficient.

        Args:
            budget_center_id: ID of the budget center
            requested_amount: Amount to validate

        Raises:
            ValidationError: If insufficient budget
        """
        result = self.check_budget(budget_center_id, requested_amount)
        if not result.is_sufficient:
            raise ValidationError(result.message)

    def get_utilization(self, budget_center_id: int) -> Decimal:
        """
        Get budget utilization percentage.

        Args:
            budget_center_id: ID of the budget center

        Returns:
            Utilization rate as percentage
        """
        budget_center = self._budget_reader.get_by_id(budget_center_id)
        if budget_center is None:
            raise ValidationError(f"Budget center {budget_center_id} not found")

        return budget_center.utilization_rate
