"""
Actor-aware access to stored payslips: list, detail, approval and period summary.

Like RoleService (REM-05), this works against the Django models directly:
payroll has no repository for the ``Payroll`` payslip table, and building one
is out of scope for the authorization fix this service exists to provide. What
it adds to the pre-existing view logic is the authorization boundary itself:
every method authorizes first, and nothing sensitive is loaded, returned or
mutated until that succeeds.
"""

from django.db.models import Count, Sum

from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
    PayslipTarget,
)
from modules.payroll.infrastructure.persistence.models import Payroll
from shared.domain.exceptions import NotFoundError, ValidationError


class PayslipAccessService:
    def __init__(self, policy: PayrollAuthorizationPolicy | None = None) -> None:
        self._policy = policy or PayrollAuthorizationPolicy()

    def list_payslips(self, actor: PayrollActor, year: int, month: int) -> list[Payroll]:
        """Payslips for a period, filtered to those the actor may view."""
        self._policy.authorize_list_payslips(actor)
        payslips = (
            Payroll.objects.filter(period__year=year, period__month=month)
            .select_related("employee", "employee__department")
            .order_by("employee__employee_id")
        )
        return self._policy.filter_viewable_payslips(actor, payslips)

    def get_payslip(self, actor: PayrollActor, payslip_id: int) -> Payroll:
        """
        Raises:
            AuthorizationError: Whether or not the payslip exists.
            NotFoundError: Only once the actor is authorized.
        """
        target = self._target(payslip_id)
        self._policy.authorize_view_payslip(actor, target)
        if target is None:
            raise NotFoundError("Payslip not found")
        return Payroll.objects.select_related("employee", "employee__department").get(
            id=payslip_id
        )

    def approve_payslip(self, actor: PayrollActor, payslip_id: int) -> Payroll:
        """Mark a Draft payslip Processed. Nothing changes unless authorized."""
        target = self._target(payslip_id)
        self._policy.authorize_approve_payslip(actor, target)
        if target is None:
            raise NotFoundError("Payslip not found")

        payslip = Payroll.objects.get(id=payslip_id)
        if payslip.status != "Draft":
            raise ValidationError(
                f"Cannot approve payslip in {payslip.status} status",
                code="PAYSLIP_NOT_DRAFT",
            )

        payslip.status = "Processed"
        payslip.save()
        return payslip

    def get_period_summary(self, actor: PayrollActor, year: int, month: int) -> dict:
        """
        Aggregated totals for a period.

        Raises:
            NotFoundError: If the period has no payroll data (after authorization).
        """
        self._policy.authorize_view_summary(actor)
        payslips = Payroll.objects.filter(period__year=year, period__month=month)
        if not payslips.exists():
            raise NotFoundError("No payroll data for this period")

        return payslips.aggregate(
            total_employees=Count("id"),
            total_base_usd=Sum("base_salary_usd"),
            total_base_zig=Sum("base_salary_zig"),
            total_allowances_usd=Sum("total_allowances_usd"),
            total_allowances_zig=Sum("total_allowances_zig"),
            total_net_usd=Sum("net_salary_usd"),
            total_net_zig=Sum("net_salary_zig"),
            total_paye_usd=Sum("paye_usd"),
            total_paye_zig=Sum("paye_zig"),
            total_nssa_emp_usd=Sum("nssa_employee_usd"),
            total_nssa_emp_zig=Sum("nssa_employee_zig"),
            total_nssa_employer_usd=Sum("nssa_employer_usd"),
            total_nssa_employer_zig=Sum("nssa_employer_zig"),
        )

    @staticmethod
    def _target(payslip_id: int) -> PayslipTarget | None:
        """The minimum identity needed to authorize; no payslip data is loaded."""
        employee_id = (
            Payroll.objects.filter(id=payslip_id)
            .values_list("employee_id", flat=True)
            .first()
        )
        if employee_id is None:
            return None
        return PayslipTarget(payslip_id=payslip_id, employee_id=employee_id)
