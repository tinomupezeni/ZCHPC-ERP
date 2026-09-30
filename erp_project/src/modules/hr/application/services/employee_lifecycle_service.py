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

Anything involving ARCHIVED is refused by the Employee aggregate; there is
no archive transition here.

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

from shared.domain.exceptions import NotFoundError
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
    ):
        """
        Args:
            employee_repository: Repository for employees
            user_repository: identity IUserRepository for the linked login
                (the Django one is built on first use if None)
            event_bus: Event bus for the existing employee events
        """
        self._employees = employee_repository
        self._users = user_repository
        self._event_bus = event_bus or EventBus.get_instance()

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
