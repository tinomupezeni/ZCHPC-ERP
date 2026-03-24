"""
Payslip aggregate root.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    PayslipStatus,
    Earnings,
    Deductions,
)


@dataclass
class Payslip(AggregateRoot[int]):
    """
    Aggregate root for individual employee payslips.

    Contains all salary components for a single employee in a pay period.
    Supports dual-currency (USD and ZIG) calculations.
    """

    # Core relationships
    payroll_id: Optional[int]
    employee_id: int
    period: PayrollPeriod

    # Earnings breakdown
    base_salary_usd: Decimal = Decimal("0")
    base_salary_zig: Decimal = Decimal("0")
    total_allowances_usd: Decimal = Decimal("0")
    total_allowances_zig: Decimal = Decimal("0")

    # Gross calculation
    gross_usd: Decimal = Decimal("0")
    gross_zig: Decimal = Decimal("0")

    # Statutory deductions
    paye_usd: Decimal = Decimal("0")
    paye_zig: Decimal = Decimal("0")
    aids_levy_usd: Decimal = Decimal("0")
    aids_levy_zig: Decimal = Decimal("0")
    nssa_employee_usd: Decimal = Decimal("0")
    nssa_employee_zig: Decimal = Decimal("0")
    nssa_employer_usd: Decimal = Decimal("0")
    nssa_employer_zig: Decimal = Decimal("0")

    # Other deductions
    other_deductions_usd: Decimal = Decimal("0")
    other_deductions_zig: Decimal = Decimal("0")

    # Total deductions
    total_deductions_usd: Decimal = Decimal("0")
    total_deductions_zig: Decimal = Decimal("0")

    # Net salary
    net_salary_usd: Decimal = Decimal("0")
    net_salary_zig: Decimal = Decimal("0")

    # Exchange rate used
    exchange_rate: Decimal = Decimal("0")

    # Status and metadata
    status: PayslipStatus = PayslipStatus.DRAFT
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def calculate_totals(self) -> None:
        """Recalculate gross, deductions, and net totals."""
        # Gross = Base + Allowances
        self.gross_usd = self.base_salary_usd + self.total_allowances_usd
        self.gross_zig = self.base_salary_zig + self.total_allowances_zig

        # Total deductions = Statutory + Other
        self.total_deductions_usd = (
            self.paye_usd +
            self.aids_levy_usd +
            self.nssa_employee_usd +
            self.other_deductions_usd
        )
        self.total_deductions_zig = (
            self.paye_zig +
            self.aids_levy_zig +
            self.nssa_employee_zig +
            self.other_deductions_zig
        )

        # Net = Gross - Deductions
        self.net_salary_usd = self.gross_usd - self.total_deductions_usd
        self.net_salary_zig = self.gross_zig - self.total_deductions_zig

    def approve(self) -> None:
        """Approve the payslip for processing."""
        if self.status != PayslipStatus.DRAFT:
            raise ValidationError(
                f"Cannot approve payslip in {self.status.value} status"
            )
        self.status = PayslipStatus.PROCESSED
        self.updated_at = datetime.now()

    def mark_paid(self) -> None:
        """Mark the payslip as paid."""
        if self.status != PayslipStatus.PROCESSED:
            raise ValidationError(
                f"Cannot mark as paid: payslip is {self.status.value}"
            )
        self.status = PayslipStatus.PAID
        self.updated_at = datetime.now()

    def mark_failed(self, reason: str = "") -> None:
        """Mark the payslip as failed."""
        self.status = PayslipStatus.FAILED
        if reason:
            self.notes = f"Failed: {reason}"
        self.updated_at = datetime.now()

    def revert_to_draft(self) -> None:
        """Revert payslip back to draft status."""
        if self.status == PayslipStatus.PAID:
            raise ValidationError("Cannot revert a paid payslip")
        self.status = PayslipStatus.DRAFT
        self.updated_at = datetime.now()

    def set_earnings(self, earnings: Earnings) -> None:
        """Set earnings from an Earnings value object."""
        self.base_salary_usd = earnings.base_salary_usd
        self.base_salary_zig = earnings.base_salary_zig
        self.total_allowances_usd = earnings.total_allowances_usd
        self.total_allowances_zig = earnings.total_allowances_zig
        self.gross_usd = earnings.gross_usd
        self.gross_zig = earnings.gross_zig

    def set_deductions(self, deductions: Deductions) -> None:
        """Set deductions from a Deductions value object."""
        self.paye_usd = deductions.paye_usd
        self.paye_zig = deductions.paye_zig
        self.aids_levy_usd = deductions.aids_levy_usd
        self.aids_levy_zig = deductions.aids_levy_zig
        self.nssa_employee_usd = deductions.nssa_employee_usd
        self.nssa_employee_zig = deductions.nssa_employee_zig
        self.nssa_employer_usd = deductions.nssa_employer_usd
        self.nssa_employer_zig = deductions.nssa_employer_zig
        self.other_deductions_usd = deductions.total_other_usd
        self.other_deductions_zig = deductions.total_other_zig
        self.total_deductions_usd = deductions.total_usd
        self.total_deductions_zig = deductions.total_zig

    @property
    def total_employer_cost_usd(self) -> Decimal:
        """Total cost to employer in USD."""
        return self.gross_usd + self.nssa_employer_usd

    @property
    def total_employer_cost_zig(self) -> Decimal:
        """Total cost to employer in ZIG."""
        return self.gross_zig + self.nssa_employer_zig

    @property
    def is_editable(self) -> bool:
        """Check if payslip can be edited."""
        return self.status.can_edit

    @classmethod
    def create(
        cls,
        employee_id: int,
        period: PayrollPeriod,
        payroll_id: Optional[int] = None
    ) -> "Payslip":
        """Factory method to create a new payslip."""
        now = datetime.now()
        return cls(
            id=None,
            payroll_id=payroll_id,
            employee_id=employee_id,
            period=period,
            status=PayslipStatus.DRAFT,
            created_at=now,
            updated_at=now
        )
