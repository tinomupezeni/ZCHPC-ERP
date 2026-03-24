"""
Portal payslip service.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from modules.portal.application.interfaces import (
    IPayrollProvider,
    PayslipDTO,
)


class PortalPayslipService:
    """
    Payslip service for employee portal.

    Provides read-only access to employee payslips.
    """

    def __init__(
        self,
        payroll_provider: IPayrollProvider,
    ) -> None:
        self._payroll_provider = payroll_provider

    def get_payslips(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[PayslipDTO]:
        """
        Get payslips for an employee.

        Args:
            employee_id: Employee ID
            year: Optional year filter

        Returns:
            List of payslips (only Processed/Paid status)
        """
        payslips = self._payroll_provider.get_payslips(
            employee_id=employee_id,
            year=year,
        )

        # Filter to only show processed/paid payslips
        return [
            p for p in payslips
            if p.status in ("Processed", "Paid")
        ]

    def get_payslip(
        self,
        employee_id: int,
        payslip_id: int,
    ) -> Optional[PayslipDTO]:
        """
        Get a specific payslip.

        Args:
            employee_id: Employee ID (for verification)
            payslip_id: Payslip ID

        Returns:
            Payslip if found and belongs to employee
        """
        payslip = self._payroll_provider.get_payslip(payslip_id)

        if payslip is None:
            return None

        # Verify belongs to employee
        if payslip.employee_id != employee_id:
            return None

        # Verify status
        if payslip.status not in ("Processed", "Paid"):
            return None

        return payslip

    def get_payslip_breakdown(
        self,
        employee_id: int,
        payslip_id: int,
    ) -> Optional[dict]:
        """
        Get detailed payslip breakdown.

        Returns:
            Dict with categorized earnings and deductions
        """
        payslip = self.get_payslip(employee_id, payslip_id)
        if payslip is None:
            return None

        return {
            "period": f"{payslip.period_year}-{payslip.period_month:02d}",
            "exchange_rate": str(payslip.exchange_rate),
            "earnings": {
                "base_salary": {
                    "usd": str(payslip.base_salary_usd),
                    "zig": str(payslip.base_salary_zig),
                },
                "allowances": {
                    "usd": str(payslip.allowances_usd),
                    "zig": str(payslip.allowances_zig),
                },
                "gross": {
                    "usd": str(payslip.gross_usd),
                    "zig": str(payslip.gross_zig),
                },
            },
            "deductions": {
                "paye": {
                    "usd": str(payslip.paye_usd),
                    "zig": str(payslip.paye_zig),
                },
                "aids_levy": {
                    "usd": str(payslip.aids_levy_usd),
                    "zig": str(payslip.aids_levy_zig),
                },
                "nssa": {
                    "usd": str(payslip.nssa_employee_usd),
                    "zig": str(payslip.nssa_employee_zig),
                },
                "total": {
                    "usd": str(payslip.total_deductions_usd),
                    "zig": str(payslip.total_deductions_zig),
                },
            },
            "net_salary": {
                "usd": str(payslip.net_salary_usd),
                "zig": str(payslip.net_salary_zig),
            },
            "status": payslip.status,
        }

    def get_yearly_summary(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> dict:
        """
        Get yearly payslip summary.

        Returns:
            Dict with yearly totals and averages
        """
        if year is None:
            year = date.today().year

        payslips = self.get_payslips(employee_id, year)

        if not payslips:
            return {
                "year": year,
                "payslip_count": 0,
                "totals": None,
            }

        # Calculate totals
        total_gross_usd = sum(p.gross_usd for p in payslips)
        total_gross_zig = sum(p.gross_zig for p in payslips)
        total_deductions_usd = sum(p.total_deductions_usd for p in payslips)
        total_deductions_zig = sum(p.total_deductions_zig for p in payslips)
        total_net_usd = sum(p.net_salary_usd for p in payslips)
        total_net_zig = sum(p.net_salary_zig for p in payslips)
        total_paye_usd = sum(p.paye_usd for p in payslips)
        total_nssa_usd = sum(p.nssa_employee_usd for p in payslips)

        count = len(payslips)

        return {
            "year": year,
            "payslip_count": count,
            "totals": {
                "gross": {
                    "usd": str(total_gross_usd),
                    "zig": str(total_gross_zig),
                },
                "deductions": {
                    "usd": str(total_deductions_usd),
                    "zig": str(total_deductions_zig),
                },
                "net": {
                    "usd": str(total_net_usd),
                    "zig": str(total_net_zig),
                },
                "paye": str(total_paye_usd),
                "nssa": str(total_nssa_usd),
            },
            "averages": {
                "gross_usd": str(total_gross_usd / count),
                "net_usd": str(total_net_usd / count),
            },
            "months": [
                {
                    "month": p.period_month,
                    "net_usd": str(p.net_salary_usd),
                }
                for p in sorted(payslips, key=lambda x: x.period_month)
            ],
        }
