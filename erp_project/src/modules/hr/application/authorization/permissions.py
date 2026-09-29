"""
Employee-management capability strings (RBAC permission vocabulary).

Mirrors the pattern already used by
``modules.procurement.application.authorization.permissions``:

    - permissions are dotted strings matched by
      ``modules.identity.domain.value_objects.Permission``
    - a role's granted permissions live in ``hr.Role.permissions`` (JSON
      list) and are loaded into an identity ``PermissionSet`` by
      ``modules.identity.infrastructure.route_access.permission_set_for_user``

No new authorization framework is introduced here - only the capability
vocabulary this specific check needs. Reaching the ``hr`` module (the
coarse RBACMiddleware gate) is not sufficient to reassign an employee's
role or department; that additionally requires the capability below, so a
role scoped to ordinary employee-record maintenance does not automatically
carry the authority to grant itself (or anyone else) elevated access.

Note on wildcards: the existing ``Permission`` semantics mean a role
granted ``hr.*`` or ``*`` is granted this capability too. Roles that should
only maintain ordinary employee fields must not be granted either of those
broader wildcards alongside employee-management access.

RoleManagementPermissions exists for the same reason, one layer further
upstream: ``hr.*`` (or any narrower ``hr.`` grant) is enough to reach the
Roles API at all, but must not by itself be enough to administer
``Role.permissions`` - the record that determines what every permission
check in the system, including this one, actually grants. Without a
capability distinct from general ``hr.`` reachability, any actor who can
reach the Roles API could grant themselves EmployeeManagementPermissions
.MANAGE_ASSIGNMENTS (or anything else) directly, defeating it from
upstream. This is deliberately a single, undifferentiated capability
covering role creation, metadata edits, permission-list changes, and
deletion - the confirmed business requirement is "HR administers roles",
not a more granular breakdown, and the repository gives no evidence such
a breakdown is needed.
"""


class EmployeeManagementPermissions:
    """Capability strings for employee-record administration."""

    CREATE = "hr.employee.create"
    DEACTIVATE = "hr.employee.deactivate"
    MANAGE_ASSIGNMENTS = "hr.employee.manage_assignments"
    # REM-08: account-level operations on an employee's login. Kept under
    # hr.employee.* on purpose: migration 0017 granted identity.* to nearly
    # every legacy role, so any identity.* capability would be held by
    # ordinary staff through that wildcard.
    REACTIVATE = "hr.employee.reactivate"
    DELETE = "hr.employee.delete"


class RoleManagementPermissions:
    """Capability strings for role/permission administration."""

    MANAGE = "hr.role.manage"


class DepartmentManagementPermissions:
    """
    Capability strings for department administration (AUD-01 F8).

    Creating, renaming, deleting a department and recording its head all need
    MANAGE. The head is security-relevant: procurement's department-head
    approval authority is Department.head. Reaching the hr routes (any hr.*
    grant, e.g. hr.employee.view) is not enough. Which roles hold it is the
    organisation's decision, made through the Roles API.
    """

    MANAGE = "hr.department.manage"
