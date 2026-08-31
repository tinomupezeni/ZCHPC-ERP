"""
Employee application service.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.db import transaction

from shared.domain.exceptions import ValidationError, NotFoundError
from shared.domain.value_objects import Email, NationalId, PhoneNumber, EmployeeId
from shared.infrastructure import EventBus

from modules.hr.application.interfaces import (
    IEmployeeRepository,
    IDepartmentRepository,
    IPositionRepository,
    EmployeeDTO,
    SalaryDTO,
)
from modules.hr.domain.entities import Employee
from modules.hr.domain.value_objects import (
    EmergencyContact,
    EmploymentType,
    Gender,
    MaritalStatus,
)
from modules.hr.domain.events import (
    EmployeeHiredEvent,
    EmployeeTerminatedEvent,
    EmployeeUpdatedEvent,
    SalaryChangedEvent,
)
from modules.hr.domain.services import SequentialEmployeeIdGenerator


@dataclass
class CreateEmployeeCommand:
    """Command to create a new employee."""

    first_name: str
    surname: str
    employee_id: str | None = None  # Optional custom EC number
    email: str | None = None
    phone: str | None = None
    national_id: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    marital_status: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    role_id: int | None = None
    employee_type: str = "Full-time"
    reports_to_id: int | None = None
    date_joined: date | None = None
    contract_from: date | None = None
    contract_to: date | None = None
    leave_days_entitled: int = 22
    usd_salary: Decimal | None = None
    zig_salary: Decimal | None = None
    pay_frequency: str = "Monthly"
    bank_name: str | None = None
    bank_account: str | None = None
    nssa_number: str | None = None
    zimra_number: str | None = None
    paye_number: str | None = None
    pays_aids_levy: bool = True
    pension_fund: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None
    emergency_contact_relationship: str | None = None
    deductions_data: list | None = None  # List of deduction assignments
    user_id: UUID | None = None


@dataclass
class UpdateEmployeeCommand:
    """Command to update an employee."""

    employee_id: int
    first_name: str | None = None
    surname: str | None = None
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    marital_status: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    role_id: int | None = None
    employee_type: str | None = None
    reports_to_id: int | None = None
    contract_from: date | None = None
    contract_to: date | None = None
    leave_days_entitled: int | None = None
    usd_salary: Decimal | None = None
    zig_salary: Decimal | None = None
    pay_frequency: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    nssa_number: str | None = None
    zimra_number: str | None = None
    paye_number: str | None = None
    pays_aids_levy: bool | None = None
    pension_fund: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_number: str | None = None
    emergency_contact_relationship: str | None = None


class EmployeeService:
    """
    Application service for employee operations.
    """

    def __init__(
        self,
        employee_repository: IEmployeeRepository,
        department_repository: IDepartmentRepository,
        position_repository: IPositionRepository,
        event_bus: EventBus | None = None,
    ):
        """Initialize service with repositories."""
        self._employees = employee_repository
        self._departments = department_repository
        self._positions = position_repository
        self._event_bus = event_bus or EventBus.get_instance()

    def create_employee(self, command: CreateEmployeeCommand) -> Employee:
        """
        Create a new employee.

        Args:
            command: Create employee command

        Returns:
            Created employee

        Raises:
            ValidationError: If validation fails
        """
        # Validate email uniqueness
        if command.email and self._employees.exists_by_email(command.email):
            raise ValidationError(
                message=f"Employee with email {command.email} already exists",
                code="DUPLICATE_EMAIL",
            )

        # Validate national ID uniqueness
        if command.national_id and self._employees.exists_by_national_id(command.national_id):
            raise ValidationError(
                message=f"Employee with national ID {command.national_id} already exists",
                code="DUPLICATE_NATIONAL_ID",
            )

        # Validate department exists
        if command.department_id:
            dept = self._departments.get_by_id(command.department_id)
            if not dept:
                raise NotFoundError(f"Department with ID {command.department_id} not found")

        # Validate position exists and belongs to department
        if command.position_id:
            pos = self._positions.get_by_id(command.position_id)
            if not pos:
                raise NotFoundError(f"Position with ID {command.position_id} not found")
            if command.department_id and pos.department_id != command.department_id:
                raise ValidationError(
                    message="Position does not belong to the specified department",
                    code="POSITION_DEPARTMENT_MISMATCH",
                )

        # Use provided employee ID or generate a new one
        if command.employee_id and command.employee_id.strip():
            # Validate custom employee_id uniqueness
            if self._employees.exists_by_employee_id(command.employee_id.strip()):
                raise ValidationError(
                    message=f"Employee with EC Number {command.employee_id} already exists",
                    code="DUPLICATE_EMPLOYEE_ID",
                )
            employee_id = EmployeeId(command.employee_id.strip())
        else:
            # Auto-generate employee ID
            id_generator = SequentialEmployeeIdGenerator(self._employees.get_max_employee_id)
            employee_id = id_generator.next_id()

        # Create employee entity
        employee = Employee(
            id=0,  # Will be set by repository
            employee_id=employee_id,
            user_id=command.user_id,
            first_name=command.first_name,
            surname=command.surname,
            national_id=NationalId(command.national_id) if command.national_id else None,
            date_of_birth=command.date_of_birth,
            gender=Gender.from_string(command.gender) if command.gender else None,
            marital_status=MaritalStatus.from_string(command.marital_status) if command.marital_status else None,
            email=Email(command.email) if command.email else None,
            phone=PhoneNumber(command.phone) if command.phone else None,
            department_id=command.department_id,
            position_id=command.position_id,
            role_id=command.role_id,
            employee_type=EmploymentType.from_string(command.employee_type),
            reports_to_id=command.reports_to_id,
            date_joined=command.date_joined or date.today(),
            contract_from=command.contract_from,
            contract_to=command.contract_to,
            is_active=True,
            emergency_contact=EmergencyContact(
                name=command.emergency_contact_name or "",
                number=command.emergency_contact_number or "",
                relationship=command.emergency_contact_relationship or "",
            ),
        )

        # Save. Salary, banking, statutory, and leave data live in the
        # payroll/leave modules' own tables now (not on the Employee
        # aggregate) - see _get_payroll_info() for the corresponding read
        # path. All writes happen in one transaction so a failure partway
        # through doesn't leave an employee without their profile rows.
        with transaction.atomic():
            self._employees.add(employee)
            self._save_payroll_info(employee.id, command)
            if command.bank_name or command.bank_account:
                self._save_bank_account(employee.id, command)
            self._save_statutory_info(employee.id, command)
            self._save_leave_profile(employee.id, command.leave_days_entitled)

        # Publish event
        self._event_bus.publish(
            EmployeeHiredEvent(
                employee_id=employee.id,
                employee_number=str(employee.employee_id),
                first_name=employee.first_name,
                surname=employee.surname,
                department_id=employee.department_id,
                position_id=employee.position_id,
                date_joined=employee.date_joined,
            )
        )

        return employee

    def update_employee(self, command: UpdateEmployeeCommand) -> Employee:
        """
        Update an existing employee.

        Args:
            command: Update employee command

        Returns:
            Updated employee

        Raises:
            NotFoundError: If employee not found
            ValidationError: If validation fails
        """
        employee = self._employees.get_by_id(command.employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {command.employee_id} not found")

        changes = []

        with transaction.atomic():
            # Update personal info
            if command.first_name or command.surname or command.date_of_birth or command.gender or command.marital_status:
                employee.update_personal_info(
                    first_name=command.first_name,
                    surname=command.surname,
                    date_of_birth=command.date_of_birth,
                    gender=Gender.from_string(command.gender) if command.gender else None,
                    marital_status=MaritalStatus.from_string(command.marital_status) if command.marital_status else None,
                )
                changes.append("personal_info")

            # Update contact info
            if command.email is not None or command.phone is not None:
                employee.update_contact_info(email=command.email, phone=command.phone)
                changes.append("contact_info")

            # Update employment
            if any([command.department_id, command.position_id, command.role_id, command.employee_type, command.reports_to_id]):
                employee.update_employment(
                    department_id=command.department_id,
                    position_id=command.position_id,
                    role_id=command.role_id,
                    employee_type=EmploymentType.from_string(command.employee_type) if command.employee_type else None,
                    reports_to_id=command.reports_to_id,
                )
                changes.append("employment")

            # Update salary (lives in payroll.PayrollProfile, not on the entity)
            salary_change_event = None
            if command.usd_salary is not None or command.zig_salary is not None or command.pay_frequency is not None:
                old_info = self._get_payroll_info(employee.id)
                self._save_payroll_info(employee.id, command, existing=old_info)
                changes.append("salary")
                salary_change_event = SalaryChangedEvent(
                    employee_id=employee.id,
                    employee_number=str(employee.employee_id),
                    old_usd_amount=old_info["usd_salary"],
                    old_zig_amount=old_info["zig_salary"],
                    new_usd_amount=command.usd_salary if command.usd_salary is not None else old_info["usd_salary"],
                    new_zig_amount=command.zig_salary if command.zig_salary is not None else old_info["zig_salary"],
                )

            # Update banking, statutory, and leave profile - each lives in its
            # own table now, so update-or-create against those directly.
            if command.bank_name or command.bank_account:
                self._save_bank_account(employee.id, command)

            if any([command.nssa_number, command.zimra_number, command.paye_number, command.pays_aids_levy is not None, command.pension_fund is not None]):
                self._save_statutory_info(employee.id, command)

            if command.leave_days_entitled is not None:
                self._save_leave_profile(employee.id, command.leave_days_entitled)

            if any([command.bank_name, command.bank_account, command.pension_fund, command.nssa_number, command.zimra_number, command.paye_number, command.pays_aids_levy is not None, command.leave_days_entitled is not None]):
                changes.append("statutory_and_banking")

            if command.emergency_contact_name or command.emergency_contact_number or command.emergency_contact_relationship:
                employee.update_emergency_contact(EmergencyContact(
                    name=command.emergency_contact_name or employee.emergency_contact.name,
                    number=command.emergency_contact_number or employee.emergency_contact.number,
                    relationship=command.emergency_contact_relationship or employee.emergency_contact.relationship
                ))
                changes.append("emergency_contact")

            # Save
            self._employees.update(employee)

        if salary_change_event:
            self._event_bus.publish(salary_change_event)

        # Publish update event
        if changes:
            self._event_bus.publish(
                EmployeeUpdatedEvent(
                    employee_id=employee.id,
                    employee_number=str(employee.employee_id),
                    changes=tuple(changes),
                )
            )

        return employee

    def deactivate_employee(self, employee_id: int, reason: str = "") -> Employee:
        """
        Deactivate an employee (soft delete).

        Args:
            employee_id: Employee ID
            reason: Reason for deactivation

        Returns:
            Deactivated employee
        """
        employee = self._employees.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        employee.deactivate()
        self._employees.update(employee)

        self._event_bus.publish(
            EmployeeTerminatedEvent(
                employee_id=employee.id,
                employee_number=str(employee.employee_id),
                reason=reason,
            )
        )

        return employee

    def get_employee(self, employee_id: int) -> EmployeeDTO | None:
        """Get employee DTO by ID."""
        employee = self._employees.get_by_id(employee_id)
        if not employee:
            return None
        return self._to_dto(employee)

    def get_employee_by_employee_id(self, employee_id: str) -> EmployeeDTO | None:
        """Get employee DTO by employee number."""
        employee = self._employees.get_by_employee_id(employee_id)
        if not employee:
            return None
        return self._to_dto(employee)

    def get_active_employees(self) -> list[EmployeeDTO]:
        """Get all active employees."""
        employees = self._employees.get_all(include_inactive=False)
        return [self._to_dto(e) for e in employees]

    def get_employees_by_department(self, department_id: int) -> list[EmployeeDTO]:
        """Get employees in a department."""
        employees = self._employees.get_by_department(department_id)
        return [self._to_dto(e) for e in employees]

    def get_employee_salary(self, employee_id: int) -> SalaryDTO | None:
        """Get employee salary information."""
        employee = self._employees.get_by_id(employee_id)
        if not employee:
            return None
        payroll_info = self._get_payroll_info(employee.id)
        if payroll_info["usd_salary"] is None and payroll_info["zig_salary"] is None:
            return None
        return SalaryDTO(
            employee_id=employee.id,
            employee_number=str(employee.employee_id),
            usd_amount=payroll_info["usd_salary"] or Decimal("0"),
            zig_amount=payroll_info["zig_salary"] or Decimal("0"),
            pay_frequency=payroll_info["pay_frequency"],
        )

    def _get_payroll_info(self, employee_id: int) -> dict:
        """
        Fetch salary/banking info for an employee.

        Salary and bank account moved out of the Employee aggregate into the
        payroll module's normalized tables (PayrollProfile, EmployeeBankAccount)
        during the DB normalization pass, so they're read directly here rather
        than off the Employee entity.
        """
        from modules.payroll.infrastructure.persistence.models import (
            EmployeeBankAccount,
            PayrollProfile,
        )

        profile = PayrollProfile.objects.filter(employee_id=employee_id).first()
        bank = EmployeeBankAccount.objects.filter(
            employee_id=employee_id, is_primary=True
        ).first()

        return {
            "usd_salary": profile.usd_salary if profile else None,
            "zig_salary": profile.zig_salary if profile else None,
            "pay_frequency": profile.pay_frequency if profile else "monthly",
            "bank_name": bank.bank_name if bank else None,
            "bank_account": bank.account_number if bank else None,
        }

    def _save_payroll_info(
        self,
        employee_id: int,
        command: "CreateEmployeeCommand | UpdateEmployeeCommand",
        existing: dict | None = None,
    ) -> None:
        """Create or update the employee's PayrollProfile row."""
        from modules.payroll.infrastructure.persistence.models import PayrollProfile

        existing = existing or {}
        profile, _ = PayrollProfile.objects.get_or_create(employee_id=employee_id)
        profile.usd_salary = (
            command.usd_salary if command.usd_salary is not None
            else existing.get("usd_salary", profile.usd_salary) or 0
        )
        profile.zig_salary = (
            command.zig_salary if command.zig_salary is not None
            else existing.get("zig_salary", profile.zig_salary) or 0
        )
        profile.pay_frequency = command.pay_frequency or existing.get("pay_frequency") or profile.pay_frequency
        profile.save()

    def _save_bank_account(
        self, employee_id: int, command: "CreateEmployeeCommand | UpdateEmployeeCommand"
    ) -> None:
        """Create or update the employee's primary EmployeeBankAccount row."""
        from modules.payroll.infrastructure.persistence.models import EmployeeBankAccount

        bank, _ = EmployeeBankAccount.objects.get_or_create(
            employee_id=employee_id,
            is_primary=True,
            defaults={"bank_name": "", "account_number": ""},
        )
        if command.bank_name:
            bank.bank_name = command.bank_name
        if command.bank_account:
            bank.account_number = command.bank_account
        bank.save()

    def _save_statutory_info(
        self, employee_id: int, command: "CreateEmployeeCommand | UpdateEmployeeCommand"
    ) -> None:
        """Create or update the employee's StatutoryProfile row."""
        from modules.payroll.infrastructure.persistence.models import StatutoryProfile

        statutory, _ = StatutoryProfile.objects.get_or_create(employee_id=employee_id)
        if command.nssa_number:
            statutory.nssa_number = command.nssa_number
        if command.zimra_number:
            statutory.zimra_tax_number = command.zimra_number
        if command.paye_number:
            statutory.paye_number = command.paye_number
        if command.pays_aids_levy is not None:
            statutory.pays_aids_levy = command.pays_aids_levy
        if command.pension_fund is not None:
            statutory.pension_fund = command.pension_fund
        statutory.save()

    def _save_leave_profile(self, employee_id: int, leave_days_entitled: int) -> None:
        """Create or update the employee's LeaveProfile row."""
        from modules.leave.infrastructure.persistence.models import LeaveProfile

        LeaveProfile.objects.update_or_create(
            employee_id=employee_id,
            defaults={"leave_days_entitled": leave_days_entitled},
        )

    def _to_dto(self, employee: Employee) -> EmployeeDTO:
        """Convert employee entity to DTO."""
        dept_name = None
        if employee.department_id:
            dept = self._departments.get_by_id(employee.department_id)
            if dept:
                dept_name = dept.name

        pos_title = None
        if employee.position_id:
            pos = self._positions.get_by_id(employee.position_id)
            if pos:
                pos_title = pos.title

        payroll_info = self._get_payroll_info(employee.id)

        return EmployeeDTO(
            id=employee.id,
            employee_id=str(employee.employee_id),
            first_name=employee.first_name,
            surname=employee.surname,
            full_name=employee.full_name,
            email=employee.email.value if employee.email else None,
            phone=employee.phone.value if employee.phone else None,
            national_id=employee.national_id.value if employee.national_id else None,
            date_of_birth=employee.date_of_birth,
            gender=employee.gender.value if employee.gender else None,
            marital_status=employee.marital_status.value if employee.marital_status else None,
            department_id=employee.department_id,
            department_name=dept_name,
            position_id=employee.position_id,
            position_title=pos_title,
            employee_type=employee.employee_type.value,
            date_joined=employee.date_joined,
            is_active=employee.is_active,
            usd_salary=payroll_info["usd_salary"],
            zig_salary=payroll_info["zig_salary"],
            pay_frequency=payroll_info["pay_frequency"],
            bank_name=payroll_info["bank_name"],
            bank_account=payroll_info["bank_account"],
        )
