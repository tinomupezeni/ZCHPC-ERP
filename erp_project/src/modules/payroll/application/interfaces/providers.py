"""
Provider interfaces for Payroll module cross-module communication.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional, Protocol

from modules.payroll.domain.value_objects import PayrollPeriod


@dataclass
class PayslipDTO:
    """Data transfer object for payslip information."""

    id: int
    employee_id: int
    period_year: int
    period_month: int
    base_salary_usd: Decimal
    base_salary_zig: Decimal
    gross_usd: Decimal
    gross_zig: Decimal
    total_deductions_usd: Decimal
    total_deductions_zig: Decimal
    net_salary_usd: Decimal
    net_salary_zig: Decimal
    status: str


@dataclass
class PayrollSummaryDTO:
    """Data transfer object for payroll summary."""

    period_year: int
    period_month: int
    total_employees: int
    total_gross_usd: Decimal
    total_gross_zig: Decimal
    total_net_usd: Decimal
    total_net_zig: Decimal
    total_paye_usd: Decimal
    total_paye_zig: Decimal
    total_nssa_usd: Decimal
    total_nssa_zig: Decimal
    status: str


@dataclass
class TaxBracketDTO:
    """Data transfer object for tax bracket."""

    id: int
    currency: str
    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal
    deduction: Decimal
    active_from: date


@dataclass
class ExchangeRateDTO:
    """Data transfer object for exchange rate."""

    id: int
    rate_date: date
    zig_to_usd_rate: Decimal
    usd_to_zig_rate: Decimal
    source: Optional[str]


class IPayrollProvider(Protocol):
    """
    Interface for payroll information access by other modules.

    Provides read-only access to payroll data for cross-module queries.
    """

    def get_payslip(
        self, employee_id: int, period: PayrollPeriod
    ) -> Optional[PayslipDTO]:
        """Get payslip for an employee in a specific period."""
        ...

    def get_payslips_for_period(
        self, period: PayrollPeriod
    ) -> List[PayslipDTO]:
        """Get all payslips for a period."""
        ...

    def get_payroll_summary(
        self, period: PayrollPeriod
    ) -> Optional[PayrollSummaryDTO]:
        """Get summary for a payroll period."""
        ...

    def get_latest_exchange_rate(self) -> Optional[ExchangeRateDTO]:
        """Get the latest exchange rate."""
        ...

    def get_tax_brackets(
        self, currency: str
    ) -> List[TaxBracketDTO]:
        """Get tax brackets for a currency."""
        ...


class IEmployeePayrollInfoProvider(Protocol):
    """
    Interface to get employee information needed for payroll.

    This is provided by the HR module.
    """

    def get_active_employee_ids(self) -> List[int]:
        """Get IDs of all active employees."""
        ...

    def get_employee_salary_info(self, employee_id: int) -> dict:
        """
        Get salary information for an employee.

        Returns dict with:
        - usd_salary
        - zig_salary
        - pays_aids_levy
        - employee_name
        """
        ...
