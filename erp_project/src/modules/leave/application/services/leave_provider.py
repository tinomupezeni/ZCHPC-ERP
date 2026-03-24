"""
Leave provider implementation.

Provides leave data to other modules (e.g., payroll).
"""

from datetime import date
from typing import Sequence

from modules.leave.application.interfaces import (
    ILeaveBalanceRepository,
    ILeaveProvider,
    ILeaveRequestRepository,
    ILeaveTypeRepository,
    LeaveBalanceDTO,
    LeaveBalanceSummaryDTO,
    LeaveRequestDTO,
)
from modules.leave.domain.value_objects import LeaveStatus


class LeaveProvider(ILeaveProvider):
    """
    Implementation of ILeaveProvider.

    Used by payroll module for calculating leave-related data.
    """

    def __init__(
        self,
        balance_repository: ILeaveBalanceRepository,
        request_repository: ILeaveRequestRepository,
        leave_type_repository: ILeaveTypeRepository,
    ) -> None:
        self._balance_repository = balance_repository
        self._request_repository = request_repository
        self._leave_type_repository = leave_type_repository

    def get_leave_balance(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalanceDTO | None:
        """Get leave balance for employee, type, and year."""
        balance = self._balance_repository.get_by_employee_and_type_and_year(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
        )
        if not balance:
            return None

        leave_type = self._leave_type_repository.get_by_id(leave_type_id)
        leave_type_name = leave_type.name if leave_type else "Unknown"

        return LeaveBalanceDTO(
            id=balance.id,
            employee_id=balance.employee_id,
            leave_type_id=balance.leave_type_id,
            leave_type_name=leave_type_name,
            year=balance.year,
            entitled_days=balance.entitled_days,
            used_days=balance.used_days,
            remaining_days=balance.remaining_days,
            usage_percentage=balance.usage_percentage,
        )

    def get_all_balances(
        self,
        employee_id: int,
        year: int,
    ) -> LeaveBalanceSummaryDTO:
        """Get all leave balances for employee in a year."""
        balances = self._balance_repository.get_by_employee_and_year(
            employee_id=employee_id,
            year=year,
        )

        # Get leave type names
        leave_types = {lt.id: lt.name for lt in self._leave_type_repository.get_all()}

        from decimal import Decimal

        balance_dtos = []
        total_entitled = Decimal("0")
        total_used = Decimal("0")
        total_remaining = Decimal("0")

        for balance in balances:
            leave_type_name = leave_types.get(balance.leave_type_id, "Unknown")
            dto = LeaveBalanceDTO(
                id=balance.id,
                employee_id=balance.employee_id,
                leave_type_id=balance.leave_type_id,
                leave_type_name=leave_type_name,
                year=balance.year,
                entitled_days=balance.entitled_days,
                used_days=balance.used_days,
                remaining_days=balance.remaining_days,
                usage_percentage=balance.usage_percentage,
            )
            balance_dtos.append(dto)
            total_entitled += balance.entitled_days
            total_used += balance.used_days
            total_remaining += balance.remaining_days

        return LeaveBalanceSummaryDTO(
            employee_id=employee_id,
            year=year,
            total_entitled=total_entitled,
            total_used=total_used,
            total_remaining=total_remaining,
            balances=balance_dtos,
        )

    def get_leave_days_in_period(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """Get total approved leave days in a period."""
        requests = self._request_repository.get_approved_requests_in_period(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_days = 0
        for request in requests:
            # Calculate overlapping days
            overlap_start = max(request.start_date, start_date)
            overlap_end = min(request.end_date, end_date)
            if overlap_start <= overlap_end:
                total_days += (overlap_end - overlap_start).days + 1

        return total_days

    def get_approved_leaves(
        self,
        employee_id: int,
        start_date: date,
        end_date: date,
    ) -> Sequence[LeaveRequestDTO]:
        """Get approved leave requests in a period."""
        requests = self._request_repository.get_approved_requests_in_period(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Get leave type names
        leave_types = {lt.id: lt.name for lt in self._leave_type_repository.get_all()}

        return [
            LeaveRequestDTO(
                id=r.id,
                employee_id=r.employee_id,
                leave_type_id=r.leave_type_id,
                leave_type_name=leave_types.get(r.leave_type_id, "Unknown"),
                start_date=r.start_date,
                end_date=r.end_date,
                days=r.days,
                reason=r.reason,
                status=r.status.value,
                can_cancel=r.can_cancel,
                requested_at=r.requested_at.isoformat() if r.requested_at else "",
                reviewed_by_id=r.reviewed_by_id,
                reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None,
            )
            for r in requests
        ]

    def is_on_leave(
        self,
        employee_id: int,
        check_date: date,
    ) -> bool:
        """Check if employee is on approved leave on a specific date."""
        requests = self._request_repository.get_approved_requests_in_period(
            employee_id=employee_id,
            start_date=check_date,
            end_date=check_date,
        )
        return len(requests) > 0
