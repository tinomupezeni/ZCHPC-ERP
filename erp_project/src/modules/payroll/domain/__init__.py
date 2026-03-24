"""
Payroll domain layer.

Contains entities, value objects, events, and domain services.
"""

from modules.payroll.domain.value_objects import (
    PayrollPeriod,
    PayrollStatus,
    PayslipStatus,
    TaxBracket,
    Currency,
    Earnings,
    AllowanceItem,
    Deductions,
    DeductionItem,
)
from modules.payroll.domain.entities import (
    TaxTable,
    ExchangeRate,
    AllowanceType,
    EmployeeAllowance,
    DeductionType,
    EmployeeDeduction,
    Payslip,
    Payroll,
    PayrollSummary,
)
from modules.payroll.domain.events import (
    PayrollOpened,
    PayrollProcessingStarted,
    PayrollProcessed,
    PayrollClosed,
    PayrollReopened,
    PayslipGenerated,
    PayslipApproved,
    PayslipPaid,
    TaxBracketUpdated,
    ExchangeRateUpdated,
)
from modules.payroll.domain.services import (
    TaxCalculator,
    AIDSLevyCalculator,
    NSSACalculator,
    StatutoryCalculator,
    PayslipGenerator,
    EmployeeSalaryInfo,
    GrossPayCalculator,
    NetPayCalculator,
)

__all__ = [
    # Value Objects
    "PayrollPeriod",
    "PayrollStatus",
    "PayslipStatus",
    "TaxBracket",
    "Currency",
    "Earnings",
    "AllowanceItem",
    "Deductions",
    "DeductionItem",
    # Entities
    "TaxTable",
    "ExchangeRate",
    "AllowanceType",
    "EmployeeAllowance",
    "DeductionType",
    "EmployeeDeduction",
    "Payslip",
    "Payroll",
    "PayrollSummary",
    # Events
    "PayrollOpened",
    "PayrollProcessingStarted",
    "PayrollProcessed",
    "PayrollClosed",
    "PayrollReopened",
    "PayslipGenerated",
    "PayslipApproved",
    "PayslipPaid",
    "TaxBracketUpdated",
    "ExchangeRateUpdated",
    # Services
    "TaxCalculator",
    "AIDSLevyCalculator",
    "NSSACalculator",
    "StatutoryCalculator",
    "PayslipGenerator",
    "EmployeeSalaryInfo",
    "GrossPayCalculator",
    "NetPayCalculator",
]
