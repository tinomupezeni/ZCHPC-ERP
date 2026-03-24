"""
Payroll domain events.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import DomainEvent


@dataclass(frozen=True)
class PayrollOpened(DomainEvent):
    """Event raised when a new payroll period is opened."""

    payroll_id: int
    period_year: int
    period_month: int


@dataclass(frozen=True)
class PayrollProcessingStarted(DomainEvent):
    """Event raised when payroll processing begins."""

    payroll_id: int
    period_year: int
    period_month: int
    processed_by: int


@dataclass(frozen=True)
class PayrollProcessed(DomainEvent):
    """Event raised when payroll processing completes."""

    payroll_id: int
    period_year: int
    period_month: int
    total_employees: int
    total_gross_usd: Decimal
    total_gross_zig: Decimal
    total_net_usd: Decimal
    total_net_zig: Decimal
    processed_by: int


@dataclass(frozen=True)
class PayrollClosed(DomainEvent):
    """Event raised when a payroll period is closed."""

    payroll_id: int
    period_year: int
    period_month: int
    closed_by: int


@dataclass(frozen=True)
class PayrollReopened(DomainEvent):
    """Event raised when a closed payroll is reopened."""

    payroll_id: int
    period_year: int
    period_month: int


@dataclass(frozen=True)
class PayslipGenerated(DomainEvent):
    """Event raised when a payslip is generated."""

    payslip_id: int
    payroll_id: Optional[int]
    employee_id: int
    period_year: int
    period_month: int
    net_salary_usd: Decimal
    net_salary_zig: Decimal


@dataclass(frozen=True)
class PayslipApproved(DomainEvent):
    """Event raised when a payslip is approved."""

    payslip_id: int
    employee_id: int
    period_year: int
    period_month: int


@dataclass(frozen=True)
class PayslipPaid(DomainEvent):
    """Event raised when a payslip is marked as paid."""

    payslip_id: int
    employee_id: int
    period_year: int
    period_month: int
    net_salary_usd: Decimal
    net_salary_zig: Decimal
    paid_at: datetime


@dataclass(frozen=True)
class TaxBracketUpdated(DomainEvent):
    """Event raised when tax brackets are updated."""

    currency: str
    effective_from: str  # ISO date string
    bracket_count: int
    updated_by: Optional[int] = None


@dataclass(frozen=True)
class ExchangeRateUpdated(DomainEvent):
    """Event raised when exchange rate is updated."""

    rate_date: str  # ISO date string
    zig_to_usd_rate: Decimal
    source: Optional[str] = None
