"""
Application layer interfaces for the portal module.
"""

from modules.portal.application.interfaces.repositories import (
    IExpenseClaimRepository,
    ISupportTicketRepository,
    INotificationRepository,
    IDocumentRepository,
    IDocumentCategoryRepository,
    IExpenseCategoryRepository,
    IQRTokenRepository,
)
from modules.portal.application.interfaces.providers import (
    # DTOs
    EmployeeDTO,
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
    LeaveBalanceDTO,
    LeaveRequestDTO,
    PayslipDTO,
    JobDTO,
    CompanyEventDTO,
    # Providers
    IEmployeeProvider,
    IAttendanceProvider,
    ILeaveProvider,
    IPayrollProvider,
    IRecruitmentProvider,
    IEventProvider,
)

__all__ = [
    # Repositories
    "IExpenseClaimRepository",
    "ISupportTicketRepository",
    "INotificationRepository",
    "IDocumentRepository",
    "IDocumentCategoryRepository",
    "IExpenseCategoryRepository",
    "IQRTokenRepository",
    # DTOs
    "EmployeeDTO",
    "AttendanceRecordDTO",
    "AttendanceSummaryDTO",
    "LeaveBalanceDTO",
    "LeaveRequestDTO",
    "PayslipDTO",
    "JobDTO",
    "CompanyEventDTO",
    # Providers
    "IEmployeeProvider",
    "IAttendanceProvider",
    "ILeaveProvider",
    "IPayrollProvider",
    "IRecruitmentProvider",
    "IEventProvider",
]
