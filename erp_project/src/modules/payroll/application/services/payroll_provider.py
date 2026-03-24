"""
PayrollProvider implementation for cross-module communication.
"""

from datetime import date
from typing import List, Optional

from modules.payroll.domain.value_objects import PayrollPeriod, Currency
from modules.payroll.application.interfaces import (
    IPayrollRepository,
    IPayslipRepository,
    ITaxTableRepository,
    IExchangeRateRepository,
    PayslipDTO,
    PayrollSummaryDTO,
    TaxBracketDTO,
    ExchangeRateDTO,
    IPayrollProvider,
)


class PayrollProvider(IPayrollProvider):
    """
    Provides payroll information to other modules.

    Implements the IPayrollProvider interface for read-only access
    to payroll data.
    """

    def __init__(
        self,
        payroll_repository: IPayrollRepository,
        payslip_repository: IPayslipRepository,
        tax_repository: ITaxTableRepository,
        exchange_rate_repository: IExchangeRateRepository
    ):
        self.payroll_repo = payroll_repository
        self.payslip_repo = payslip_repository
        self.tax_repo = tax_repository
        self.rate_repo = exchange_rate_repository

    def get_payslip(
        self, employee_id: int, period: PayrollPeriod
    ) -> Optional[PayslipDTO]:
        """Get payslip for an employee in a specific period."""
        payslip = self.payslip_repo.get_by_employee_and_period(
            employee_id, period
        )
        if not payslip:
            return None

        return PayslipDTO(
            id=payslip.id,
            employee_id=payslip.employee_id,
            period_year=period.year,
            period_month=period.month,
            base_salary_usd=payslip.base_salary_usd,
            base_salary_zig=payslip.base_salary_zig,
            gross_usd=payslip.gross_usd,
            gross_zig=payslip.gross_zig,
            total_deductions_usd=payslip.total_deductions_usd,
            total_deductions_zig=payslip.total_deductions_zig,
            net_salary_usd=payslip.net_salary_usd,
            net_salary_zig=payslip.net_salary_zig,
            status=payslip.status.value
        )

    def get_payslips_for_period(
        self, period: PayrollPeriod
    ) -> List[PayslipDTO]:
        """Get all payslips for a period."""
        payslips = self.payslip_repo.get_by_period(period)
        return [
            PayslipDTO(
                id=ps.id,
                employee_id=ps.employee_id,
                period_year=period.year,
                period_month=period.month,
                base_salary_usd=ps.base_salary_usd,
                base_salary_zig=ps.base_salary_zig,
                gross_usd=ps.gross_usd,
                gross_zig=ps.gross_zig,
                total_deductions_usd=ps.total_deductions_usd,
                total_deductions_zig=ps.total_deductions_zig,
                net_salary_usd=ps.net_salary_usd,
                net_salary_zig=ps.net_salary_zig,
                status=ps.status.value
            )
            for ps in payslips
        ]

    def get_payroll_summary(
        self, period: PayrollPeriod
    ) -> Optional[PayrollSummaryDTO]:
        """Get summary for a payroll period."""
        payroll = self.payroll_repo.get_by_period(period)
        if not payroll:
            return None

        return PayrollSummaryDTO(
            period_year=period.year,
            period_month=period.month,
            total_employees=payroll.total_employees,
            total_gross_usd=payroll.total_gross_usd,
            total_gross_zig=payroll.total_gross_zig,
            total_net_usd=payroll.total_net_usd,
            total_net_zig=payroll.total_net_zig,
            total_paye_usd=payroll.total_paye_usd,
            total_paye_zig=payroll.total_paye_zig,
            total_nssa_usd=payroll.total_nssa_usd,
            total_nssa_zig=payroll.total_nssa_zig,
            status=payroll.status.value
        )

    def get_latest_exchange_rate(self) -> Optional[ExchangeRateDTO]:
        """Get the latest exchange rate."""
        rate = self.rate_repo.get_latest()
        if not rate:
            return None

        return ExchangeRateDTO(
            id=rate.id,
            rate_date=rate.rate_date,
            zig_to_usd_rate=rate.zig_to_usd_rate,
            usd_to_zig_rate=rate.usd_to_zig_rate,
            source=rate.source
        )

    def get_tax_brackets(self, currency: str) -> List[TaxBracketDTO]:
        """Get tax brackets for a currency."""
        try:
            curr = Currency.from_string(currency)
        except ValueError:
            return []

        tax_table = self.tax_repo.get_active_for_currency(curr, date.today())
        if not tax_table:
            return []

        return [
            TaxBracketDTO(
                id=i,  # Index as ID since brackets are value objects
                currency=currency,
                min_income=bracket.min_income,
                max_income=bracket.max_income,
                rate=bracket.rate,
                deduction=bracket.deduction,
                active_from=tax_table.effective_from
            )
            for i, bracket in enumerate(tax_table.brackets)
        ]
