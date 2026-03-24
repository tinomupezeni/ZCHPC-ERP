"""
Repository interfaces for the Payroll module.
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from modules.payroll.domain.entities import (
    TaxTable,
    ExchangeRate,
    AllowanceType,
    DeductionType,
    EmployeeAllowance,
    EmployeeDeduction,
    Payslip,
    Payroll,
)
from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    Currency,
    TaxBracket,
)


class ITaxTableRepository(ABC):
    """Repository interface for TaxTable aggregate."""

    @abstractmethod
    def get_by_id(self, table_id: int) -> Optional[TaxTable]:
        """Get tax table by ID."""
        pass

    @abstractmethod
    def get_active_for_currency(
        self, currency: Currency, as_of: date
    ) -> Optional[TaxTable]:
        """Get the active tax table for a currency as of a specific date."""
        pass

    @abstractmethod
    def get_brackets_for_currency(
        self, currency: Currency, as_of: date
    ) -> List[Tuple[Decimal, Decimal, Decimal, Decimal]]:
        """
        Get tax brackets as tuples for a currency.

        Returns list of (min_income, max_income, rate, deduction) tuples.
        """
        pass

    @abstractmethod
    def save(self, tax_table: TaxTable) -> TaxTable:
        """Save a tax table."""
        pass

    @abstractmethod
    def get_all(self, currency: Optional[Currency] = None) -> List[TaxTable]:
        """Get all tax tables, optionally filtered by currency."""
        pass


class IExchangeRateRepository(ABC):
    """Repository interface for ExchangeRate aggregate."""

    @abstractmethod
    def get_by_id(self, rate_id: int) -> Optional[ExchangeRate]:
        """Get exchange rate by ID."""
        pass

    @abstractmethod
    def get_by_date(self, rate_date: date) -> Optional[ExchangeRate]:
        """Get exchange rate for a specific date."""
        pass

    @abstractmethod
    def get_latest(self, as_of: Optional[date] = None) -> Optional[ExchangeRate]:
        """Get the latest exchange rate, optionally as of a specific date."""
        pass

    @abstractmethod
    def save(self, exchange_rate: ExchangeRate) -> ExchangeRate:
        """Save an exchange rate."""
        pass

    @abstractmethod
    def delete(self, rate_id: int) -> bool:
        """Delete an exchange rate."""
        pass

    @abstractmethod
    def get_range(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRate]:
        """Get exchange rates within a date range."""
        pass


class IAllowanceTypeRepository(ABC):
    """Repository interface for AllowanceType aggregate."""

    @abstractmethod
    def get_by_id(self, type_id: int) -> Optional[AllowanceType]:
        """Get allowance type by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[AllowanceType]:
        """Get allowance type by name."""
        pass

    @abstractmethod
    def get_all(self, active_only: bool = True) -> List[AllowanceType]:
        """Get all allowance types."""
        pass

    @abstractmethod
    def save(self, allowance_type: AllowanceType) -> AllowanceType:
        """Save an allowance type."""
        pass

    @abstractmethod
    def delete(self, type_id: int) -> bool:
        """Delete an allowance type."""
        pass


class IDeductionTypeRepository(ABC):
    """Repository interface for DeductionType aggregate."""

    @abstractmethod
    def get_by_id(self, type_id: int) -> Optional[DeductionType]:
        """Get deduction type by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[DeductionType]:
        """Get deduction type by name."""
        pass

    @abstractmethod
    def get_all(self, active_only: bool = True) -> List[DeductionType]:
        """Get all deduction types."""
        pass

    @abstractmethod
    def save(self, deduction_type: DeductionType) -> DeductionType:
        """Save a deduction type."""
        pass

    @abstractmethod
    def delete(self, type_id: int) -> bool:
        """Delete a deduction type."""
        pass


class IEmployeeAllowanceRepository(ABC):
    """Repository interface for EmployeeAllowance."""

    @abstractmethod
    def get_by_employee(self, employee_id: int) -> List[EmployeeAllowance]:
        """Get all allowances for an employee."""
        pass

    @abstractmethod
    def save(self, allowance: EmployeeAllowance) -> EmployeeAllowance:
        """Save an employee allowance."""
        pass

    @abstractmethod
    def delete(self, allowance_id: int) -> bool:
        """Delete an employee allowance."""
        pass


class IEmployeeDeductionRepository(ABC):
    """Repository interface for EmployeeDeduction."""

    @abstractmethod
    def get_by_employee(self, employee_id: int) -> List[EmployeeDeduction]:
        """Get all deductions for an employee."""
        pass

    @abstractmethod
    def save(self, deduction: EmployeeDeduction) -> EmployeeDeduction:
        """Save an employee deduction."""
        pass

    @abstractmethod
    def delete(self, deduction_id: int) -> bool:
        """Delete an employee deduction."""
        pass


class IPayslipRepository(ABC):
    """Repository interface for Payslip aggregate."""

    @abstractmethod
    def get_by_id(self, payslip_id: int) -> Optional[Payslip]:
        """Get payslip by ID."""
        pass

    @abstractmethod
    def get_by_employee_and_period(
        self, employee_id: int, period: PayrollPeriod
    ) -> Optional[Payslip]:
        """Get payslip for an employee in a specific period."""
        pass

    @abstractmethod
    def get_by_payroll(self, payroll_id: int) -> List[Payslip]:
        """Get all payslips in a payroll batch."""
        pass

    @abstractmethod
    def get_by_period(self, period: PayrollPeriod) -> List[Payslip]:
        """Get all payslips for a period."""
        pass

    @abstractmethod
    def save(self, payslip: Payslip) -> Payslip:
        """Save a payslip."""
        pass

    @abstractmethod
    def save_batch(self, payslips: List[Payslip]) -> List[Payslip]:
        """Save multiple payslips."""
        pass

    @abstractmethod
    def delete(self, payslip_id: int) -> bool:
        """Delete a payslip."""
        pass


class IPayrollRepository(ABC):
    """Repository interface for Payroll aggregate."""

    @abstractmethod
    def get_by_id(self, payroll_id: int) -> Optional[Payroll]:
        """Get payroll by ID."""
        pass

    @abstractmethod
    def get_by_period(self, period: PayrollPeriod) -> Optional[Payroll]:
        """Get payroll for a specific period."""
        pass

    @abstractmethod
    def get_all(self, year: Optional[int] = None) -> List[Payroll]:
        """Get all payrolls, optionally filtered by year."""
        pass

    @abstractmethod
    def save(self, payroll: Payroll) -> Payroll:
        """Save a payroll."""
        pass

    @abstractmethod
    def delete(self, payroll_id: int) -> bool:
        """Delete a payroll."""
        pass
