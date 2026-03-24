"""
Portal application services.
"""

from modules.portal.application.services.auth_service import (
    PortalAuthService,
    AuthResult,
)
from modules.portal.application.services.dashboard_service import (
    DashboardService,
    DashboardData,
)
from modules.portal.application.services.attendance_service import (
    PortalAttendanceService,
    ClockResult,
)
from modules.portal.application.services.leave_service import (
    PortalLeaveService,
    LeaveRequestResult,
)
from modules.portal.application.services.payslip_service import (
    PortalPayslipService,
)
from modules.portal.application.services.careers_service import (
    CareersService,
    ApplicationResult,
)

__all__ = [
    # Auth
    "PortalAuthService",
    "AuthResult",
    # Dashboard
    "DashboardService",
    "DashboardData",
    # Attendance
    "PortalAttendanceService",
    "ClockResult",
    # Leave
    "PortalLeaveService",
    "LeaveRequestResult",
    # Payslip
    "PortalPayslipService",
    # Careers
    "CareersService",
    "ApplicationResult",
]
