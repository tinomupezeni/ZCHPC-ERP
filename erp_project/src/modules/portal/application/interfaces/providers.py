"""
Provider interfaces for integrating with other modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional


# ============================
# DTOs for Provider Responses
# ============================

@dataclass
class EmployeeDTO:
    """Employee data from HR module."""

    id: int
    employee_id: str  # EC number like EMP0001
    first_name: str
    surname: str
    email: Optional[str]
    phone: Optional[str]
    department_id: Optional[int]
    department_name: Optional[str]
    position_id: Optional[int]
    position_name: Optional[str]
    is_active: bool
    user_id: Optional[int]


@dataclass
class AttendanceRecordDTO:
    """Attendance record from Attendance module."""

    id: int
    employee_id: int
    date: date
    time_in: Optional[datetime]
    time_out: Optional[datetime]
    status: str  # Present, Absent, Late, etc.


@dataclass
class AttendanceSummaryDTO:
    """Monthly attendance summary."""

    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    leave_days: int
    late_days: int
    total_hours: float


@dataclass
class LeaveBalanceDTO:
    """Leave balance from Leave module."""

    leave_type_id: int
    leave_type_name: str
    entitled_days: int
    used_days: int
    pending_days: int
    remaining_days: int


@dataclass
class LeaveRequestDTO:
    """Leave request from Leave module."""

    id: int
    employee_id: int
    leave_type_id: int
    leave_type_name: str
    start_date: date
    end_date: date
    days_count: int
    reason: Optional[str]
    status: str
    created_at: datetime


@dataclass
class PayslipDTO:
    """Payslip data from Payroll module."""

    id: int
    employee_id: int
    period_year: int
    period_month: int
    base_salary_usd: Decimal
    base_salary_zig: Decimal
    allowances_usd: Decimal
    allowances_zig: Decimal
    gross_usd: Decimal
    gross_zig: Decimal
    paye_usd: Decimal
    paye_zig: Decimal
    aids_levy_usd: Decimal
    aids_levy_zig: Decimal
    nssa_employee_usd: Decimal
    nssa_employee_zig: Decimal
    total_deductions_usd: Decimal
    total_deductions_zig: Decimal
    net_salary_usd: Decimal
    net_salary_zig: Decimal
    exchange_rate: Decimal
    status: str


@dataclass
class JobDTO:
    """Job posting from Recruitment module."""

    id: int
    title: str
    department_name: Optional[str]
    location: Optional[str]
    salary_usd_min: Optional[Decimal]
    salary_usd_max: Optional[Decimal]
    description: str
    qualifications: str
    posted_date: Optional[date]
    status: str


@dataclass
class CompanyEventDTO:
    """Company event from HR module."""

    id: int
    title: str
    description: Optional[str]
    event_date: date
    event_type: str


# ============================
# Provider Interfaces
# ============================

class IEmployeeProvider(ABC):
    """Interface for getting employee data from HR module."""

    @abstractmethod
    def get_by_id(self, employee_id: int) -> Optional[EmployeeDTO]:
        """Get employee by internal ID."""
        ...

    @abstractmethod
    def get_by_ec_number(self, ec_number: str) -> Optional[EmployeeDTO]:
        """Get employee by EC number (employee_id field)."""
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[EmployeeDTO]:
        """Get employee by Django user ID."""
        ...

    @abstractmethod
    def authenticate(
        self,
        ec_number: str,
        password: str,
    ) -> Optional[EmployeeDTO]:
        """Authenticate employee by EC number and password."""
        ...


class IAttendanceProvider(ABC):
    """Interface for attendance data from Attendance module."""

    @abstractmethod
    def get_today_status(
        self,
        employee_id: int,
    ) -> Optional[AttendanceRecordDTO]:
        """Get today's attendance status for employee."""
        ...

    @abstractmethod
    def get_history(
        self,
        employee_id: int,
        from_date: date,
        to_date: date,
    ) -> List[AttendanceRecordDTO]:
        """Get attendance history for date range."""
        ...

    @abstractmethod
    def get_monthly_summary(
        self,
        employee_id: int,
        year: int,
        month: int,
    ) -> AttendanceSummaryDTO:
        """Get monthly attendance summary."""
        ...

    @abstractmethod
    def clock_in(self, employee_id: int) -> AttendanceRecordDTO:
        """Clock in employee."""
        ...

    @abstractmethod
    def clock_out(self, employee_id: int) -> AttendanceRecordDTO:
        """Clock out employee."""
        ...


class ILeaveProvider(ABC):
    """Interface for leave data from Leave module."""

    @abstractmethod
    def get_balances(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[LeaveBalanceDTO]:
        """Get leave balances for employee."""
        ...

    @abstractmethod
    def get_requests(
        self,
        employee_id: int,
        status: Optional[str] = None,
    ) -> List[LeaveRequestDTO]:
        """Get leave requests for employee."""
        ...

    @abstractmethod
    def create_request(
        self,
        employee_id: int,
        leave_type_id: int,
        start_date: date,
        end_date: date,
        reason: Optional[str] = None,
    ) -> LeaveRequestDTO:
        """Create a new leave request."""
        ...

    @abstractmethod
    def cancel_request(self, request_id: int) -> bool:
        """Cancel a leave request."""
        ...


class IPayrollProvider(ABC):
    """Interface for payroll data from Payroll module."""

    @abstractmethod
    def get_payslips(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[PayslipDTO]:
        """Get payslips for employee."""
        ...

    @abstractmethod
    def get_payslip(
        self,
        payslip_id: int,
    ) -> Optional[PayslipDTO]:
        """Get a specific payslip."""
        ...


class IRecruitmentProvider(ABC):
    """Interface for recruitment data from Recruitment module."""

    @abstractmethod
    def get_open_jobs(self) -> List[JobDTO]:
        """Get all open job postings."""
        ...

    @abstractmethod
    def get_job(self, job_id: int) -> Optional[JobDTO]:
        """Get a specific job posting."""
        ...

    @abstractmethod
    def apply_for_job(
        self,
        job_id: int,
        candidate_data: dict,
    ) -> int:
        """Apply for a job. Returns application ID."""
        ...

    @abstractmethod
    def check_application_status(
        self,
        national_id: str,
    ) -> List[dict]:
        """Check application status by national ID."""
        ...


class IEventProvider(ABC):
    """Interface for company events from HR module."""

    @abstractmethod
    def get_upcoming_events(self, days: int = 30) -> List[CompanyEventDTO]:
        """Get upcoming company events."""
        ...
