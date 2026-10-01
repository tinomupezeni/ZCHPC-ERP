"""
Employee lifecycle transitions (AUD-02).

The one place an employee's lifecycle state and the login switch of the
account behind it are changed. Employees.lifecycle_status (with its
is_active mirror) and CustomUser.is_active are always written here, together
and in one transaction, so a transition can never leave them disagreeing -
which is what let a disabled employee keep a working login, or a disabled
login keep being paid (AUD-02 F2).

Supported transitions:

    ACTIVE      -- deactivate -->  DEACTIVATED
    DEACTIVATED -- reactivate -->  ACTIVE
    ACTIVE      -- archive    -->  ARCHIVED
    DEACTIVATED -- archive    -->  ARCHIVED

ARCHIVED is final: deactivating or reactivating an archived employee is
refused by the Employee aggregate.

A transition is convergent: it always leaves the login matching the target
state, even if the employee was already in it. So deactivating an employee
whose login was somehow left enabled disables that login, and reactivating
one whose login was left disabled re-enables it. Asking for the state an
employee and login are both already in changes nothing.

This service does no authorization. Its callers do, before calling it:
EmployeeService (the hr employees API) and identity's UserService (the user
administration API), both through EmployeeAuthorizationPolicy.
"""

from dataclasses import dataclass

from django.db import transaction

from shared.domain.exceptions import ConflictError, NotFoundError
from shared.infrastructure import EventBus

from modules.hr.application.interfaces import IEmployeeRepository
from modules.hr.domain.entities import Employee
from modules.hr.domain.events import EmployeeTerminatedEvent


@dataclass
class LifecycleTransitionResult:
    """Outcome of a lifecycle transition."""

    employee: Employee
    # Whether the employee's lifecycle state itself changed.
    changed: bool
    # Set only when a disabled login was re-enabled: its one-time temporary
    # password, which the owner must replace (REM-07).
    temporary_password: str | None = None


class EmployeeLifecycleService:
    """Moves an employee and their login between lifecycle states together."""

    def __init__(
        self,
        employee_repository: IEmployeeRepository,
        user_repository=None,
        event_bus: EventBus | None = None,
        structural_assignments=None,
    ):
        """
        Args:
            employee_repository: Repository for employees
            user_repository: identity IUserRepository for the linked login
                (the Django one is built on first use if None)
            event_bus: Event bus for the existing employee events
            structural_assignments: The employee's department headships
                (the Django one is built on first use if None)
        """
        self._employees = employee_repository
        self._users = user_repository
        self._event_bus = event_bus or EventBus.get_instance()
        self._structure = structural_assignments

    def deactivate(self, employee_id: int, reason: str = "") -> LifecycleTransitionResult:
        """
        ACTIVE -> DEACTIVATED, and the linked login is disabled.

        A disabled login is refused on every request and on token refresh,
        so this also ends every session already issued. The role, department
        and every other assignment are left as they are.

        Raises:
            NotFoundError: If the employee does not exist
            ValidationError: If the employee is archived
        """
        from modules.identity.application.services import disable_login

        with transaction.atomic():
            employee = self._load_for_transition(employee_id)
            changed = employee.deactivate()
            if changed:
                self._employees.update(employee)
            if employee.user_id is not None:
                disable_login(self._user_repository(), employee.user_id)

        if changed:
            self._event_bus.publish(
                EmployeeTerminatedEvent(
                    employee_id=employee.id,
                    employee_number=str(employee.employee_id),
                    reason=reason,
                )
            )
        return LifecycleTransitionResult(employee=employee, changed=changed)

    def reactivate(self, employee_id: int) -> LifecycleTransitionResult:
        """
        DEACTIVATED -> ACTIVE, and the linked login is re-enabled.

        It is the same employee record: identity, EC number, role and
        department are untouched. A re-enabled login never gets its previous
        password back; identity issues a temporary one (REM-07), returned
        here once.

        Raises:
            NotFoundError: If the employee does not exist
            ValidationError: If the employee is archived
        """
        from modules.identity.application.services import enable_login

        temporary_password = None
        with transaction.atomic():
            employee = self._load_for_transition(employee_id)
            changed = employee.reactivate()
            if changed:
                self._employees.update(employee)
            if employee.user_id is not None:
                temporary_password = enable_login(self._user_repository(), employee.user_id)

        return LifecycleTransitionResult(
            employee=employee, changed=changed, temporary_password=temporary_password
        )

    def archive(
        self, employee_id: int, *, vacate_department_headships: bool = False
    ) -> LifecycleTransitionResult:
        """
        ACTIVE or DEACTIVATED -> ARCHIVED, and the linked login is disabled.

        Nothing is deleted: the employee row, role, EC number and history
        stay. An archived employee never authenticates again (identity's
        account_access rule) and is never reopened.

        Structural authority fails closed. An employee who heads a department
        is archived only if the caller explicitly asks to vacate those
        headships, and never while any of those departments has purchase
        requests awaiting department-head approval - reassign the head first
        (the department API), which hands the pending approvals over.

        Archiving an archived employee changes nothing.

        Raises:
            NotFoundError: If the employee does not exist
            ConflictError: EMPLOYEE_ARCHIVE_BLOCKED, with the departments
                headed and the pending approvals in ``details``
        """
        from modules.identity.application.services import disable_login

        with transaction.atomic():
            employee = self._load_for_transition(employee_id)
            changed = not employee.is_archived
            if changed:
                self._release_department_headships(employee.id, vacate_department_headships)
                employee.archive()
                self._employees.update(employee)
            if employee.user_id is not None:
                disable_login(self._user_repository(), employee.user_id)

        return LifecycleTransitionResult(employee=employee, changed=changed)

    def _release_department_headships(self, employee_id: int, vacate: bool) -> None:
        structure = self._structural_assignments()
        headed = structure.departments_headed_by(employee_id)
        if not headed:
            return
        pending = structure.pending_department_head_approvals(headed)
        if pending or not vacate:
            raise ConflictError(
                "The employee heads a department. Reassign the department head "
                "first, or vacate the headship explicitly when no approvals are "
                "waiting on it.",
                code="EMPLOYEE_ARCHIVE_BLOCKED",
                details={
                    "department_head_of": headed,
                    "pending_department_head_approvals": pending,
                },
            )
        structure.vacate_department_headships(employee_id)

    def _structural_assignments(self):
        if self._structure is None:
            from modules.hr.infrastructure.persistence.structural_assignments import (
                DjangoStructuralAssignments,
            )

            self._structure = DjangoStructuralAssignments()
        return self._structure

    def _load_for_transition(self, employee_id: int) -> Employee:
        """The employee, row-locked so concurrent transitions run one at a time."""
        employee = self._employees.get_by_id_for_update(employee_id)
        if employee is None:
            raise NotFoundError(f"Employee with ID {employee_id} not found")
        return employee

    def _user_repository(self):
        if self._users is None:
            from modules.identity.infrastructure.persistence.user_repository import (
                DjangoUserRepository,
            )

            self._users = DjangoUserRepository()
        return self._users
