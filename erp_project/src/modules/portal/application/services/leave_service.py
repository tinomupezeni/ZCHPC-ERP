"""
Portal leave service.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.portal.application.interfaces import (
    ILeaveProvider,
    INotificationRepository,
    LeaveBalanceDTO,
    LeaveRequestDTO,
)
from modules.portal.domain.entities import Notification


@dataclass
class LeaveRequestResult:
    """Result of leave request operation."""

    success: bool
    request: Optional[LeaveRequestDTO] = None
    message: Optional[str] = None


class PortalLeaveService:
    """
    Leave management service for employee portal.

    Handles leave balance queries and request submission.
    """

    def __init__(
        self,
        leave_provider: ILeaveProvider,
        notification_repo: INotificationRepository,
    ) -> None:
        self._leave_provider = leave_provider
        self._notification_repo = notification_repo

    def get_balances(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[LeaveBalanceDTO]:
        """
        Get leave balances for an employee.

        Args:
            employee_id: Employee ID
            year: Year (defaults to current)

        Returns:
            List of leave balances by type
        """
        if year is None:
            year = date.today().year

        return self._leave_provider.get_balances(
            employee_id=employee_id,
            year=year,
        )

    def get_requests(
        self,
        employee_id: int,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[LeaveRequestDTO]:
        """
        Get leave requests for an employee.

        Args:
            employee_id: Employee ID
            status: Optional status filter
            from_date: Optional start date filter
            to_date: Optional end date filter

        Returns:
            List of leave requests
        """
        requests = self._leave_provider.get_requests(
            employee_id=employee_id,
            status=status,
        )

        # Apply date filters if provided
        if from_date or to_date:
            filtered = []
            for req in requests:
                if from_date and req.start_date < from_date:
                    continue
                if to_date and req.end_date > to_date:
                    continue
                filtered.append(req)
            requests = filtered

        return requests

    def create_request(
        self,
        employee_id: int,
        leave_type_id: int,
        start_date: date,
        end_date: date,
        reason: Optional[str] = None,
    ) -> LeaveRequestResult:
        """
        Create a new leave request.

        Args:
            employee_id: Employee ID
            leave_type_id: Type of leave
            start_date: Start date
            end_date: End date
            reason: Optional reason

        Returns:
            LeaveRequestResult with created request
        """
        # Validate dates
        if start_date > end_date:
            return LeaveRequestResult(
                success=False,
                message="Start date cannot be after end date"
            )

        if start_date < date.today():
            return LeaveRequestResult(
                success=False,
                message="Cannot request leave for past dates"
            )

        # Check balance
        balances = self.get_balances(employee_id, start_date.year)
        type_balance = next(
            (b for b in balances if b.leave_type_id == leave_type_id),
            None
        )

        if type_balance is None:
            return LeaveRequestResult(
                success=False,
                message="Invalid leave type"
            )

        # Calculate days
        days_count = (end_date - start_date).days + 1

        if days_count > type_balance.remaining_days:
            return LeaveRequestResult(
                success=False,
                message=f"Insufficient leave balance. "
                        f"Requested: {days_count}, Available: {type_balance.remaining_days}"
            )

        try:
            request = self._leave_provider.create_request(
                employee_id=employee_id,
                leave_type_id=leave_type_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
            )
            return LeaveRequestResult(
                success=True,
                request=request,
                message="Leave request submitted successfully"
            )
        except Exception as e:
            return LeaveRequestResult(
                success=False,
                message=str(e)
            )

    def cancel_request(
        self,
        employee_id: int,
        request_id: int,
    ) -> LeaveRequestResult:
        """
        Cancel a leave request.

        Args:
            employee_id: Employee ID (for verification)
            request_id: Request ID to cancel

        Returns:
            LeaveRequestResult indicating success or failure
        """
        # Verify request belongs to employee
        requests = self.get_requests(employee_id)
        request = next((r for r in requests if r.id == request_id), None)

        if request is None:
            return LeaveRequestResult(
                success=False,
                message="Leave request not found"
            )

        if request.status not in ("Pending",):
            return LeaveRequestResult(
                success=False,
                message="Only pending requests can be cancelled"
            )

        try:
            self._leave_provider.cancel_request(request_id)
            return LeaveRequestResult(
                success=True,
                message="Leave request cancelled successfully"
            )
        except Exception as e:
            return LeaveRequestResult(
                success=False,
                message=str(e)
            )

    def get_calendar(
        self,
        employee_id: int,
        year: int,
        month: int,
    ) -> List[dict]:
        """
        Get leave requests in calendar format.

        Returns:
            List of calendar events
        """
        # Get requests for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        requests = self.get_requests(
            employee_id=employee_id,
            from_date=start_date,
            to_date=end_date,
        )

        # Convert to calendar events
        events = []
        for req in requests:
            events.append({
                "id": req.id,
                "title": req.leave_type_name,
                "start": req.start_date.isoformat(),
                "end": req.end_date.isoformat(),
                "status": req.status,
                "days": req.days_count,
            })

        return events

    def get_summary(
        self,
        employee_id: int,
    ) -> dict:
        """
        Get leave summary statistics.

        Returns:
            Dict with summary statistics
        """
        current_year = date.today().year
        balances = self.get_balances(employee_id, current_year)
        requests = self.get_requests(employee_id)

        # Count by status
        pending = sum(1 for r in requests if r.status == "Pending")
        approved = sum(1 for r in requests if r.status == "Approved")
        rejected = sum(1 for r in requests if r.status == "Rejected")

        # Total days
        total_entitled = sum(b.entitled_days for b in balances)
        total_used = sum(b.used_days for b in balances)
        total_remaining = sum(b.remaining_days for b in balances)

        return {
            "total_entitled": total_entitled,
            "total_used": total_used,
            "total_remaining": total_remaining,
            "pending_requests": pending,
            "approved_requests": approved,
            "rejected_requests": rejected,
            "balances": [
                {
                    "type": b.leave_type_name,
                    "entitled": b.entitled_days,
                    "used": b.used_days,
                    "pending": b.pending_days,
                    "remaining": b.remaining_days,
                }
                for b in balances
            ],
        }
