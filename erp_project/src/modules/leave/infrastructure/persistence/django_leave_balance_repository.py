"""
Django ORM implementation of ILeaveBalanceRepository.
"""

from decimal import Decimal
from typing import Sequence

from modules.leave.infrastructure.persistence.models import LeaveBalance as LeaveBalanceModel

from modules.leave.application.interfaces import ILeaveBalanceRepository
from modules.leave.domain.entities import LeaveBalance
from modules.leave.domain.value_objects import LeaveEntitlement


class DjangoLeaveBalanceRepository(ILeaveBalanceRepository):
    """Django ORM implementation of leave balance repository."""

    def get_by_id(self, balance_id: int) -> LeaveBalance | None:
        """Get balance by ID."""
        try:
            model = LeaveBalanceModel.objects.select_related("leave_type").get(
                id=balance_id
            )
            return self._to_entity(model)
        except LeaveBalanceModel.DoesNotExist:
            return None

    def get_by_employee_and_type_and_year(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalance | None:
        """Get balance for employee, type, and year."""
        try:
            model = LeaveBalanceModel.objects.select_related("leave_type").get(
                employee_id=employee_id,
                leave_type_id=leave_type_id,
                year=year,
            )
            return self._to_entity(model)
        except LeaveBalanceModel.DoesNotExist:
            return None

    def get_by_employee_and_year(
        self,
        employee_id: int,
        year: int,
    ) -> Sequence[LeaveBalance]:
        """Get all balances for employee in a year."""
        queryset = LeaveBalanceModel.objects.select_related("leave_type").filter(
            employee_id=employee_id,
            year=year,
        )
        return [self._to_entity(model) for model in queryset]

    def get_by_employee(self, employee_id: int) -> Sequence[LeaveBalance]:
        """Get all balances for employee."""
        queryset = LeaveBalanceModel.objects.select_related("leave_type").filter(
            employee_id=employee_id
        )
        return [self._to_entity(model) for model in queryset]

    def save(self, balance: LeaveBalance) -> LeaveBalance:
        """Save balance."""
        # The existing model only has days_remaining, not entitled/used separately
        # We store the remaining days as days_remaining
        model, created = LeaveBalanceModel.objects.update_or_create(
            id=balance.id,
            defaults={
                "employee_id": balance.employee_id,
                "leave_type_id": balance.leave_type_id,
                "year": balance.year,
                "days_remaining": balance.remaining_days,
            },
        )
        return self._to_entity(model)

    def delete(self, balance_id: int) -> None:
        """Delete balance."""
        LeaveBalanceModel.objects.filter(id=balance_id).delete()

    def get_next_id(self) -> int:
        """Get next available ID."""
        last = LeaveBalanceModel.objects.order_by("-id").first()
        return (last.id + 1) if last else 1

    def _to_entity(self, model: LeaveBalanceModel) -> LeaveBalance:
        """
        Convert Django model to domain entity.

        Note: The existing model only has days_remaining, not entitled_days and used_days
        separately. We use the leave type's default_days_allowed as entitled_days
        and calculate used_days from the difference.
        """
        # Get entitled days from leave type default
        entitled_days = Decimal(str(model.leave_type.default_days_allowed))
        remaining_days = Decimal(str(model.days_remaining))

        # Calculate used days
        used_days = entitled_days - remaining_days
        if used_days < 0:
            # If remaining > entitled, set used to 0 and entitled to remaining
            entitled_days = remaining_days
            used_days = Decimal("0")

        entitlement = LeaveEntitlement(
            entitled_days=entitled_days,
            used_days=used_days,
        )

        return LeaveBalance(
            id=model.id,
            employee_id=model.employee_id,
            leave_type_id=model.leave_type_id,
            year=model.year,
            entitlement=entitlement,
        )
