"""
Leave application interfaces.
"""

from modules.leave.application.interfaces.providers import (
    ILeaveProvider,
    LeaveBalanceDTO,
    LeaveBalanceSummaryDTO,
    LeaveRequestDTO,
    LeaveRequestSummaryDTO,
    LeaveTypeDTO,
)
from modules.leave.application.interfaces.repositories import (
    ILeaveBalanceRepository,
    ILeaveRequestRepository,
    ILeaveTypeRepository,
)

__all__ = [
    "ILeaveTypeRepository",
    "ILeaveBalanceRepository",
    "ILeaveRequestRepository",
    "ILeaveProvider",
    "LeaveTypeDTO",
    "LeaveBalanceDTO",
    "LeaveBalanceSummaryDTO",
    "LeaveRequestDTO",
    "LeaveRequestSummaryDTO",
]
