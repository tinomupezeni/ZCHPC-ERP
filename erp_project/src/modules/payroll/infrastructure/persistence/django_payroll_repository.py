"""
Django ORM repository for the Payroll (batch) aggregate.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from modules.payroll.infrastructure.persistence.models import PayrollBatch as PayrollBatchModel

from modules.payroll.domain.entities import Payroll, PayrollSummary
from modules.payroll.domain.value_objects import PayrollPeriod, PayrollStatus
from modules.payroll.application.interfaces import IPayrollRepository


class DjangoPayrollRepository(IPayrollRepository):
    """Django ORM implementation of IPayrollRepository, backed by PayrollBatch."""

    def get_by_id(self, payroll_id: int) -> Optional[Payroll]:
        """Get payroll by ID."""
        try:
            model = PayrollBatchModel.objects.get(id=payroll_id)
            return self._to_entity(model)
        except PayrollBatchModel.DoesNotExist:
            return None

    def get_by_period(self, period: PayrollPeriod) -> Optional[Payroll]:
        """Get payroll for a specific period."""
        try:
            model = PayrollBatchModel.objects.get(
                period__year=period.year, period__month=period.month
            )
            return self._to_entity(model)
        except PayrollBatchModel.DoesNotExist:
            return None

    def get_all(self, year: Optional[int] = None) -> List[Payroll]:
        """Get all payrolls, optionally filtered by year."""
        queryset = PayrollBatchModel.objects.all()
        if year is not None:
            queryset = queryset.filter(period__year=year)
        return [self._to_entity(m) for m in queryset]

    def save(self, payroll: Payroll) -> Payroll:
        """Save a payroll."""
        period_date = date(payroll.period.year, payroll.period.month, 1)

        model, _ = PayrollBatchModel.objects.update_or_create(
            period=period_date,
            defaults={
                "status": payroll.status.value,
                "processed_at": payroll.processed_at,
                "processed_by": payroll.processed_by,
                "closed_at": payroll.closed_at,
                "closed_by": payroll.closed_by,
                "notes": payroll.notes,
                "total_employees": payroll.total_employees,
                "total_gross_usd": payroll.total_gross_usd,
                "total_gross_zig": payroll.total_gross_zig,
                "total_net_usd": payroll.total_net_usd,
                "total_net_zig": payroll.total_net_zig,
                "total_paye_usd": payroll.total_paye_usd,
                "total_paye_zig": payroll.total_paye_zig,
                "total_nssa_usd": payroll.total_nssa_usd,
                "total_nssa_zig": payroll.total_nssa_zig,
            },
        )
        return self._to_entity(model)

    def delete(self, payroll_id: int) -> bool:
        """Delete a payroll."""
        deleted, _ = PayrollBatchModel.objects.filter(id=payroll_id).delete()
        return deleted > 0

    def _to_entity(self, model: PayrollBatchModel) -> Payroll:
        """Convert Django model to domain entity."""
        return Payroll(
            id=model.id,
            period=PayrollPeriod(year=model.period.year, month=model.period.month),
            status=PayrollStatus(model.status),
            processed_at=model.processed_at,
            processed_by=model.processed_by,
            closed_at=model.closed_at,
            closed_by=model.closed_by,
            notes=model.notes or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
            total_employees=model.total_employees,
            total_gross_usd=model.total_gross_usd or Decimal("0"),
            total_gross_zig=model.total_gross_zig or Decimal("0"),
            total_net_usd=model.total_net_usd or Decimal("0"),
            total_net_zig=model.total_net_zig or Decimal("0"),
            total_paye_usd=model.total_paye_usd or Decimal("0"),
            total_paye_zig=model.total_paye_zig or Decimal("0"),
            total_nssa_usd=model.total_nssa_usd or Decimal("0"),
            total_nssa_zig=model.total_nssa_zig or Decimal("0"),
        )
