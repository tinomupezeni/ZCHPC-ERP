"""
Django implementations of portal providers.

These providers integrate with existing Django models from other modules.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.contrib.auth import authenticate
from django.db.models import Sum

from modules.portal.application.interfaces import (
    IEmployeeProvider,
    IAttendanceProvider,
    ILeaveProvider,
    IPayrollProvider,
    IRecruitmentProvider,
    IEventProvider,
    EmployeeDTO,
    AttendanceRecordDTO,
    AttendanceSummaryDTO,
    LeaveBalanceDTO,
    LeaveRequestDTO,
    PayslipDTO,
    JobDTO,
    CompanyEventDTO,
)


class DjangoEmployeeProvider(IEmployeeProvider):
    """Provider for employee data from HR module."""

    def _to_dto(self, employee) -> EmployeeDTO:
        """Convert Django model to DTO."""
        # Reverse OneToOne raises RelatedObjectDoesNotExist (an AttributeError
        # subclass) when absent, so getattr(..., None) is the safe accessor.
        employment_details = getattr(employee, "employment_details", None)
        return EmployeeDTO(
            id=employee.id,
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            surname=employee.surname,
            email=employee.email,
            phone=employee.phone,
            department_id=employment_details.department_id if employment_details else None,
            department_name=(
                employment_details.department.name
                if employment_details and employment_details.department else None
            ),
            position_id=employment_details.position_id if employment_details else None,
            position_name=(
                employment_details.position.title
                if employment_details and employment_details.position else None
            ),
            is_active=employee.is_active,
            user_id=employee.user_id,
        )

    def get_by_id(self, employee_id: int) -> Optional[EmployeeDTO]:
        from modules.hr.infrastructure.persistence.models import Employees
        try:
            employee = Employees.objects.select_related(
                "employment_details__department", "employment_details__position"
            ).get(pk=employee_id)
            return self._to_dto(employee)
        except Employees.DoesNotExist:
            return None

    def get_by_ec_number(self, ec_number: str) -> Optional[EmployeeDTO]:
        from modules.hr.infrastructure.persistence.models import Employees
        try:
            employee = Employees.objects.select_related(
                "employment_details__department", "employment_details__position"
            ).get(employee_id=ec_number)
            return self._to_dto(employee)
        except Employees.DoesNotExist:
            return None

    def get_by_user_id(self, user_id: int) -> Optional[EmployeeDTO]:
        from modules.hr.infrastructure.persistence.models import Employees
        try:
            employee = Employees.objects.select_related(
                "employment_details__department", "employment_details__position"
            ).get(user_id=user_id)
            return self._to_dto(employee)
        except Employees.DoesNotExist:
            return None

    def authenticate(
        self,
        ec_number: str,
        password: str,
    ) -> Optional[EmployeeDTO]:
        from modules.hr.infrastructure.persistence.models import Employees

        # Get employee by EC number
        try:
            employee = Employees.objects.select_related(
                "employment_details__department", "employment_details__position", "user"
            ).get(employee_id=ec_number)
        except Employees.DoesNotExist:
            return None

        # Check if has linked user
        if not employee.user:
            return None

        # Authenticate user
        user = authenticate(
            email=employee.user.email,
            password=password,
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        if not employee.is_active:
            return None

        return self._to_dto(employee)


class DjangoAttendanceProvider(IAttendanceProvider):
    """Provider for attendance data from Attendance module."""

    def _to_dto(self, record) -> AttendanceRecordDTO:
        return AttendanceRecordDTO(
            id=record.id,
            employee_id=record.employee_id,
            date=record.date,
            time_in=record.time_in,
            time_out=record.time_out,
            status=record.status if hasattr(record, "status") else "Present",
        )

    def get_today_status(
        self,
        employee_id: int,
    ) -> Optional[AttendanceRecordDTO]:
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        try:
            record = AttendanceRecord.objects.get(
                employee_id=employee_id,
                date=date.today(),
            )
            return self._to_dto(record)
        except AttendanceRecord.DoesNotExist:
            return None

    def get_history(
        self,
        employee_id: int,
        from_date: date,
        to_date: date,
    ) -> List[AttendanceRecordDTO]:
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(
            employee_id=employee_id,
            date__gte=from_date,
            date__lte=to_date,
        ).order_by("-date")
        return [self._to_dto(r) for r in records]

    def get_monthly_summary(
        self,
        employee_id: int,
        year: int,
        month: int,
    ) -> AttendanceSummaryDTO:
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        import calendar

        # Get total working days in month
        _, num_days = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        records = AttendanceRecord.objects.filter(
            employee_id=employee_id,
            date__gte=start_date,
            date__lte=end_date,
        )

        present_days = records.filter(time_in__isnull=False).count()

        # Calculate total hours
        total_hours = 0.0
        for record in records:
            if record.time_in and record.time_out:
                delta = record.time_out - record.time_in
                total_hours += delta.total_seconds() / 3600

        return AttendanceSummaryDTO(
            month=month,
            year=year,
            total_days=num_days,
            present_days=present_days,
            absent_days=num_days - present_days,
            leave_days=0,  # Would need to integrate with leave module
            late_days=0,
            total_hours=round(total_hours, 2),
        )

    def clock_in(self, employee_id: int) -> AttendanceRecordDTO:
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        record, _ = AttendanceRecord.objects.get_or_create(
            employee_id=employee_id,
            date=date.today(),
            defaults={"time_in": datetime.now()},
        )
        if record.time_in is None:
            record.time_in = datetime.now()
            record.save()
        return self._to_dto(record)

    def clock_out(self, employee_id: int) -> AttendanceRecordDTO:
        from modules.attendance.infrastructure.persistence.models import AttendanceRecord
        record = AttendanceRecord.objects.get(
            employee_id=employee_id,
            date=date.today(),
        )
        record.time_out = datetime.now()
        record.save()
        return self._to_dto(record)


class DjangoLeaveProvider(ILeaveProvider):
    """Provider for leave data from Leave module."""

    def get_balances(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[LeaveBalanceDTO]:
        from modules.leave.infrastructure.persistence.models import LeaveBalance, LeaveType

        if year is None:
            year = date.today().year

        balances = LeaveBalance.objects.filter(
            employee_id=employee_id,
            year=year,
        ).select_related("leave_type")

        result = []
        for balance in balances:
            # Count pending days
            from modules.leave.infrastructure.persistence.models import LeaveRequest
            pending = LeaveRequest.objects.filter(
                employee_id=employee_id,
                leave_type=balance.leave_type,
                status="Pending",
            ).aggregate(total=Sum("days_count"))["total"] or 0

            result.append(LeaveBalanceDTO(
                leave_type_id=balance.leave_type_id,
                leave_type_name=balance.leave_type.name,
                entitled_days=balance.entitled_days,
                used_days=balance.used_days,
                pending_days=pending,
                remaining_days=balance.remaining_days,
            ))

        return result

    def get_requests(
        self,
        employee_id: int,
        status: Optional[str] = None,
    ) -> List[LeaveRequestDTO]:
        from modules.leave.infrastructure.persistence.models import LeaveRequest

        queryset = LeaveRequest.objects.filter(
            employee_id=employee_id,
        ).select_related("leave_type").order_by("-created_at")

        if status:
            queryset = queryset.filter(status=status)

        return [
            LeaveRequestDTO(
                id=r.id,
                employee_id=r.employee_id,
                leave_type_id=r.leave_type_id,
                leave_type_name=r.leave_type.name,
                start_date=r.start_date,
                end_date=r.end_date,
                days_count=r.days_count,
                reason=r.reason,
                status=r.status,
                created_at=r.created_at,
            )
            for r in queryset
        ]

    def create_request(
        self,
        employee_id: int,
        leave_type_id: int,
        start_date: date,
        end_date: date,
        reason: Optional[str] = None,
    ) -> LeaveRequestDTO:
        from modules.leave.infrastructure.persistence.models import LeaveRequest

        days_count = (end_date - start_date).days + 1

        request = LeaveRequest.objects.create(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            reason=reason or "",
            status="Pending",
        )

        return LeaveRequestDTO(
            id=request.id,
            employee_id=request.employee_id,
            leave_type_id=request.leave_type_id,
            leave_type_name=request.leave_type.name,
            start_date=request.start_date,
            end_date=request.end_date,
            days_count=request.days_count,
            reason=request.reason,
            status=request.status,
            created_at=request.created_at,
        )

    def cancel_request(self, request_id: int) -> bool:
        from modules.leave.infrastructure.persistence.models import LeaveRequest
        try:
            request = LeaveRequest.objects.get(
                pk=request_id,
                status="Pending",
            )
            request.status = "Cancelled"
            request.save()
            return True
        except LeaveRequest.DoesNotExist:
            return False


class DjangoPayrollProvider(IPayrollProvider):
    """Provider for payroll data from Payroll module."""

    def _to_dto(self, payslip) -> PayslipDTO:
        return PayslipDTO(
            id=payslip.id,
            employee_id=payslip.employee_id,
            period_year=payslip.payroll.period_year,
            period_month=payslip.payroll.period_month,
            base_salary_usd=Decimal(str(payslip.base_salary_usd or 0)),
            base_salary_zig=Decimal(str(payslip.base_salary_zig or 0)),
            allowances_usd=Decimal(str(payslip.allowances_usd or 0)),
            allowances_zig=Decimal(str(payslip.allowances_zig or 0)),
            gross_usd=Decimal(str(payslip.gross_usd or 0)),
            gross_zig=Decimal(str(payslip.gross_zig or 0)),
            paye_usd=Decimal(str(payslip.paye_usd or 0)),
            paye_zig=Decimal(str(payslip.paye_zig or 0)),
            aids_levy_usd=Decimal(str(payslip.aids_levy_usd or 0)),
            aids_levy_zig=Decimal(str(payslip.aids_levy_zig or 0)),
            nssa_employee_usd=Decimal(str(payslip.nssa_employee_usd or 0)),
            nssa_employee_zig=Decimal(str(payslip.nssa_employee_zig or 0)),
            total_deductions_usd=Decimal(str(payslip.total_deductions_usd or 0)),
            total_deductions_zig=Decimal(str(payslip.total_deductions_zig or 0)),
            net_salary_usd=Decimal(str(payslip.net_salary_usd or 0)),
            net_salary_zig=Decimal(str(payslip.net_salary_zig or 0)),
            exchange_rate=Decimal(str(payslip.exchange_rate or 1)),
            status=payslip.status,
        )

    def get_payslips(
        self,
        employee_id: int,
        year: Optional[int] = None,
    ) -> List[PayslipDTO]:
        from modules.payroll.infrastructure.persistence.models import Payroll as Payslip

        queryset = Payslip.objects.filter(
            employee_id=employee_id,
        ).select_related("payroll").order_by("-payroll__period_year", "-payroll__period_month")

        if year:
            queryset = queryset.filter(payroll__period_year=year)

        return [self._to_dto(p) for p in queryset]

    def get_payslip(
        self,
        payslip_id: int,
    ) -> Optional[PayslipDTO]:
        from modules.payroll.infrastructure.persistence.models import Payroll as Payslip
        try:
            payslip = Payslip.objects.select_related("payroll").get(pk=payslip_id)
            return self._to_dto(payslip)
        except Payslip.DoesNotExist:
            return None


class DjangoRecruitmentProvider(IRecruitmentProvider):
    """Provider for recruitment data."""

    def get_open_jobs(self) -> List[JobDTO]:
        from modules.recruitment.infrastructure.persistence.models import Job

        jobs = Job.objects.filter(
            status="Open",
        ).select_related("department")

        return [
            JobDTO(
                id=j.id,
                title=j.title,
                department_name=j.department.name if j.department else None,
                location=j.location,
                salary_usd_min=Decimal(str(j.salary_usd_min or 0)),
                salary_usd_max=Decimal(str(j.salary_usd_max or 0)),
                description=j.description or "",
                qualifications=j.qualifications or "",
                posted_date=j.posted_date,
                status=j.status,
            )
            for j in jobs
        ]

    def get_job(self, job_id: int) -> Optional[JobDTO]:
        from modules.recruitment.infrastructure.persistence.models import Job
        try:
            j = Job.objects.select_related("department").get(pk=job_id)
            return JobDTO(
                id=j.id,
                title=j.title,
                department_name=j.department.name if j.department else None,
                location=j.location,
                salary_usd_min=Decimal(str(j.salary_usd_min or 0)),
                salary_usd_max=Decimal(str(j.salary_usd_max or 0)),
                description=j.description or "",
                qualifications=j.qualifications or "",
                posted_date=j.posted_date,
                status=j.status,
            )
        except Job.DoesNotExist:
            return None

    def apply_for_job(
        self,
        job_id: int,
        candidate_data: dict,
    ) -> int:
        from modules.recruitment.infrastructure.persistence.models import Candidate, JobApplication
        from django.db import transaction

        with transaction.atomic():
            # Get or create candidate
            candidate, _ = Candidate.objects.update_or_create(
                national_id=candidate_data["national_id"],
                defaults={
                    "first_name": candidate_data["first_name"],
                    "last_name": candidate_data["last_name"],
                    "email": candidate_data["email"],
                    "phone": candidate_data["phone"],
                    "date_of_birth": candidate_data.get("date_of_birth"),
                    "qualifications": candidate_data.get("qualifications", ""),
                    "experience": candidate_data.get("experience", ""),
                },
            )

            # Check if already applied
            if JobApplication.objects.filter(
                job_id=job_id,
                candidate=candidate,
            ).exists():
                raise ValueError("You have already applied for this position")

            # Create application
            application = JobApplication.objects.create(
                job_id=job_id,
                candidate=candidate,
                cover_letter=candidate_data.get("cover_letter", ""),
                status="Pending",
            )

            return application.id

    def check_application_status(
        self,
        national_id: str,
    ) -> List[dict]:
        from modules.recruitment.infrastructure.persistence.models import Candidate, JobApplication

        try:
            candidate = Candidate.objects.get(national_id=national_id)
        except Candidate.DoesNotExist:
            return []

        applications = JobApplication.objects.filter(
            candidate=candidate,
        ).select_related("job")

        return [
            {
                "job_id": app.job_id,
                "job_title": app.job.title,
                "applied_at": app.applied_at.isoformat(),
                "status": app.status,
            }
            for app in applications
        ]


class DjangoEventProvider(IEventProvider):
    """Provider for company events."""

    def get_upcoming_events(self, days: int = 30) -> List[CompanyEventDTO]:
        from modules.leave.infrastructure.persistence.models import CompanyEvent

        today = date.today()
        end_date = today + timedelta(days=days)

        events = CompanyEvent.objects.filter(
            event_date__gte=today,
            event_date__lte=end_date,
        ).order_by("event_date")

        return [
            CompanyEventDTO(
                id=e.id,
                title=e.title,
                description=e.description,
                event_date=e.event_date,
                event_type=e.event_type if hasattr(e, "event_type") else "General",
            )
            for e in events
        ]
