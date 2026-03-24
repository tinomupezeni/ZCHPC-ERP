"""
Payroll application layer.

Contains application services, interfaces, and DTOs.
"""

from modules.payroll.application.interfaces import (
    # Repositories
    ITaxTableRepository,
    IExchangeRateRepository,
    IAllowanceTypeRepository,
    IDeductionTypeRepository,
    IEmployeeAllowanceRepository,
    IEmployeeDeductionRepository,
    IPayslipRepository,
    IPayrollRepository,
    # DTOs
    PayslipDTO,
    PayrollSummaryDTO,
    TaxBracketDTO,
    ExchangeRateDTO,
    # Providers
    IPayrollProvider,
    IEmployeePayrollInfoProvider,
)
from modules.payroll.application.services import (
    PayrollService,
    ProcessPayrollCommand,
    ProcessPayrollResult,
    ExchangeRateService,
    CreateExchangeRateCommand,
    UpdateExchangeRateCommand,
    PayrollProvider,
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
    # Services
    "PayrollService",
    "ProcessPayrollCommand",
    "ProcessPayrollResult",
    "ExchangeRateService",
    "CreateExchangeRateCommand",
    "UpdateExchangeRateCommand",
    "PayrollProvider",
]
