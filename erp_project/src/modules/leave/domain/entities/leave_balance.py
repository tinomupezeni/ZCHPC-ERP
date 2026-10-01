"""
LeaveBalance aggregate root.
"""

from datetime import datetime
from decimal import Decimal

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError

from modules.leave.domain.value_objects import LeaveEntitlement


class LeaveBalance(AggregateRoot[int]):
    """
    LeaveBalance aggregate root.

    Tracks leave balance for an employee for a specific leave type and year.
    """

    def __init__(
        self,
        id: int,
        employee_id: int,
        leave_type_id: int,
        year: int,
        entitlement: LeaveEntitlement,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize leave balance."""
        super().__init__(id)
        self.employee_id = employee_id
        self.leave_type_id = leave_type_id
        self.year = year
        self.entitlement = entitlement
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self) -> None:
        """Validate leave balance data."""
        if not self.employee_id:
            raise ValidationError(
                message="Employee ID is required",
                code="MISSING_EMPLOYEE_ID",
            )
        if not self.leave_type_id:
            raise ValidationError(
                message="Leave type ID is required",
                code="MISSING_LEAVE_TYPE_ID",
            )
        if self.year < 2000 or self.year > 2100:
            raise ValidationError(
                message="Year must be between 2000 and 2100",
                code="INVALID_YEAR",
            )

    @classmethod
    def create(
        cls,
        id: int,
        employee_id: int,
        leave_type_id: int,
        year: int,
        entitled_days: int | Decimal,
        used_days: int | Decimal = 0,
    ) -> "LeaveBalance":
        """
        Create a new leave balance.

        Args:
            id: Balance ID
            employee_id: Employee ID
            leave_type_id: Leave type ID
            year: Year for this balance
            entitled_days: Total days entitled
            used_days: Days already used

        Returns:
            New LeaveBalance instance
        """
        return cls(
            id=id,
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
            entitlement=LeaveEntitlement.create(entitled_days, used_days),
        )

    @property
    def entitled_days(self) -> Decimal:
        """Get entitled days."""
        return self.entitlement.entitled_days

    @property
    def used_days(self) -> Decimal:
        """Get used days."""
        return self.entitlement.used_days

    @property
    def remaining_days(self) -> Decimal:
        """Get remaining days."""
        return self.entitlement.remaining_days

    @property
    def is_exhausted(self) -> bool:
        """Check if balance is exhausted."""
        return self.entitlement.is_exhausted

    @property
    def usage_percentage(self) -> Decimal:
        """Get usage percentage."""
        return self.entitlement.usage_percentage

    def can_take(self, days: int | Decimal) -> bool:
        """
        Check if employee can take specified number of days.

        Args:
            days: Number of days to check

        Returns:
            True if employee has sufficient balance
        """
        return self.entitlement.can_take(Decimal(str(days)))

    def deduct(self, days: int | Decimal) -> None:
        """
        Deduct days from balance.

        Args:
            days: Number of days to deduct

        Raises:
            ValidationError: If insufficient balance
        """
        decimal_days = Decimal(str(days))
        self.entitlement = self.entitlement.with_usage(decimal_days)
        self.updated_at = datetime.utcnow()

    def restore(self, days: int | Decimal) -> None:
        """
        Restore days to balance (e.g., cancelled leave).

        Args:
            days: Number of days to restore
        """
        decimal_days = Decimal(str(days))
        self.entitlement = self.entitlement.with_reversal(decimal_days)
        self.updated_at = datetime.utcnow()

    def adjust_entitlement(self, new_entitled_days: int | Decimal) -> None:
        """
        Adjust the entitled days.

        Args:
            new_entitled_days: New entitlement amount
        """
        self.entitlement = LeaveEntitlement(
            entitled_days=Decimal(str(new_entitled_days)),
            used_days=self.entitlement.used_days,
        )
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return f"LeaveBalance(employee={self.employee_id}, type={self.leave_type_id}, {self.entitlement})"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"LeaveBalance(id={self.id}, employee_id={self.employee_id}, "
            f"leave_type_id={self.leave_type_id}, year={self.year}, "
            f"remaining={self.remaining_days})"
        )
