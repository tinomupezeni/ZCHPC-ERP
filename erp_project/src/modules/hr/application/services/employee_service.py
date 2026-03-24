"""
Employee application service.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

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
    BankAccount,
    EmergencyContact,
    EmploymentType,
    Gender,
    MaritalStatus,
    PayFrequency,
    Salary,
    StatutoryInfo,
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
    emergency_contact_phone: str | None = None
    emergency_contact_relationship: str | None = None
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
    emergency_contact_phone: str | None = None
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

        # Generate employee ID
        id_generator = SequentialEmployeeIdGenerator(self._employees.get_max_employee_id)
        employee_id = id_generator.next_id()

        # Build salary if provided
        salary = None
        if command.usd_salary or command.zig_salary:
            salary = Salary.create(
                usd_amount=command.usd_salary,
                zig_amount=command.zig_salary,
            )

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
            salary=salary,
            pay_frequency=PayFrequency.from_string(command.pay_frequency),
            bank_account=BankAccount(
                bank_name=command.bank_name or "",
                account_number=command.bank_account or "",
            ),
            statutory_info=StatutoryInfo(
                nssa_number=command.nssa_number or "",
                zimra_number=command.zimra_number or "",
                paye_number=command.paye_number or "",
                pays_aids_levy=command.pays_aids_levy,
            ),
            pension_fund=command.pension_fund or "",
            emergency_contact=EmergencyContact(
                name=command.emergency_contact_name or "",
                phone=command.emergency_contact_phone or "",
                relationship=command.emergency_contact_relationship or "",
            ),
        )

        # Save
        self._employees.add(employee)

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

        # Update salary
        if command.usd_salary is not None or command.zig_salary is not None:
            old_salary = employee.salary
            new_salary = Salary.create(
                usd_amount=command.usd_salary if command.usd_salary is not None else (old_salary.usd_amount if old_salary else 0),
                zig_amount=command.zig_salary if command.zig_salary is not None else (old_salary.zig_amount if old_salary else 0),
            )
            employee.update_salary(new_salary)
            changes.append("salary")

            # Publish salary change event
            self._event_bus.publish(
                SalaryChangedEvent(
                    employee_id=employee.id,
                    employee_number=str(employee.employee_id),
                    old_usd_amount=old_salary.usd_amount if old_salary else None,
                    old_zig_amount=old_salary.zig_amount if old_salary else None,
                    new_usd_amount=new_salary.usd_amount,
                    new_zig_amount=new_salary.zig_amount,
                )
            )

        # Save
        self._employees.update(employee)

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
        if not employee or not employee.salary:
            return None
        return SalaryDTO(
            employee_id=employee.id,
            employee_number=str(employee.employee_id),
            usd_amount=employee.salary.usd_amount,
            zig_amount=employee.salary.zig_amount,
            pay_frequency=employee.pay_frequency.value,
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

        return EmployeeDTO(
            id=employee.id,
            employee_id=str(employee.employee_id),
            first_name=employee.first_name,
            surname=employee.surname,
            full_name=employee.full_name,
            email=employee.email.value if employee.email else None,
            department_id=employee.department_id,
            department_name=dept_name,
            position_id=employee.position_id,
            position_title=pos_title,
            date_joined=employee.date_joined,
            is_active=employee.is_active,
        )
