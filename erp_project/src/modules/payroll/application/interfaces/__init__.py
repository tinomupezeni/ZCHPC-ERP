"""
Payroll application interfaces.
"""

from modules.payroll.application.interfaces.repositories import (
    ITaxTableRepository,
    IExchangeRateRepository,
    IAllowanceTypeRepository,
    IDeductionTypeRepository,
    IEmployeeAllowanceRepository,
    IEmployeeDeductionRepository,
    IPayslipRepository,
    IPayrollRepository,
)
from modules.payroll.application.interfaces.providers import (
    PayslipDTO,
    PayrollSummaryDTO,
    TaxBracketDTO,
    ExchangeRateDTO,
    IPayrollProvider,
    IEmployeePayrollInfoProvider,
)

__all__ = [
    # Repositories
    "ITaxTableRepository",
    "IExchangeRateRepository",
    "IAllowanceTypeRepository",
    "IDeductionTypeRepository",
    "IEmployeeAllowanceRepository",
    "IEmployeeDeductionRepository",
    "IPayslipRepository",
    "IPayrollRepository",
    # DTOs
    "PayslipDTO",
    "PayrollSummaryDTO",
    "TaxBracketDTO",
    "ExchangeRateDTO",
    # Providers
    "IPayrollProvider",
    "IEmployeePayrollInfoProvider",
]
