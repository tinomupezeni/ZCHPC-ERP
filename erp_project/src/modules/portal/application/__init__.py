"""
Portal application layer.

Contains application services and interfaces.
"""

from modules.portal.application.interfaces import (
    # Repositories
    IExpenseClaimRepository,
    ISupportTicketRepository,
    INotificationRepository,
    IDocumentRepository,
    IDocumentCategoryRepository,
    IExpenseCategoryRepository,
    IQRTokenRepository,
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
from modules.portal.application.services import (
    PortalAuthService,
    AuthResult,
    DashboardService,
    DashboardData,
    PortalAttendanceService,
    ClockResult,
    PortalLeaveService,
    LeaveRequestResult,
    PortalPayslipService,
    CareersService,
    ApplicationResult,
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
    # Services
    "PortalAuthService",
    "AuthResult",
    "DashboardService",
    "DashboardData",
    "PortalAttendanceService",
    "ClockResult",
    "PortalLeaveService",
    "LeaveRequestResult",
    "PortalPayslipService",
    "CareersService",
    "ApplicationResult",
]
