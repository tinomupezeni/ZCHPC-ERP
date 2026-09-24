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

    def create_role(self, command: CreateRoleCommand, actor_permissions: PermissionSet) -> Role:
        """
        Create a new role.

        Raises:
            AuthorizationError: If actor_permissions lacks
                RoleManagementPermissions.MANAGE.
            ValidationError: If name is missing or already in use.
        """
        self._authorize_role_administration(actor_permissions)

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
                RoleManagementPermissions.MANAGE.
            NotFoundError: If the role does not exist.
        """
        self._authorize_role_administration(actor_permissions)

        try:
            role = Role.objects.get(id=command.role_id)
        except Role.DoesNotExist:
            raise NotFoundError(f"Role with ID {command.role_id} not found")

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
                RoleManagementPermissions.MANAGE.
            NotFoundError: If the role does not exist.
        """
        self._authorize_role_administration(actor_permissions)

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise NotFoundError(f"Role with ID {role_id} not found")

        role.delete()
