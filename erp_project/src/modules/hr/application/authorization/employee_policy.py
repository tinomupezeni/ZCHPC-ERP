"""
Authorization for employee lifecycle operations (REM-01).

RBACMiddleware only answers "may this user reach the hr routes at all". This
policy answers "may this actor create, reassign or deactivate *this*
employee", and EmployeeService calls it before anything is changed.

Every ``authorize_*`` method returns None or raises AuthorizationError /
ValidationError. The policy does no I/O: EmployeeService resolves the target
role's and target employee's permissions and hands them in.

Rules (confirmed REM-01 decisions - capability-based, no job-title hierarchy):

- Creating an employee needs ``hr.employee.create``.
- Setting a role or changing a department needs
  ``hr.employee.manage_assignments``, on create and on update alike.
- The assigned role must exist, and every permission it grants must already
  be held by the actor (``PermissionSet.covers``). Nobody can hand out
  authority they do not have themselves, so the organisation stays free to
  decide which roles hold which capabilities.
- Nobody may assign themselves a role granting anything they do not already
  hold. Self-demotion (e.g. an ADMIN taking a narrower role) stays allowed.
- Changing an existing employee's role or department also needs authority
  over that employee: the actor must hold every permission the target
  currently holds (AUD-01 F2), so nobody can demote or move someone above
  them.
- Deactivating an employee needs ``hr.employee.deactivate``, may not target
  the actor themselves, and may not target anyone whose effective
  permissions the actor does not hold (so, for example, only a full-access
  actor can deactivate a full-access one).
- Account operations on an employee's login through the identity API
  (REM-08) follow the same shape: re-enabling or unlocking a login needs
  ``hr.employee.reactivate``, permanently deleting one needs
  ``hr.employee.delete``, and both refuse the actor themselves and anyone
  holding permissions the actor lacks.

Superusers resolve to PermissionSet.full_access() via
resolve_actor_permissions, so they pass every capability and "covers" check
without special-casing here.
"""

from modules.hr.application.authorization.permissions import EmployeeManagementPermissions
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError, ValidationError


class EmployeeAuthorizationPolicy:
    def authorize_create(self, actor_permissions: PermissionSet) -> None:
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.CREATE,
            "Creating an employee",
            "EMPLOYEE_CREATE_NOT_AUTHORIZED",
        )

    def authorize_assignment(
        self,
        actor_permissions: PermissionSet,
        *,
        role_id: int | None,
        department_id: int | None,
        role_permissions: PermissionSet | None,
        is_self: bool,
    ) -> None:
        """
        Authorize setting ``role_id`` and/or ``department_id``.

        ``role_permissions`` is the permission set of the role being
        assigned, or None when no role with ``role_id`` exists.
        """
        if role_id is None and department_id is None:
            return

        self._require(
            actor_permissions,
            EmployeeManagementPermissions.MANAGE_ASSIGNMENTS,
            "Changing an employee's role or department",
            "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED",
        )

        if role_id is None:
            return

        if role_permissions is None:
            raise ValidationError(
                message=f"Role with ID {role_id} does not exist",
                code="INVALID_ROLE",
            )

        if actor_permissions.covers(role_permissions):
            return

        if is_self:
            raise AuthorizationError(
                "You cannot assign yourself a role that grants permissions you "
                "do not already hold.",
                code="EMPLOYEE_SELF_ROLE_ESCALATION",
            )
        raise AuthorizationError(
            "You cannot assign a role that grants permissions you do not hold.",
            code="EMPLOYEE_ROLE_EXCEEDS_ACTOR_AUTHORITY",
        )

    def authorize_assignment_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
    ) -> None:
        """
        Changing an existing employee's role or department also needs
        authority over that employee as they stand: the actor must hold every
        permission the target currently holds (AUD-01 F2). Without this, an
        actor could demote or move anyone above them to a role within their
        own ceiling. Acting on oneself always passes (an actor covers their
        own permissions); authorize_assignment still stops self-escalation.
        """
        if not actor_permissions.covers(target_permissions):
            raise AuthorizationError(
                "You cannot change the role or department of an employee who "
                "holds permissions you do not hold.",
                code="EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY",
            )

    def authorize_deactivate(self, actor_permissions: PermissionSet) -> None:
        """Capability check; runs before the target is loaded."""
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.DEACTIVATE,
            "Deactivating an employee",
            "EMPLOYEE_DEACTIVATE_NOT_AUTHORIZED",
        )

    def authorize_deactivate_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
        is_self: bool,
    ) -> None:
        self._require_target(
            actor_permissions,
            target_permissions,
            is_self,
            "deactivate",
            self_code="EMPLOYEE_SELF_DEACTIVATION",
        )

    def authorize_reactivate(self, actor_permissions: PermissionSet) -> None:
        """Capability to re-enable a disabled or locked-out login (REM-08)."""
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.REACTIVATE,
            "Reactivating or unlocking an account",
            "EMPLOYEE_REACTIVATE_NOT_AUTHORIZED",
        )

    def authorize_reactivate_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
        is_self: bool,
    ) -> None:
        self._require_target(
            actor_permissions,
            target_permissions,
            is_self,
            "reactivate",
            self_code="EMPLOYEE_SELF_REACTIVATION",
        )

    def authorize_delete(self, actor_permissions: PermissionSet) -> None:
        """Capability to permanently delete a login and its employee record (REM-08)."""
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.DELETE,
            "Deleting an account",
            "EMPLOYEE_DELETE_NOT_AUTHORIZED",
        )

    def authorize_delete_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
        is_self: bool,
    ) -> None:
        self._require_target(
            actor_permissions,
            target_permissions,
            is_self,
            "delete",
            self_code="EMPLOYEE_SELF_DELETION",
        )

    @staticmethod
    def _require_target(
        actor_permissions: PermissionSet,
        target_permissions: PermissionSet,
        is_self: bool,
        verb: str,
        *,
        self_code: str,
    ) -> None:
        """Never act on yourself; never on anyone holding more than you."""
        if is_self:
            raise AuthorizationError(
                f"You cannot {verb} your own account.",
                code=self_code,
            )
        if not actor_permissions.covers(target_permissions):
            raise AuthorizationError(
                f"You cannot {verb} an employee who holds permissions you do not hold.",
                code="EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY",
            )

    @staticmethod
    def _require(
        actor_permissions: PermissionSet, capability: str, action: str, code: str
    ) -> None:
        if actor_permissions.has_permission(capability):
            return
        raise AuthorizationError(
            f"{action} requires the '{capability}' permission.",
            code=code,
        )
