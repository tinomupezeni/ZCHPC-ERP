"""
Leave balance application service.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from shared.domain.exceptions import NotFoundError, ValidationError

from modules.leave.application.interfaces import (
    ILeaveBalanceRepository,
    ILeaveRequestRepository,
    ILeaveTypeRepository,
    LeaveBalanceDTO,
    LeaveBalanceSummaryDTO,
)
from modules.leave.domain.entities import LeaveBalance
from modules.leave.domain.events import LeaveBalanceAdjusted
from modules.leave.domain.services import ILeaveBalanceCalculator
from modules.leave.domain.value_objects import LeaveEntitlement, LeaveStatus


@dataclass
class CreateLeaveBalanceCommand:
    """Command to create a leave balance."""

    employee_id: int
    leave_type_id: int
    year: int
    entitled_days: Decimal


@dataclass
class AdjustLeaveBalanceCommand:
    """Command to adjust a leave balance."""

    balance_id: int
    adjustment_days: Decimal
    reason: str
    adjusted_by_id: int


@dataclass
class SetLeaveEntitlementCommand:
    """Command to set leave entitlement."""

    employee_id: int
    leave_type_id: int
    year: int
    entitled_days: Decimal


class LeaveBalanceService:
    """
    Application service for leave balance operations.

    Handles use cases related to leave balances.
    """

    def __init__(
        self,
        balance_repository: ILeaveBalanceRepository,
        leave_type_repository: ILeaveTypeRepository,
        request_repository: ILeaveRequestRepository,
        balance_calculator: ILeaveBalanceCalculator,
    ) -> None:
        self._balance_repository = balance_repository
        self._leave_type_repository = leave_type_repository
        self._request_repository = request_repository
        self._balance_calculator = balance_calculator

    def create_or_update_balance(
        self, command: SetLeaveEntitlementCommand
    ) -> LeaveBalanceDTO:
        """Create or update leave balance for an employee."""
        # Verify leave type exists
        leave_type = self._leave_type_repository.get_by_id(command.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {command.leave_type_id} not found")

        # Check for existing balance
        existing = self._balance_repository.get_by_employee_and_type_and_year(
            employee_id=command.employee_id,
            leave_type_id=command.leave_type_id,
            year=command.year,
        )

        if existing:
            # Update existing balance
            existing.adjust_entitlement(command.entitled_days)
            saved = self._balance_repository.save(existing)
        else:
            # Create new balance
            entitlement = LeaveEntitlement(
                entitled_days=command.entitled_days,
                used_days=Decimal("0"),
            )
            balance = LeaveBalance(
                id=self._balance_repository.get_next_id(),
                employee_id=command.employee_id,
                leave_type_id=command.leave_type_id,
                year=command.year,
                entitlement=entitlement,
            )
            saved = self._balance_repository.save(balance)

        return self._to_dto(saved, leave_type.name)

    def adjust_balance(self, command: AdjustLeaveBalanceCommand) -> LeaveBalanceDTO:
        """Adjust a leave balance (add or subtract days)."""
        balance = self._balance_repository.get_by_id(command.balance_id)
        if not balance:
            raise NotFoundError(f"Leave balance with ID {command.balance_id} not found")

        # Get leave type name
        leave_type = self._leave_type_repository.get_by_id(balance.leave_type_id)
        if not leave_type:
            raise NotFoundError(f"Leave type with ID {balance.leave_type_id} not found")

        old_entitled = balance.entitled_days
        balance.adjust_entitlement(balance.entitled_days + command.adjustment_days)

        # Add domain event
        balance.add_domain_event(
            LeaveBalanceAdjusted(
                balance_id=balance.id,
                employee_id=balance.employee_id,
                leave_type_id=balance.leave_type_id,
                old_entitled_days=old_entitled,
                new_entitled_days=balance.entitled_days,
                adjustment_reason=command.reason,
                adjusted_by_id=command.adjusted_by_id,
                adjusted_at=datetime.now(),
            )
        )

        saved = self._balance_repository.save(balance)
        return self._to_dto(saved, leave_type.name)

    def get_balance(
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
        return self._to_dto(balance, leave_type_name)

    def get_all_balances(
        self,
        employee_id: int,
        year: int,
    ) -> LeaveBalanceSummaryDTO:
        """Get all leave balances for an employee in a year."""
        balances = self._balance_repository.get_by_employee_and_year(
            employee_id=employee_id,
            year=year,
        )

        # Get leave type names
        leave_types = {lt.id: lt.name for lt in self._leave_type_repository.get_all()}

        balance_dtos = []
        total_entitled = Decimal("0")
        total_used = Decimal("0")
        total_remaining = Decimal("0")

        for balance in balances:
            leave_type_name = leave_types.get(balance.leave_type_id, "Unknown")
            dto = self._to_dto(balance, leave_type_name)
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

    def get_available_days(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> Decimal:
        """Get available days considering pending requests."""
        balance = self._balance_repository.get_by_employee_and_type_and_year(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
        )
        if not balance:
            return Decimal("0")

        # Get pending requests
        pending_requests = self._request_repository.get_by_employee(
            employee_id=employee_id,
            year=year,
            status=LeaveStatus.PENDING,
        )

        return self._balance_calculator.calculate_available_days(
            balance=balance,
            pending_requests=pending_requests,
        )

    def initialize_balances_for_employee(
        self,
        employee_id: int,
        year: int,
    ) -> Sequence[LeaveBalanceDTO]:
        """Initialize all leave balances for an employee using default days."""
        leave_types = self._leave_type_repository.get_all(include_inactive=False)
        results = []

        for leave_type in leave_types:
            # Check if balance already exists
            existing = self._balance_repository.get_by_employee_and_type_and_year(
                employee_id=employee_id,
                leave_type_id=leave_type.id,
                year=year,
            )
            if existing:
                results.append(self._to_dto(existing, leave_type.name))
                continue

            # Create with default days
            entitlement = LeaveEntitlement(
                entitled_days=Decimal(str(leave_type.default_days_allowed)),
                used_days=Decimal("0"),
            )
            balance = LeaveBalance(
                id=self._balance_repository.get_next_id(),
                employee_id=employee_id,
                leave_type_id=leave_type.id,
                year=year,
                entitlement=entitlement,
            )
            saved = self._balance_repository.save(balance)
            results.append(self._to_dto(saved, leave_type.name))

        return results

    def _to_dto(self, balance: LeaveBalance, leave_type_name: str) -> LeaveBalanceDTO:
        """Convert entity to DTO."""
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
