"""
PayslipGenerator service for orchestrating payslip calculation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Protocol

from modules.payroll.domain.entities import (
    Payslip,
    TaxTable,
    ExchangeRate,
    EmployeeAllowance,
    EmployeeDeduction,
)
from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    Earnings,
    Deductions,
    Currency,
)
from modules.payroll.domain.services.tax_calculator import (
    TaxCalculator,
    AIDSLevyCalculator,
    NSSACalculator,
)


@dataclass
class EmployeeSalaryInfo:
    """Employee salary information for payslip generation."""

    employee_id: int
    employee_name: str
    usd_salary: Decimal
    zig_salary: Decimal
    pays_aids_levy: bool = True
    allowances: List[EmployeeAllowance] = None
    deductions: List[EmployeeDeduction] = None

    def __post_init__(self):
        if self.allowances is None:
            self.allowances = []
        if self.deductions is None:
            self.deductions = []


class PayslipGenerator:
    """
    Domain service for generating payslips.

    Orchestrates the calculation of all salary components
    including earnings, statutory deductions, and other deductions.
    Handles dual-currency (USD and ZIG) calculations.
    """

    def __init__(
        self,
        tax_calculator: TaxCalculator = None,
        aids_calculator: AIDSLevyCalculator = None,
        nssa_calculator: NSSACalculator = None
    ):
        self.tax_calculator = tax_calculator or TaxCalculator()
        self.aids_calculator = aids_calculator or AIDSLevyCalculator()
        self.nssa_calculator = nssa_calculator or NSSACalculator()

    def generate(
        self,
        employee_info: EmployeeSalaryInfo,
        period: PayrollPeriod,
        usd_tax_table: TaxTable,
        zig_tax_table: TaxTable,
        exchange_rate: ExchangeRate,
        payroll_id: Optional[int] = None
    ) -> Payslip:
        """
        Generate a complete payslip for an employee.

        Args:
            employee_info: Employee salary and allowance/deduction info
            period: Payroll period
            usd_tax_table: Tax table for USD calculations
            zig_tax_table: Tax table for ZIG calculations
            exchange_rate: Current exchange rate for conversions
            payroll_id: Optional parent payroll batch ID

        Returns:
            Fully calculated Payslip entity
        """
        # Create base payslip
        payslip = Payslip.create(
            employee_id=employee_info.employee_id,
            period=period,
            payroll_id=payroll_id
        )
        payslip.exchange_rate = exchange_rate.zig_to_usd_rate

        # Calculate earnings
        earnings = self._calculate_earnings(employee_info)
        payslip.set_earnings(earnings)

        # Calculate deductions
        deductions = self._calculate_deductions(
            employee_info=employee_info,
            earnings=earnings,
            usd_tax_table=usd_tax_table,
            zig_tax_table=zig_tax_table,
            exchange_rate=exchange_rate
        )
        payslip.set_deductions(deductions)

        # Calculate net salary
        payslip.net_salary_usd = earnings.gross_usd - deductions.total_usd
        payslip.net_salary_zig = earnings.gross_zig - deductions.total_zig

        return payslip

    def _calculate_earnings(self, employee_info: EmployeeSalaryInfo) -> Earnings:
        """Calculate total earnings including allowances."""
        # Sum allowances by currency
        usd_allowances = Decimal("0")
        zig_allowances = Decimal("0")
        allowance_items = []

        for allowance in employee_info.allowances:
            if allowance.currency == Currency.USD:
                usd_allowances += allowance.amount
            else:
                zig_allowances += allowance.amount
            allowance_items.append({
                "name": allowance.allowance_type_name,
                "amount_usd": allowance.amount if allowance.currency == Currency.USD else Decimal("0"),
                "amount_zig": allowance.amount if allowance.currency == Currency.ZIG else Decimal("0"),
            })

        return Earnings.create(
            base_usd=employee_info.usd_salary or Decimal("0"),
            base_zig=employee_info.zig_salary or Decimal("0"),
            allowances_list=allowance_items
        )

    def _calculate_deductions(
        self,
        employee_info: EmployeeSalaryInfo,
        earnings: Earnings,
        usd_tax_table: TaxTable,
        zig_tax_table: TaxTable,
        exchange_rate: ExchangeRate
    ) -> Deductions:
        """Calculate all deductions including statutory and voluntary."""
        # Calculate USD statutory deductions
        usd_paye = self.tax_calculator.calculate_paye(
            earnings.gross_usd, usd_tax_table
        )
        usd_aids = self.aids_calculator.calculate(
            usd_paye, employee_info.pays_aids_levy
        )
        usd_nssa_emp, usd_nssa_employer = self.nssa_calculator.calculate(
            earnings.gross_usd, Currency.USD
        )

        # For ZIG, we need to convert to USD for tax calculation
        # then convert back to ZIG
        zig_gross_usd = exchange_rate.convert_zig_to_usd(earnings.gross_zig)
        zig_paye_usd = self.tax_calculator.calculate_paye(
            zig_gross_usd, zig_tax_table
        )
        zig_aids_usd = self.aids_calculator.calculate(
            zig_paye_usd, employee_info.pays_aids_levy
        )
        zig_nssa_emp_usd, zig_nssa_employer_usd = self.nssa_calculator.calculate(
            zig_gross_usd, Currency.USD
        )

        # Convert ZIG statutory back to ZIG
        zig_paye = exchange_rate.convert_usd_to_zig(zig_paye_usd)
        zig_aids = exchange_rate.convert_usd_to_zig(zig_aids_usd)
        zig_nssa_emp = exchange_rate.convert_usd_to_zig(zig_nssa_emp_usd)
        zig_nssa_employer = exchange_rate.convert_usd_to_zig(zig_nssa_employer_usd)

        # Sum other deductions by currency
        other_deductions = []
        for deduction in employee_info.deductions:
            other_deductions.append({
                "name": deduction.deduction_type_name,
                "amount_usd": deduction.amount if deduction.currency == Currency.USD else Decimal("0"),
                "amount_zig": deduction.amount if deduction.currency == Currency.ZIG else Decimal("0"),
            })

        return Deductions.create_statutory(
            paye_usd=usd_paye,
            paye_zig=zig_paye,
            aids_levy_usd=usd_aids,
            aids_levy_zig=zig_aids,
            nssa_employee_usd=usd_nssa_emp,
            nssa_employee_zig=zig_nssa_emp,
            nssa_employer_usd=usd_nssa_employer,
            nssa_employer_zig=zig_nssa_employer,
            other_deductions=other_deductions
        )


class GrossPayCalculator:
    """Service for calculating gross pay."""

    @staticmethod
    def calculate(
        base_salary: Decimal,
        allowances: List[EmployeeAllowance],
        currency: Currency
    ) -> Decimal:
        """
        Calculate gross pay.

        Args:
            base_salary: Base salary amount
            allowances: List of employee allowances
            currency: Currency to filter allowances

        Returns:
            Gross pay amount
        """
        total_allowances = sum(
            (a.amount for a in allowances if a.currency == currency),
            Decimal("0")
        )
        return (base_salary + total_allowances).quantize(Decimal("0.01"))


class NetPayCalculator:
    """Service for calculating net pay."""

    @staticmethod
    def calculate(
        gross_salary: Decimal,
        total_deductions: Decimal
    ) -> Decimal:
        """
        Calculate net pay.

        Args:
            gross_salary: Gross salary amount
            total_deductions: Total deductions amount

        Returns:
            Net pay amount (can be negative if deductions exceed gross)
        """
        return (gross_salary - total_deductions).quantize(Decimal("0.01"))
