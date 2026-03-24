"""
Payroll Module.

Manages salary processing, tax calculation, NSSA contributions,
AIDS levy, allowances, deductions, and payslip generation.

Provides IPayrollProvider interface for cross-module integration.
"""

from modules.payroll.domain import (
    # Value Objects
    PayrollPeriod,
    PayrollStatus,
    PayslipStatus,
    TaxBracket,
    Currency,
    Earnings,
    Deductions,
    # Entities
    TaxTable,
    ExchangeRate,
    AllowanceType,
    DeductionType,
    Payslip,
    Payroll,
    PayrollSummary,
    # Services
    TaxCalculator,
    AIDSLevyCalculator,
    NSSACalculator,
    PayslipGenerator,
)
from modules.payroll.application import (
    # DTOs
    PayslipDTO,
    PayrollSummaryDTO,
    TaxBracketDTO,
    ExchangeRateDTO,
    # Providers
    IPayrollProvider,
    PayrollProvider,
    # Services
    PayrollService,
    ExchangeRateService,
)

__all__ = [
    # Value Objects
    "PayrollPeriod",
    "PayrollStatus",
    "PayslipStatus",
    "TaxBracket",
    "Currency",
    "Earnings",
    "Deductions",
    # Entities
    "TaxTable",
    "ExchangeRate",
    "AllowanceType",
    "DeductionType",
    "Payslip",
    "Payroll",
    "PayrollSummary",
    # Domain Services
    "TaxCalculator",
    "AIDSLevyCalculator",
    "NSSACalculator",
    "PayslipGenerator",
    # DTOs
    "PayslipDTO",
    "PayrollSummaryDTO",
    "TaxBracketDTO",
    "ExchangeRateDTO",
    # Providers
    "IPayrollProvider",
    "PayrollProvider",
    # Services
    "PayrollService",
    "ExchangeRateService",
]
