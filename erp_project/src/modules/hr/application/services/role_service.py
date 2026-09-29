"""
Role application service.

RoleService is deliberately thin: unlike Employee/Department/Position,
``Role`` has no existing repository or domain-entity layer in this module
(RoleListCreateView/RoleDetailView have always talked to the Django model
directly - see modules.hr.api.views.organization_views). Introducing a
full repository/domain rebuild for Role is out of scope for the
authorization fix this service exists to provide; this class adds exactly
one thing to the pre-existing direct-model-access shape - the
authorization boundary itself - following the same minimal-surface
approach modules.hr.application.services.employee_service.EmployeeService
already used for the analogous employee-assignment fix.
"""

from dataclasses import dataclass

from shared.domain.exceptions import AuthorizationError, NotFoundError, ValidationError

from modules.hr.application.authorization import RoleManagementPermissions
from modules.hr.infrastructure.persistence.models import Role
from modules.identity.domain.value_objects import PermissionSet


@dataclass
class CreateRoleCommand:
    """Command to create a new role."""

    name: str
    display_name: str | None = None
    description: str = ""
    permissions: list[str] | None = None


@dataclass
class UpdateRoleCommand:
    """Command to update an existing role."""

    role_id: int
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
    permissions_provided: bool = False


class RoleService:
    """
    Application service for role/permission administration.

    Every mutation here - create, metadata edit, permissions edit, delete -
    requires RoleManagementPermissions.MANAGE. This is the authorization
    boundary for "may this actor administer roles at all", enforced once,
    at the top of each method, before any other validation runs. Reaching
    this service already means RBACMiddleware's coarser "does this role
    hold anything in the hr module" gate was satisfied; that gate answers
    a different, weaker question and was never meant to be sufficient here
    (see modules.hr.application.authorization.permissions for why).

    Permission ceiling (AUD-01 F1), the same rule REM-01 applies to role
    assignment (``PermissionSet.covers``):

    - a role may only be written with permissions the actor already holds,
      so hr.role.manage cannot be used to grant "*" or anything else the
      actor lacks - including to a role the actor itself holds;
    - a role may only be changed or deleted by an actor who holds every
      permission it currently grants, so a narrower administrator cannot
      strip, rename or delete a more privileged role (e.g. ADMIN).

    A superuser or "*" holder covers everything and is unaffected.
    """

    @staticmethod
    def _authorize_role_administration(actor_permissions: PermissionSet) -> None:
        if actor_permissions.has_permission(RoleManagementPermissions.MANAGE):
            return

        raise AuthorizationError(
            "Administering roles requires the "
            f"'{RoleManagementPermissions.MANAGE}' permission.",
            code="ROLE_ADMINISTRATION_NOT_AUTHORIZED",
        )

    @staticmethod
    def _requested_permissions(permissions) -> PermissionSet:
        """
        Parse a requested permission list. Only a list of non-empty strings is
        accepted: a bare string would otherwise be stored and later read one
        character at a time, so "portal.*" would grant "*".
        """
        if permissions is None:
            return PermissionSet.empty()
        if not isinstance(permissions, list) or not all(
            isinstance(p, str) and p.strip() for p in permissions
        ):
            raise ValidationError(
                message="Permissions must be a list of non-empty strings",
                code="INVALID_ROLE_PERMISSIONS",
            )
        return PermissionSet.from_list(permissions)

    @staticmethod
    def _current_permissions(role: Role) -> PermissionSet:
        """
        What the stored role grants, parsed exactly as permission_set_for_user
        parses it. A value that cannot be parsed is treated as full access, so
        only a full-access actor may touch it.
        """
        try:
            return PermissionSet.from_list(list(role.permissions or []))
        except (TypeError, ValidationError):
            return PermissionSet.full_access()

    @staticmethod
    def _require_covers(
        actor_permissions: PermissionSet, permissions: PermissionSet, message: str, code: str
    ) -> None:
        if not actor_permissions.covers(permissions):
            raise AuthorizationError(message, code=code)

    def _authorize_role_target(self, actor_permissions: PermissionSet, role: Role) -> None:
        self._require_covers(
            actor_permissions,
            self._current_permissions(role),
            "You cannot modify a role that grants permissions you do not hold.",
            "ROLE_TARGET_EXCEEDS_ACTOR_AUTHORITY",
        )

    def _authorize_grant(self, actor_permissions: PermissionSet, permissions: PermissionSet) -> None:
        self._require_covers(
            actor_permissions,
            permissions,
            "You cannot grant permissions you do not hold.",
            "ROLE_PERMISSIONS_EXCEED_ACTOR_AUTHORITY",
        )

    def create_role(self, command: CreateRoleCommand, actor_permissions: PermissionSet) -> Role:
        """
        Create a new role.

        Raises:
            AuthorizationError: If actor_permissions lacks
                RoleManagementPermissions.MANAGE, or the role would grant
                permissions the actor does not hold.
            ValidationError: If name is missing or already in use, or the
                permissions are not a list of non-empty strings.
        """
        self._authorize_role_administration(actor_permissions)
        self._authorize_grant(actor_permissions, self._requested_permissions(command.permissions))

        if not command.name:
            raise ValidationError(message="Name is required", code="ROLE_NAME_REQUIRED")

        if Role.objects.filter(name=command.name).exists():
            raise ValidationError(
                message=f"Role with name '{command.name}' already exists",
                code="DUPLICATE_ROLE_NAME",
            )

        return Role.objects.create(
            name=command.name,
            display_name=command.display_name or command.name,
            description=command.description,
            permissions=command.permissions or [],
        )

    def update_role(self, command: UpdateRoleCommand, actor_permissions: PermissionSet) -> Role:
        """
        Update an existing role's metadata and/or permissions.

        Raises:
            AuthorizationError: If actor_permissions lacks
                RoleManagementPermissions.MANAGE, the role currently grants
                permissions the actor does not hold, or the new permissions
                exceed the actor's own.
            NotFoundError: If the role does not exist.
            ValidationError: If the permissions are not a list of non-empty
                strings.
        """
        self._authorize_role_administration(actor_permissions)
        if command.permissions_provided:
            requested = self._requested_permissions(command.permissions)
            self._authorize_grant(actor_permissions, requested)

        try:
            role = Role.objects.get(id=command.role_id)
        except Role.DoesNotExist:
            raise NotFoundError(f"Role with ID {command.role_id} not found")

        self._authorize_role_target(actor_permissions, role)

        if command.name is not None:
            role.name = command.name
        if command.display_name is not None:
            role.display_name = command.display_name
        if command.description is not None:
            role.description = command.description
        if command.permissions_provided:
            role.permissions = command.permissions or []

        role.save()
        return role

    def delete_role(self, role_id: int, actor_permissions: PermissionSet) -> None:
        """
        Delete a role.

        Raises:
            AuthorizationError: If actor_permissions lacks
                RoleManagementPermissions.MANAGE, or the role grants
                permissions the actor does not hold.
            NotFoundError: If the role does not exist.
        """
        self._authorize_role_administration(actor_permissions)

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise NotFoundError(f"Role with ID {role_id} not found")

        self._authorize_role_target(actor_permissions, role)
        role.delete()
