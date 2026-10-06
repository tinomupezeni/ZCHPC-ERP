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
- Editing an employee's ordinary fields (name, date of birth, gender,
  marital status, phone, emergency contact; and position, employee type and
  reporting line, which grant no authority - AUD-02 F9) needs authority over
  that employee in the same sense (AUD-02 F1). There is no separate capability:
  reaching the hr routes is the prerequisite, authority over the target is
  the rule. Yourself and your peers are covered.
- Deactivating an employee needs ``hr.employee.deactivate``, may not target
  the actor themselves, and may not target anyone whose effective
  permissions the actor does not hold (so, for example, only a full-access
  actor can deactivate a full-access one).
- Account operations on an employee's login through the identity API
  (REM-08) follow the same shape: re-enabling or unlocking a login needs
  ``hr.employee.reactivate``, and refuses the actor themselves and anyone
  holding permissions the actor lacks. There is no delete operation to
  authorize (AUD-02).
- Archiving an employee (AUD-02) needs ``hr.employee.archive`` and the same
  target rule. Reading archived employees' records needs
  ``hr.employee.view_archived``; ordinary employee access does not include it.
- Seeing another person's login (AUD-02 F6) needs ``hr.employee.view``.
  Everyone may see their own. It is a read: there is no target-authority
  ("covers") check, so a viewer sees accounts above them too. Which of those
  logins are listed is a separate lifecycle rule, applied by UserService.

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

    def authorize_update_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
    ) -> None:
        """
        Editing an employee's ordinary fields (AUD-02 F1) needs authority
        over that employee as they stand. Judged whenever such a field is
        sent, changed or not. Acting on oneself always passes (an actor
        covers their own permissions).
        """
        self._require_covers(
            actor_permissions,
            target_permissions,
            "You cannot edit an employee who holds permissions you do not hold.",
        )

    def authorize_rename_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
    ) -> None:
        """
        Renaming another login (AUD-02 F7) also needs authority over it as it
        stands. Renaming yourself needs neither, and callers do not ask.
        """
        self._require_covers(
            actor_permissions,
            target_permissions,
            "You cannot rename an account that holds permissions you do not hold.",
        )

    def authorize_login_attachment_target(
        self,
        actor_permissions: PermissionSet,
        *,
        target_permissions: PermissionSet,
    ) -> None:
        """
        Creating an employee whose email matches an existing login attaches
        the new record to that login (AUD-02 F7): it gains an employee
        record, a department, any role given, and an employment lifecycle
        that from then on decides whether it may log in. That needs
        authority over the login as it stands. A login that holds nothing
        is covered by anyone allowed to create employees.
        """
        self._require_covers(
            actor_permissions,
            target_permissions,
            "You cannot attach an employee record to an existing account that "
            "holds permissions you do not hold.",
        )

    @staticmethod
    def _require_covers(
        actor_permissions: PermissionSet, target_permissions: PermissionSet, message: str
    ) -> None:
        if not actor_permissions.covers(target_permissions):
            raise AuthorizationError(message, code="EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY")

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

    def authorize_archive(self, actor_permissions: PermissionSet) -> None:
        """Capability to permanently close an employment lifecycle (AUD-02)."""
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.ARCHIVE,
            "Archiving an employee",
            "EMPLOYEE_ARCHIVE_NOT_AUTHORIZED",
        )

    def authorize_archive_target(
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
            "archive",
            self_code="EMPLOYEE_SELF_ARCHIVE",
        )

    def authorize_view_archived(self, actor_permissions: PermissionSet) -> None:
        """Capability to read the records of archived employees (AUD-02)."""
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.VIEW_ARCHIVED,
            "Viewing archived employees",
            "EMPLOYEE_VIEW_ARCHIVED_NOT_AUTHORIZED",
        )

    def may_view_archived(self, actor_permissions: PermissionSet | None) -> bool:
        return (actor_permissions or PermissionSet.empty()).has_permission(
            EmployeeManagementPermissions.VIEW_ARCHIVED
        )

    def may_view_accounts(self, actor_permissions: PermissionSet | None) -> bool:
        """Whether the actor may see other people's logins (AUD-02 F6)."""
        return (actor_permissions or PermissionSet.empty()).has_permission(
            EmployeeManagementPermissions.VIEW
        )

    def authorize_view_account(
        self, actor_permissions: PermissionSet, *, is_self: bool
    ) -> None:
        """
        Reading one login (AUD-02 F6): your own always; anyone else's needs
        hr.employee.view. Checked before the target is loaded, so a refusal
        says nothing about whether the account exists.
        """
        if is_self:
            return
        self._require(
            actor_permissions,
            EmployeeManagementPermissions.VIEW,
            "Viewing another user's account",
            "EMPLOYEE_VIEW_NOT_AUTHORIZED",
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
