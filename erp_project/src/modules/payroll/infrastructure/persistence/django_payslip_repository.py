"""
Django ORM repository for Payslip.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from django.db import transaction

from modules.payroll.infrastructure.persistence.models import Payroll as PayrollModel

from modules.payroll.domain.entities import Payslip
from modules.payroll.domain.value_objects import PayrollPeriod, PayslipStatus
from modules.payroll.application.interfaces import IPayslipRepository


class DjangoPayslipRepository(IPayslipRepository):
    """
    Django ORM implementation of IPayslipRepository.

    Maps to the legacy Payroll model which is actually a payslip
    (one record per employee per period).
    """

    def get_by_id(self, payslip_id: int) -> Optional[Payslip]:
        """Get payslip by ID."""
        try:
            model = PayrollModel.objects.select_related("employee").get(id=payslip_id)
            return self._to_entity(model)
        except PayrollModel.DoesNotExist:
            return None

    def get_by_employee_and_period(
        self, employee_id: int, period: PayrollPeriod
    ) -> Optional[Payslip]:
        """Get payslip for an employee in a specific period."""
        model = PayrollModel.objects.filter(
            employee_id=employee_id,
            period__year=period.year,
            period__month=period.month
        ).select_related("employee").first()

        return self._to_entity(model) if model else None

    def get_by_payroll(self, payroll_id: int) -> List[Payslip]:
        """Get all payslips in a payroll batch."""
        # In legacy system, payroll_id is not stored separately
        # This method would need a payroll batch table
        return []

    def get_by_period(self, period: PayrollPeriod) -> List[Payslip]:
        """Get all payslips for a period."""
        models = PayrollModel.objects.filter(
            period__year=period.year,
            period__month=period.month
        ).select_related("employee").order_by("employee__employee_id")

        return [self._to_entity(m) for m in models]

    def save(self, payslip: Payslip) -> Payslip:
        """Save a payslip."""
        if payslip.id:
            model = self._update_model(payslip)
        else:
            model = self._create_model(payslip)

        return self._to_entity(model)

    @transaction.atomic
    def save_batch(self, payslips: List[Payslip]) -> List[Payslip]:
        """Save multiple payslips."""
        saved = []
        for payslip in payslips:
            saved.append(self.save(payslip))
        return saved

    def delete(self, payslip_id: int) -> bool:
        """Delete a payslip."""
        try:
            PayrollModel.objects.filter(id=payslip_id).delete()
            return True
        except Exception:
            return False

    def _to_entity(self, model: PayrollModel) -> Payslip:
        """Convert Django model to domain entity."""
        # Create period from the model's period date
        period = PayrollPeriod(
            year=model.period.year,
            month=model.period.month
        )

        # Map status
        status_map = {
            "Draft": PayslipStatus.DRAFT,
            "Pending": PayslipStatus.PENDING,
            "Processed": PayslipStatus.PROCESSED,
            "Failed": PayslipStatus.FAILED,
            "Paid": PayslipStatus.PAID,
        }
        status = status_map.get(model.status, PayslipStatus.DRAFT)

        return Payslip(
            id=model.id,
            payroll_id=None,  # Legacy system doesn't have batch payroll ID
            employee_id=model.employee_id,
            period=period,
            base_salary_usd=model.base_salary_usd or Decimal("0"),
            base_salary_zig=model.base_salary_zig or Decimal("0"),
            total_allowances_usd=model.total_allowances_usd or Decimal("0"),
            total_allowances_zig=model.total_allowances_zig or Decimal("0"),
            gross_usd=(model.base_salary_usd or Decimal("0")) + (model.total_allowances_usd or Decimal("0")),
            gross_zig=(model.base_salary_zig or Decimal("0")) + (model.total_allowances_zig or Decimal("0")),
            paye_usd=model.paye_usd or Decimal("0"),
            paye_zig=model.paye_zig or Decimal("0"),
            aids_levy_usd=model.aids_levy_usd or Decimal("0"),
            aids_levy_zig=model.aids_levy_zig or Decimal("0"),
            nssa_employee_usd=model.nssa_employee_usd or Decimal("0"),
            nssa_employee_zig=model.nssa_employee_zig or Decimal("0"),
            nssa_employer_usd=model.nssa_employer_usd or Decimal("0"),
            nssa_employer_zig=model.nssa_employer_zig or Decimal("0"),
            other_deductions_usd=model.total_deductions_usd or Decimal("0"),
            other_deductions_zig=model.total_deductions_zig or Decimal("0"),
            total_deductions_usd=self._calc_total_deductions_usd(model),
            total_deductions_zig=self._calc_total_deductions_zig(model),
            net_salary_usd=model.net_salary_usd or Decimal("0"),
            net_salary_zig=model.net_salary_zig or Decimal("0"),
            exchange_rate=model.exchange_rate or Decimal("0"),
            status=status,
            notes=model.notes or "",
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _calc_total_deductions_usd(self, model: PayrollModel) -> Decimal:
        """Calculate total deductions in USD."""
        return (
            (model.paye_usd or Decimal("0")) +
            (model.aids_levy_usd or Decimal("0")) +
            (model.nssa_employee_usd or Decimal("0")) +
            (model.total_deductions_usd or Decimal("0"))
        )

    def _calc_total_deductions_zig(self, model: PayrollModel) -> Decimal:
        """Calculate total deductions in ZIG."""
        return (
            (model.paye_zig or Decimal("0")) +
            (model.aids_levy_zig or Decimal("0")) +
            (model.nssa_employee_zig or Decimal("0")) +
            (model.total_deductions_zig or Decimal("0"))
        )

    def _create_model(self, entity: Payslip) -> PayrollModel:
        """Create Django model from entity."""
        period_date = date(entity.period.year, entity.period.month, 1)

        return PayrollModel.objects.create(
            employee_id=entity.employee_id,
            period=period_date,
            base_salary_usd=entity.base_salary_usd,
            base_salary_zig=entity.base_salary_zig,
            net_salary_usd=entity.net_salary_usd,
            net_salary_zig=entity.net_salary_zig,
            exchange_rate=entity.exchange_rate,
            paye_usd=entity.paye_usd,
            paye_zig=entity.paye_zig,
            aids_levy_usd=entity.aids_levy_usd,
            aids_levy_zig=entity.aids_levy_zig,
            nssa_employee_usd=entity.nssa_employee_usd,
            nssa_employee_zig=entity.nssa_employee_zig,
            nssa_employer_usd=entity.nssa_employer_usd,
            nssa_employer_zig=entity.nssa_employer_zig,
            total_allowances_usd=entity.total_allowances_usd,
            total_allowances_zig=entity.total_allowances_zig,
            total_deductions_usd=entity.other_deductions_usd,
            total_deductions_zig=entity.other_deductions_zig,
            status=entity.status.value,
            notes=entity.notes
        )

    def _update_model(self, entity: Payslip) -> PayrollModel:
        """Update existing Django model."""
        model = PayrollModel.objects.get(id=entity.id)

        model.base_salary_usd = entity.base_salary_usd
        model.base_salary_zig = entity.base_salary_zig
        model.net_salary_usd = entity.net_salary_usd
        model.net_salary_zig = entity.net_salary_zig
        model.exchange_rate = entity.exchange_rate
        model.paye_usd = entity.paye_usd
        model.paye_zig = entity.paye_zig
        model.aids_levy_usd = entity.aids_levy_usd
        model.aids_levy_zig = entity.aids_levy_zig
        model.nssa_employee_usd = entity.nssa_employee_usd
        model.nssa_employee_zig = entity.nssa_employee_zig
        model.nssa_employer_usd = entity.nssa_employer_usd
        model.nssa_employer_zig = entity.nssa_employer_zig
        model.total_allowances_usd = entity.total_allowances_usd
        model.total_allowances_zig = entity.total_allowances_zig
        model.total_deductions_usd = entity.other_deductions_usd
        model.total_deductions_zig = entity.other_deductions_zig
        model.status = entity.status.value
        model.notes = entity.notes

        model.save()
        return model
