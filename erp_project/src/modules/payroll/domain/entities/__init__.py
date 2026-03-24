"""
Payroll domain entities.
"""

from modules.payroll.domain.entities.tax_table import TaxTable
from modules.payroll.domain.entities.exchange_rate import ExchangeRate
from modules.payroll.domain.entities.allowance_type import AllowanceType, EmployeeAllowance
from modules.payroll.domain.entities.deduction_type import DeductionType, EmployeeDeduction
from modules.payroll.domain.entities.payslip import Payslip
from modules.payroll.domain.entities.payroll import Payroll, PayrollSummary

__all__ = [
    "TaxTable",
    "ExchangeRate",
    "AllowanceType",
    "EmployeeAllowance",
    "DeductionType",
    "EmployeeDeduction",
    "Payslip",
    "Payroll",
    "PayrollSummary",
]
