"""
Payroll aggregate root for batch payroll processing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import PayrollPeriod, PayrollStatus


@dataclass
class PayrollSummary:
    """Summary statistics for a payroll batch."""

    total_employees: int = 0
    total_gross_usd: Decimal = Decimal("0")
    total_gross_zig: Decimal = Decimal("0")
    total_net_usd: Decimal = Decimal("0")
    total_net_zig: Decimal = Decimal("0")
    total_paye_usd: Decimal = Decimal("0")
    total_paye_zig: Decimal = Decimal("0")
    total_nssa_employee_usd: Decimal = Decimal("0")
    total_nssa_employee_zig: Decimal = Decimal("0")
    total_nssa_employer_usd: Decimal = Decimal("0")
    total_nssa_employer_zig: Decimal = Decimal("0")
    total_aids_levy_usd: Decimal = Decimal("0")
    total_aids_levy_zig: Decimal = Decimal("0")
    total_deductions_usd: Decimal = Decimal("0")
    total_deductions_zig: Decimal = Decimal("0")
    total_allowances_usd: Decimal = Decimal("0")
    total_allowances_zig: Decimal = Decimal("0")

    @property
    def total_employer_cost_usd(self) -> Decimal:
        """Total cost to employer in USD."""
        return self.total_gross_usd + self.total_nssa_employer_usd

    @property
    def total_employer_cost_zig(self) -> Decimal:
        """Total cost to employer in ZIG."""
        return self.total_gross_zig + self.total_nssa_employer_zig


class Payroll(AggregateRoot[int]):
    """
    Aggregate root for payroll batches.

    Manages the processing of payroll for a specific period.
    Contains summary information for all payslips in the batch.

    Plain class with an explicit __init__ (not @dataclass) - AggregateRoot's
    own __init__(self, id) sets up identity/domain-event bookkeeping and a
    dataclass on a subclass generates its own __init__ that never calls it,
    so `id` (an inherited read-only property) can't even be added as a
    dataclass field. See LeaveRequest for the same working pattern.
    """

    def __init__(
        self,
        id: Optional[int],
        period: PayrollPeriod,
        status: PayrollStatus = PayrollStatus.OPEN,
        processed_at: Optional[datetime] = None,
        processed_by: Optional[int] = None,  # User ID
        closed_at: Optional[datetime] = None,
        closed_by: Optional[int] = None,  # User ID
        notes: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        # Summary fields (calculated from payslips)
        total_employees: int = 0,
        total_gross_usd: Decimal = Decimal("0"),
        total_gross_zig: Decimal = Decimal("0"),
        total_net_usd: Decimal = Decimal("0"),
        total_net_zig: Decimal = Decimal("0"),
        total_paye_usd: Decimal = Decimal("0"),
        total_paye_zig: Decimal = Decimal("0"),
        total_nssa_usd: Decimal = Decimal("0"),
        total_nssa_zig: Decimal = Decimal("0"),
    ) -> None:
        super().__init__(id)
        self.period = period
        self.status = status
        self.processed_at = processed_at
        self.processed_by = processed_by
        self.closed_at = closed_at
        self.closed_by = closed_by
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.total_employees = total_employees
        self.total_gross_usd = total_gross_usd
        self.total_gross_zig = total_gross_zig
        self.total_net_usd = total_net_usd
        self.total_net_zig = total_net_zig
        self.total_paye_usd = total_paye_usd
        self.total_paye_zig = total_paye_zig
        self.total_nssa_usd = total_nssa_usd
        self.total_nssa_zig = total_nssa_zig

    def start_processing(self, user_id: int) -> None:
        """Begin processing the payroll."""
        if self.status != PayrollStatus.OPEN:
            raise ValidationError(
                f"Cannot process payroll in {self.status.value} status"
            )
        self.status = PayrollStatus.PROCESSING
        self.processed_by = user_id
        self.processed_at = datetime.now()
        self.updated_at = datetime.now()

    def complete_processing(self, summary: PayrollSummary) -> None:
        """
        Complete payroll processing with summary.

        Returns to OPEN (not a new "processed" status - PayrollStatus has
        none) so the period can be re-processed later to pick up newly
        added employees; process_payroll() already skips anyone who has a
        payslip for the period, so a re-run only fills in gaps. Closing a
        period for good is a separate, explicit close() action.
        """
        if self.status != PayrollStatus.PROCESSING:
            raise ValidationError(
                f"Cannot complete: payroll is {self.status.value}"
            )
        self.total_employees = summary.total_employees
        self.total_gross_usd = summary.total_gross_usd
        self.total_gross_zig = summary.total_gross_zig
        self.total_net_usd = summary.total_net_usd
        self.total_net_zig = summary.total_net_zig
        self.total_paye_usd = summary.total_paye_usd
        self.total_paye_zig = summary.total_paye_zig
        self.total_nssa_usd = (
            summary.total_nssa_employee_usd + summary.total_nssa_employer_usd
        )
        self.total_nssa_zig = (
            summary.total_nssa_employee_zig + summary.total_nssa_employer_zig
        )
        self.status = PayrollStatus.OPEN
        self.updated_at = datetime.now()

    def close(self, user_id: int) -> None:
        """Close the payroll period."""
        if self.status == PayrollStatus.CLOSED:
            raise ValidationError("Payroll is already closed")
        if self.status == PayrollStatus.OPEN:
            raise ValidationError("Cannot close unprocessed payroll")
        self.status = PayrollStatus.CLOSED
        self.closed_by = user_id
        self.closed_at = datetime.now()
        self.updated_at = datetime.now()

    def reopen(self) -> None:
        """Reopen a closed payroll."""
        if self.status != PayrollStatus.CLOSED:
            raise ValidationError(
                f"Cannot reopen: payroll is {self.status.value}"
            )
        self.status = PayrollStatus.OPEN
        self.closed_by = None
        self.closed_at = None
        self.updated_at = datetime.now()

    @property
    def can_process(self) -> bool:
        """Check if payroll can be processed."""
        return self.status.can_process

    @property
    def is_closed(self) -> bool:
        """Check if payroll is closed."""
        return self.status == PayrollStatus.CLOSED

    @property
    def total_employer_cost_usd(self) -> Decimal:
        """Total employer cost in USD (gross + employer NSSA)."""
        # Employer NSSA is half of total NSSA
        employer_nssa = self.total_nssa_usd / 2
        return self.total_gross_usd + employer_nssa

    @property
    def total_employer_cost_zig(self) -> Decimal:
        """Total employer cost in ZIG."""
        employer_nssa = self.total_nssa_zig / 2
        return self.total_gross_zig + employer_nssa

    @classmethod
    def create(cls, period: PayrollPeriod) -> "Payroll":
        """Factory method to create a new payroll."""
        now = datetime.now()
        return cls(
            id=None,
            period=period,
            status=PayrollStatus.OPEN,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def create_for_month(cls, year: int, month: int) -> "Payroll":
        """Convenience factory for creating payroll by year/month."""
        period = PayrollPeriod(year=year, month=month)
        return cls.create(period)
