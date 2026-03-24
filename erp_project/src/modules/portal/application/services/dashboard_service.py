"""
Portal dashboard service.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional

from modules.portal.application.interfaces import (
    IEmployeeProvider,
    IAttendanceProvider,
    ILeaveProvider,
    IEventProvider,
    INotificationRepository,
    EmployeeDTO,
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
    LeaveBalanceDTO,
    CompanyEventDTO,
)


@dataclass
class DashboardData:
    """Data for employee dashboard."""

    # Employee info
    employee_id: str
    employee_name: str
    department_name: Optional[str]
    position_name: Optional[str]

    # Leave summary
    leave_balances: List[LeaveBalanceDTO]

    # Attendance
    today_clock_status: Optional[AttendanceRecordDTO]
    monthly_attendance_count: int
    recent_attendance: List[AttendanceRecordDTO]

    # Counts
    pending_leave_requests: int
    pending_expense_claims: int
    open_tickets: int
    unread_notifications: int

    # Events
    upcoming_events: List[CompanyEventDTO]


class DashboardService:
    """
    Service for aggregating employee dashboard data.

    Combines data from multiple modules into a unified dashboard view.
    """

    def __init__(
        self,
        employee_provider: IEmployeeProvider,
        attendance_provider: IAttendanceProvider,
        leave_provider: ILeaveProvider,
        event_provider: IEventProvider,
        notification_repo: INotificationRepository,
    ) -> None:
        self._employee_provider = employee_provider
        self._attendance_provider = attendance_provider
        self._leave_provider = leave_provider
        self._event_provider = event_provider
        self._notification_repo = notification_repo

    def get_dashboard(
        self,
        employee_internal_id: int,
    ) -> DashboardData:
        """
        Get aggregated dashboard data for an employee.

        Args:
            employee_internal_id: Internal employee ID

        Returns:
            DashboardData with aggregated information
        """
        # Get employee info
        employee = self._employee_provider.get_by_id(employee_internal_id)
        if employee is None:
            raise ValueError(f"Employee {employee_internal_id} not found")

        # Get leave balances
        current_year = date.today().year
        leave_balances = self._leave_provider.get_balances(
            employee_id=employee_internal_id,
            year=current_year,
        )

        # Get today's attendance status
        today_status = self._attendance_provider.get_today_status(
            employee_id=employee_internal_id,
        )

        # Get this month's attendance count
        today = date.today()
        month_start = today.replace(day=1)
        monthly_summary = self._attendance_provider.get_monthly_summary(
            employee_id=employee_internal_id,
            year=today.year,
            month=today.month,
        )

        # Get last 7 days attendance
        week_ago = today - timedelta(days=7)
        recent_attendance = self._attendance_provider.get_history(
            employee_id=employee_internal_id,
            from_date=week_ago,
            to_date=today,
        )

        # Get pending counts
        pending_leave = self._count_pending_leave(employee_internal_id)

        # Get unread notifications
        unread_count = self._notification_repo.get_unread_count(
            employee_id=employee_internal_id,
        )

        # Get upcoming events
        upcoming_events = self._event_provider.get_upcoming_events(days=30)

        return DashboardData(
            employee_id=employee.employee_id,
            employee_name=f"{employee.first_name} {employee.surname}",
            department_name=employee.department_name,
            position_name=employee.position_name,
            leave_balances=leave_balances,
            today_clock_status=today_status,
            monthly_attendance_count=monthly_summary.present_days,
            recent_attendance=recent_attendance,
            pending_leave_requests=pending_leave,
            pending_expense_claims=0,  # Will be populated from expense repo
            open_tickets=0,  # Will be populated from ticket repo
            unread_notifications=unread_count,
            upcoming_events=upcoming_events,
        )

    def _count_pending_leave(self, employee_id: int) -> int:
        """Count pending leave requests."""
        requests = self._leave_provider.get_requests(
            employee_id=employee_id,
            status="Pending",
        )
        return len(requests)

    def get_quick_stats(
        self,
        employee_internal_id: int,
    ) -> dict:
        """
        Get quick statistics for dashboard widgets.

        Returns:
            Dict with key statistics
        """
        today = date.today()

        # Get today's status
        today_status = self._attendance_provider.get_today_status(
            employee_id=employee_internal_id,
        )

        # Get this month's summary
        monthly_summary = self._attendance_provider.get_monthly_summary(
            employee_id=employee_internal_id,
            year=today.year,
            month=today.month,
        )

        # Get leave balances
        leave_balances = self._leave_provider.get_balances(
            employee_id=employee_internal_id,
            year=today.year,
        )
        total_leave_remaining = sum(
            lb.remaining_days for lb in leave_balances
        )

        return {
            "is_clocked_in": today_status is not None and today_status.time_out is None,
            "clock_in_time": (
                today_status.time_in.isoformat()
                if today_status and today_status.time_in
                else None
            ),
            "days_present_this_month": monthly_summary.present_days,
            "hours_worked_this_month": monthly_summary.total_hours,
            "total_leave_remaining": total_leave_remaining,
        }
