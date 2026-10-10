"""
Portal payslip service.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from modules.portal.application.interfaces import (
    EmployeeDTO,
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

    # Responses below have the shapes the portal reads
    # (employee-portal/src/types/payslip.types.ts), amounts as numbers. PY-2.

    def get_payslip_list(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> dict:
        """PayslipsResponse: the year's payslips (all when no year), newest
        first, plus every year that has one."""
        visible = self.get_payslips(employee_id)
        shown = [p for p in visible if year is None or p.period_year == year]
        return {
            "payslips": [_list_item(p) for p in shown],
            "available_years": sorted({p.period_year for p in visible}, reverse=True),
            "current_year": year if year is not None else date.today().year,
        }

    def get_payslip_breakdown(
        self,
        employee: EmployeeDTO,
        payslip_id: int,
    ) -> Optional[dict]:
        """PayslipDetail for one of the employee's own visible payslips."""
        payslip = self.get_payslip(employee.id, payslip_id)
        if payslip is None:
            return None

        other_usd = (
            payslip.total_deductions_usd
            - payslip.paye_usd
            - payslip.aids_levy_usd
            - payslip.nssa_employee_usd
        )
        other_zig = (
            payslip.total_deductions_zig
            - payslip.paye_zig
            - payslip.aids_levy_zig
            - payslip.nssa_employee_zig
        )
        gross = _amount(payslip.gross_usd, payslip.gross_zig)
        total = _amount(payslip.total_deductions_usd, payslip.total_deductions_zig)
        net = _amount(payslip.net_salary_usd, payslip.net_salary_zig)
        return {
            **_period_fields(payslip),
            "id": payslip.id,
            "status": payslip.status,
            "employee_name": f"{employee.first_name} {employee.surname}".strip(),
            "employee_id": employee.employee_id,
            "department": employee.department_name or "",
            "position": employee.position_name or "",
            "exchange_rate": _number(payslip.exchange_rate),
            "earnings": {
                "base_salary": _amount(payslip.base_salary_usd, payslip.base_salary_zig),
                "allowances": _amount(payslip.allowances_usd, payslip.allowances_zig),
                "gross": gross,
            },
            "deductions": {
                "paye": _amount(payslip.paye_usd, payslip.paye_zig),
                "aids_levy": _amount(payslip.aids_levy_usd, payslip.aids_levy_zig),
                "nssa_employee": _amount(payslip.nssa_employee_usd, payslip.nssa_employee_zig),
                "other_deductions": _amount(other_usd, other_zig),
                "total": total,
            },
            "summary": {
                "gross_salary": gross,
                "total_deductions": total,
                "net_salary": net,
            },
            "notes": payslip.notes,
            "created_at": payslip.created_at.isoformat() if payslip.created_at else None,
        }

    def get_yearly_summary(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> dict:
        """PayslipYearSummary: the year's totals over the visible payslips."""
        if year is None:
            year = date.today().year
        payslips = self.get_payslips(employee_id, year)

        def total(field: str) -> float:
            return _number(sum((getattr(p, field) for p in payslips), Decimal("0")))

        return {
            "year": year,
            "total_gross_usd": total("gross_usd"),
            "total_gross_zig": total("gross_zig"),
            "total_deductions_usd": total("total_deductions_usd"),
            "total_deductions_zig": total("total_deductions_zig"),
            "total_net_usd": total("net_salary_usd"),
            "total_net_zig": total("net_salary_zig"),
            "payslip_count": len(payslips),
        }


def _number(value) -> float:
    return float(Decimal(value).quantize(Decimal("0.01")))


def _amount(usd, zig) -> dict:
    return {"usd": _number(usd), "zig": _number(zig)}


def _period_fields(payslip: PayslipDTO) -> dict:
    period = date(payslip.period_year, payslip.period_month, 1)
    return {
        "period": period.strftime("%Y-%m"),
        "period_display": period.strftime("%B %Y"),
        "month": payslip.period_month,
        "year": payslip.period_year,
    }


def _list_item(payslip: PayslipDTO) -> dict:
    return {
        **_period_fields(payslip),
        "id": payslip.id,
        "status": payslip.status,
        "base_salary_usd": _number(payslip.base_salary_usd),
        "net_salary_usd": _number(payslip.net_salary_usd),
        "base_salary_zig": _number(payslip.base_salary_zig),
        "net_salary_zig": _number(payslip.net_salary_zig),
        "exchange_rate": _number(payslip.exchange_rate),
    }
