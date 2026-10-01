"""
Employee application service.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.db import transaction

from shared.domain.exceptions import AuthorizationError, ValidationError, NotFoundError
from shared.domain.value_objects import Email, NationalId, PhoneNumber, EmployeeId
from shared.infrastructure import EventBus

from modules.hr.application.authorization import (
    EmployeeAuthorizationPolicy,
    resolve_actor_permissions,
)
from modules.hr.application.services.employee_lifecycle_service import (
    EmployeeLifecycleService,
    LifecycleTransitionResult,
)
from modules.hr.application.interfaces import (
    IEmployeeRepository,
    IDepartmentRepository,
    IPositionRepository,
    EmployeeDTO,
    SalaryDTO,
)
from modules.identity.domain.value_objects import PermissionSet
from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
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
        lifecycle_service: EmployeeLifecycleService | None = None,
    ):
        """Initialize service with repositories."""
        self._employees = employee_repository
        self._departments = department_repository
        self._positions = position_repository
        self._event_bus = event_bus or EventBus.get_instance()
        self._policy = EmployeeAuthorizationPolicy()
        # The one transition authority for lifecycle state (AUD-02).
        self._lifecycle = lifecycle_service or EmployeeLifecycleService(
            employee_repository=employee_repository, event_bus=self._event_bus
        )

    def _role_permissions(self, role_id: int | None) -> PermissionSet | None:
        """
        The permissions of role ``role_id``, or None if it does not exist.

        Read from hr.Role directly, as RoleService and permission_set_for_user
        do: the identity Role entity rejects names the Roles API accepts
        (e.g. hyphens), so it cannot be used to look up arbitrary roles.
        """
        if role_id is None:
            return None
        from modules.hr.infrastructure.persistence.models import Role

        role = Role.objects.filter(pk=role_id).only("permissions").first()
        if role is None:
            return None
        return PermissionSet.from_list(list(role.permissions or []))

    def _authorize_assignment(
        self,
        actor_permissions: PermissionSet,
        *,
        role_id: int | None,
        department_id: int | None,
        is_self: bool,
    ) -> None:
        """
        The one role/department assignment boundary, shared by create and
        update (see EmployeeAuthorizationPolicy.authorize_assignment).

        Reaching this service at all already means the caller passed
        RBACMiddleware's coarse "does this role hold anything in the hr
        module" gate - that gate was never meant to be the boundary for a
        specific, sensitive field change. Every other field is unaffected.
        """
        self._policy.authorize_assignment(
            actor_permissions,
            role_id=role_id,
            department_id=department_id,
            role_permissions=self._role_permissions(role_id),
            is_self=is_self,
        )

    @staticmethod
    def _authorize_payroll_data_changes(
        command: "CreateEmployeeCommand | UpdateEmployeeCommand",
        actor_permissions: PermissionSet | None,
        target_employee_id: int | None,
    ) -> None:
        """
        Salary, bank and statutory data live in payroll's tables and are
        governed by payroll's authorization policy (REM-02): reaching the hr
        module and being allowed to edit an employee is not, by itself,
        authority to write this data. Runs before anything is loaded or saved.

        ``actor_permissions=None`` is treated as holding nothing.
        """
        salary = (
            command.usd_salary is not None
            or command.zig_salary is not None
            or (isinstance(command, UpdateEmployeeCommand) and command.pay_frequency is not None)
        )
        bank = bool(command.bank_name or command.bank_account)
        statutory = bool(
            command.nssa_number
            or command.zimra_number
            or command.paye_number
            or command.pension_fund
            or (isinstance(command, UpdateEmployeeCommand) and command.pays_aids_levy is not None)
        )
        if not (salary or bank or statutory):
            return

        policy = PayrollAuthorizationPolicy()
        actor = PayrollActor.from_permissions(actor_permissions or PermissionSet.empty())
        if salary:
            policy.authorize_manage_payroll_profile(actor, target_employee_id)
        if bank:
            policy.authorize_manage_bank_accounts(actor, target_employee_id)
        if statutory:
            policy.authorize_manage_statutory_profile(actor, target_employee_id)

    def create_employee(
        self,
        command: CreateEmployeeCommand,
        actor_permissions: PermissionSet | None = None,
        actor_email: str | None = None,
    ) -> Employee:
        """
        Create a new employee.

        Args:
            command: Create employee command
            actor_permissions: The creating actor's permissions. None holds
                nothing. Creation needs hr.employee.create; a role_id also
                goes through the role-assignment boundary, and salary, bank
                or statutory data need the matching payroll capabilities.
            actor_email: The creating actor's login email, from the
                authenticated request. The new record is linked to an
                existing login with the same email (modules.hr.signals), so
                a matching email makes a role_id a self-assignment.

        Returns:
            Created employee

        Raises:
            AuthorizationError: If the actor lacks a required capability or
                may not assign the requested role.
            ValidationError: If validation fails (including an unknown role_id)
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_create(actor_permissions)
        # Initial department placement is part of creating the record (the
        # admin UI always sends it); only the role is an assignment here.
        self._authorize_assignment(
            actor_permissions,
            role_id=command.role_id,
            department_id=None,
            is_self=bool(
                actor_email
                and command.email
                and actor_email.strip().lower() == command.email.strip().lower()
            ),
        )
        self._authorize_payroll_data_changes(command, actor_permissions, None)
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

        # An archived employee is given no new reports (AUD-02).
        self._ensure_not_archived_manager(command.reports_to_id)

        # A requested EC number is checked here only for its format; whether
        # it is free is decided under the allocation lock below.
        requested_employee_id = (
            EmployeeId(command.employee_id.strip())
            if command.employee_id and command.employee_id.strip()
            else None
        )

        # Save. Salary, banking, statutory, and leave data live in the
        # payroll/leave modules' own tables now (not on the Employee
        # aggregate) - see _get_payroll_info() for the corresponding read
        # path. All writes happen in one transaction so a failure partway
        # through doesn't leave an employee without their profile rows.
        # The EC number is allocated in the same transaction (AUD-02).
        with transaction.atomic():
            employee_id = self._allocate_employee_id(requested_employee_id)

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
                emergency_contact=EmergencyContact(
                    name=command.emergency_contact_name or "",
                    number=command.emergency_contact_number or "",
                    relationship=command.emergency_contact_relationship or "",
                ),
            )

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

    def _allocate_employee_id(self, requested: EmployeeId | None) -> EmployeeId:
        """
        The EC number for a new employee (AUD-02). Must run inside the
        transaction that adds the employee.

        An EC number belongs to one employee for all time: the holder's row
        is never deleted and the number on it never changes, so any number a
        row holds - whatever its lifecycle state - is consumed. Allocation is
        serialized for the rest of the transaction, so the check below and
        the insert cannot interleave with another creation.

        A requested number is accepted only if no employee holds it (compared
        in its normalized form, e.g. "emp0007" is EMP0007); otherwise the next
        number after the highest one held is issued.

        Raises:
            ValidationError: DUPLICATE_EMPLOYEE_ID if the requested number is held
        """
        self._employees.lock_employee_id_allocation()
        if requested is not None:
            if self._employees.exists_by_employee_id(requested.value):
                raise ValidationError(
                    message=f"Employee with EC Number {requested.value} already exists",
                    code="DUPLICATE_EMPLOYEE_ID",
                )
            return requested
        return SequentialEmployeeIdGenerator(self._employees.get_max_employee_id).next_id()

    def update_employee(
        self,
        command: UpdateEmployeeCommand,
        actor_permissions: PermissionSet,
        actor_employee_id: int | None = None,
    ) -> Employee:
        """
        Update an existing employee.

        Args:
            command: Update employee command
            actor_permissions: The permissions held by the employee making
                this request, per ``hr.Role.permissions`` (see
                ``modules.identity.infrastructure.route_access
                .permission_set_for_user``). Required so this method - not
                just the coarse per-module HTTP gate - can enforce who may
                reassign an employee's role or department.
            actor_employee_id: The acting employee's own record id, from the
                authenticated request, so a role change on it is judged as a
                self-assignment.

        Returns:
            Updated employee

        Raises:
            AuthorizationError: If the command changes role_id or
                department_id without EmployeeManagementPermissions
                .MANAGE_ASSIGNMENTS, assigns a role the actor may not grant,
                or changes the role/department of an employee who holds
                permissions the actor does not.
            NotFoundError: If employee not found
            ValidationError: If validation fails (including an unknown role_id)
        """
        self._authorize_assignment(
            actor_permissions,
            role_id=command.role_id,
            department_id=command.department_id,
            is_self=actor_employee_id is not None and actor_employee_id == command.employee_id,
        )
        self._authorize_payroll_data_changes(command, actor_permissions, command.employee_id)

        employee = self._employees.get_by_id(command.employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {command.employee_id} not found")

        # An archived employee's record is closed (AUD-02), and an archived
        # employee is given no new reports.
        employee.ensure_not_archived("edited")
        self._ensure_not_archived_manager(command.reports_to_id)

        # Target authority (AUD-01 F2): judged on the employee as they stand,
        # and only when the role or department actually changes.
        if (command.role_id is not None and command.role_id != employee.role_id) or (
            command.department_id is not None and command.department_id != employee.department_id
        ):
            self._policy.authorize_assignment_target(
                actor_permissions,
                target_permissions=self._effective_permissions(employee),
            )

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

    def deactivate_employee(
        self,
        employee_id: int,
        reason: str = "",
        actor_permissions: PermissionSet | None = None,
        actor_employee_id: int | None = None,
        actor_user_id=None,
    ) -> Employee:
        """
        Deactivate an employee (soft delete) and disable their login.

        Args:
            employee_id: Employee ID
            reason: Reason for deactivation
            actor_permissions: The acting user's permissions. None holds
                nothing. Needs hr.employee.deactivate, checked before the
                target is loaded, and must cover the target's own effective
                permissions.
            actor_employee_id: The acting employee's own record id, from the
                authenticated request; deactivating it is refused.

        Returns:
            Deactivated employee

        Raises:
            AuthorizationError: If the actor may not deactivate this employee.
            NotFoundError: If employee not found
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_deactivate(actor_permissions)

        employee = self._employees.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        self._policy.authorize_deactivate_target(
            actor_permissions,
            target_permissions=self._effective_permissions(employee),
            is_self=actor_employee_id is not None and actor_employee_id == employee.id,
        )

        # The employee record and its login go inactive together or not at
        # all, through the one transition authority (AUD-02).
        return self._lifecycle.deactivate(
            employee.id, reason, actor_user_id=actor_user_id, source="hr.employee.deactivate"
        ).employee

    def reactivate_employee(
        self,
        employee_id: int,
        actor_permissions: PermissionSet | None = None,
        actor_employee_id: int | None = None,
        actor_user_id=None,
        reason: str = "",
    ) -> LifecycleTransitionResult:
        """
        Reactivate a deactivated employee and re-enable their login.

        The same employee record returns to ACTIVE: identity, EC number,
        role and department are untouched. A re-enabled login is issued a
        temporary password (REM-07), carried on the result.

        Args:
            employee_id: Employee ID
            actor_permissions: The acting user's permissions. None holds
                nothing. Needs hr.employee.reactivate, checked before the
                target is loaded, and must cover the target's own (dormant)
                permissions.
            actor_employee_id: The acting employee's own record id, from the
                authenticated request; reactivating it is refused.

        Returns:
            The transition result (employee, and any temporary password)

        Raises:
            AuthorizationError: If the actor may not reactivate this employee.
            NotFoundError: If employee not found
            ValidationError: If the employee is archived
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_reactivate(actor_permissions)

        employee = self._employees.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        self._policy.authorize_reactivate_target(
            actor_permissions,
            target_permissions=self._effective_permissions(employee),
            is_self=actor_employee_id is not None and actor_employee_id == employee.id,
        )

        return self._lifecycle.reactivate(
            employee.id, actor_user_id=actor_user_id, reason=reason, source="hr.employee.reactivate"
        )

    def archive_employee(
        self,
        employee_id: int,
        actor_permissions: PermissionSet | None = None,
        actor_employee_id: int | None = None,
        vacate_department_headships: bool = False,
        actor_user_id=None,
        reason: str = "",
    ) -> LifecycleTransitionResult:
        """
        Archive an employee: permanently close their employment lifecycle
        (AUD-02). See EmployeeLifecycleService.archive.

        Args:
            employee_id: Employee ID
            actor_permissions: The acting user's permissions. None holds
                nothing. Needs hr.employee.archive, checked before the target
                is loaded, and must cover the target's own permissions.
            actor_employee_id: The acting employee's own record id, from the
                authenticated request; archiving it is refused.
            vacate_department_headships: Explicitly leave any department the
                employee heads without a head.

        Raises:
            AuthorizationError: If the actor may not archive this employee.
            NotFoundError: If employee not found
            ConflictError: If structural authority blocks the archive
        """
        actor_permissions = actor_permissions or PermissionSet.empty()
        self._policy.authorize_archive(actor_permissions)

        employee = self._employees.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        self._policy.authorize_archive_target(
            actor_permissions,
            target_permissions=self._effective_permissions(employee),
            is_self=actor_employee_id is not None and actor_employee_id == employee.id,
        )

        return self._lifecycle.archive(
            employee.id,
            vacate_department_headships=vacate_department_headships,
            actor_user_id=actor_user_id,
            reason=reason,
            source="hr.employee.archive",
        )

    def _ensure_not_archived_manager(self, reports_to_id: int | None) -> None:
        """An archived employee is given no new reports (AUD-02)."""
        if reports_to_id is None:
            return
        manager = self._employees.get_by_id(reports_to_id)
        if manager is not None:
            manager.ensure_not_archived("assigned as a manager")

    def get_employee(
        self, employee_id: int, actor_permissions: PermissionSet | None = None
    ) -> EmployeeDTO | None:
        """
        Get employee DTO by ID.

        Salary/bank fields are populated only for an actor holding the matching
        payroll view capability; otherwise they are None (see _to_dto).

        An archived employee is returned only to an actor holding
        hr.employee.view_archived; to anyone else they do not exist (AUD-02).
        """
        employee = self._employees.get_by_id(employee_id)
        if not employee:
            return None
        if employee.is_archived and not self._policy.may_view_archived(actor_permissions):
            return None
        return self._to_dto(employee, actor_permissions)

    def get_employee_by_employee_id(
        self, employee_id: str, actor_permissions: PermissionSet | None = None
    ) -> EmployeeDTO | None:
        """Get employee DTO by employee number."""
        employee = self._employees.get_by_employee_id(employee_id)
        if not employee:
            return None
        return self._to_dto(employee, actor_permissions)

    def get_active_employees(
        self, actor_permissions: PermissionSet | None = None
    ) -> list[EmployeeDTO]:
        """Get all active employees."""
        employees = self._employees.get_all(include_inactive=False)
        return [self._to_dto(e, actor_permissions) for e in employees]

    def get_all_employees(
        self,
        actor_permissions: PermissionSet | None = None,
        include_archived: bool = False,
    ) -> list[EmployeeDTO]:
        """
        Every employee, active or deactivated. Archived employees are left
        out unless asked for, which needs hr.employee.view_archived (AUD-02).

        Raises:
            AuthorizationError: If archived employees are asked for without
                the capability
        """
        if include_archived:
            self._policy.authorize_view_archived(actor_permissions or PermissionSet.empty())
        employees = [
            employee
            for employee in self._employees.get_all(include_inactive=True)
            if include_archived or not employee.is_archived
        ]
        return [self._to_dto(e, actor_permissions) for e in employees]

    def get_employees_by_department(
        self, department_id: int, actor_permissions: PermissionSet | None = None
    ) -> list[EmployeeDTO]:
        """Get employees in a department."""
        employees = self._employees.get_by_department(department_id)
        return [self._to_dto(e, actor_permissions) for e in employees]

    def get_employee_salary(
        self, employee_id: int, actor_permissions: PermissionSet | None
    ) -> SalaryDTO | None:
        """
        Get employee salary information.

        Requires the payroll profile-view capability, checked before anything
        about the employee is loaded (so a caller without it cannot tell
        whether the employee exists).
        """
        PayrollAuthorizationPolicy().authorize_view_payroll_profile(
            PayrollActor.from_permissions(actor_permissions or PermissionSet.empty()),
            employee_id,
        )
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

    def _effective_permissions(self, employee: Employee) -> PermissionSet:
        """
        What this employee's login can actually do: resolved the same way as
        for an acting user (resolve_actor_permissions, so a linked superuser
        is full access), or from their role alone when they have no login.
        """
        if employee.user_id is not None:
            from modules.identity.infrastructure.persistence.models import CustomUser

            user = CustomUser.objects.filter(pk=employee.user_id).first()
            if user is not None:
                return resolve_actor_permissions(user)
        return self._role_permissions(employee.role_id) or PermissionSet.empty()

    def _save_leave_profile(self, employee_id: int, leave_days_entitled: int) -> None:
        """Create or update the employee's LeaveProfile row."""
        from modules.leave.infrastructure.persistence.models import LeaveProfile

        LeaveProfile.objects.update_or_create(
            employee_id=employee_id,
            defaults={"leave_days_entitled": leave_days_entitled},
        )

    @staticmethod
    def _permitted(authorize, actor: PayrollActor, employee_id: int) -> bool:
        try:
            authorize(actor, employee_id)
        except AuthorizationError:
            return False
        return True

    def _payroll_fields_for(
        self, employee_id: int, actor_permissions: PermissionSet | None
    ) -> dict:
        """
        Salary/bank values for a DTO, redacted to None unless the actor holds
        the matching payroll view capability (REM-02). Nothing is read from
        payroll's tables when neither is held. None permissions hold nothing.
        """
        policy = PayrollAuthorizationPolicy()
        actor = PayrollActor.from_permissions(actor_permissions or PermissionSet.empty())
        may_profile = self._permitted(policy.authorize_view_payroll_profile, actor, employee_id)
        may_bank = self._permitted(policy.authorize_view_bank_accounts, actor, employee_id)

        info = {
            "usd_salary": None,
            "zig_salary": None,
            "pay_frequency": None,
            "bank_name": None,
            "bank_account": None,
        }
        if not (may_profile or may_bank):
            return info

        payroll_info = self._get_payroll_info(employee_id)
        if may_profile:
            for key in ("usd_salary", "zig_salary", "pay_frequency"):
                info[key] = payroll_info[key]
        if may_bank:
            for key in ("bank_name", "bank_account"):
                info[key] = payroll_info[key]
        return info

    def _to_dto(
        self, employee: Employee, actor_permissions: PermissionSet | None = None
    ) -> EmployeeDTO:
        """Convert employee entity to DTO (payroll fields redacted by default)."""
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

        payroll_info = self._payroll_fields_for(employee.id, actor_permissions)

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
