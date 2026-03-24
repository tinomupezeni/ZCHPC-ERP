"""
Leave Module.

Manages leave types, employee leave balances, and leave requests.
Provides ILeaveProvider interface for cross-module integration with payroll.
"""

from modules.leave.application import (
    ILeaveProvider,
    LeaveBalanceDTO,
    LeaveBalanceSummaryDTO,
    LeaveProvider,
    LeaveRequestDTO,
    LeaveRequestSummaryDTO,
    LeaveTypeDTO,
)
from modules.leave.domain import (
    LeaveBalance,
    LeaveEntitlement,
    LeavePeriod,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
)

__all__ = [
    # Domain
    "LeaveType",
    "LeaveBalance",
    "LeaveRequest",
    "LeaveStatus",
    "LeavePeriod",
    "LeaveEntitlement",
    # Application
    "ILeaveProvider",
    "LeaveProvider",
    "LeaveTypeDTO",
    "LeaveBalanceDTO",
    "LeaveBalanceSummaryDTO",
    "LeaveRequestDTO",
    "LeaveRequestSummaryDTO",
]
