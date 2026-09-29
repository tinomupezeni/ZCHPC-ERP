"""
AUD-01 F8: department administration requires hr.department.manage.

Before F8, DepartmentService had no authorization at all and the department
routes relied on RBACMiddleware's coarse "holds anything in hr" gate, so an
actor holding only hr.employee.view could rename or delete a department and
make themselves its head - the relationship procurement's department-head
approval authority is built on (Department.head).

Now every mutation (create, update including head, delete) requires
DepartmentManagementPermissions.MANAGE, checked in the service before the
department is loaded. Reads are unchanged. No role is granted the capability
by name; wildcards and superusers satisfy it through the existing Permission
semantics.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.authorization import (
    DepartmentManagementPermissions,
    RoleManagementPermissions,
)
from modules.hr.application.services import (
    CreateDepartmentCommand,
    DepartmentService,
    UpdateDepartmentCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()
MANAGE = DepartmentManagementPermissions.MANAGE
DEPARTMENTS_URL = "/api/v2/hr/departments/"
_numbers = count(84001)


def department_url(department_id):
    return f"{DEPARTMENTS_URL}{department_id}/"


def make_employee(label, *permissions):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="EmployeePass123!")
    role = Role.objects.create(name=f"ROLE_{label}_{n}", permissions=list(permissions))
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email,
        employee_id=f"EMP{n}", role=role,
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def actor_client(*permissions):
    employee = make_employee("Actor", *permissions)
    return client_for(employee.user), employee


def make_department(head=None):
    n = next(_numbers)
    return Department.objects.create(name=f"Dept {n}", description="original", head=head)


def department_service():
    return DepartmentService(
        department_repository=DjangoDepartmentRepository(),
        employee_repository=DjangoEmployeeRepository(),
    )


def assert_denied(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, getattr(response, "data", response)
    assert response.data["code"] == "DEPARTMENT_ADMINISTRATION_NOT_AUTHORIZED"


def assert_unchanged(department, head_id):
    department.refresh_from_db()
    assert department.name.startswith("Dept ")
    assert department.description == "original"
    assert department.head_id == head_id


# =============================================================================
# Actors without hr.department.manage are refused every mutation
# =============================================================================


@pytest.mark.parametrize(
    "permissions",
    [
        ["hr.employee.view"],
        [RoleManagementPermissions.MANAGE],
        ["hr.employee.view", "hr.employee.create", "hr.employee.manage_assignments"],
        ["hr.department.view"],
    ],
    ids=["employee-view", "role-manage", "employee-admin", "department-view"],
)
class TestActorsWithoutTheCapability:
    def test_cannot_create(self, permissions):
        client, _ = actor_client(*permissions)
        response = client.post(DEPARTMENTS_URL, {"name": "Smuggled F8"}, format="json")
        assert_denied(response)
        assert not Department.objects.filter(name="Smuggled F8").exists()

    def test_cannot_rename_or_redescribe(self, permissions):
        client, _ = actor_client(*permissions)
        existing_head = make_employee("Head")
        department = make_department(head=existing_head)
        for method in (client.patch, client.put):
            response = method(
                department_url(department.id),
                {"name": "Renamed", "description": "changed"},
                format="json",
            )
            assert_denied(response)
        assert_unchanged(department, existing_head.id)

    def test_cannot_change_the_head(self, permissions):
        """The original F8 repro: make oneself head of someone else's department."""
        client, attacker = actor_client(*permissions)
        existing_head = make_employee("Head")
        department = make_department(head=existing_head)

        response = client.patch(
            department_url(department.id), {"head_id": attacker.id}, format="json"
        )

        assert_denied(response)
        assert_unchanged(department, existing_head.id)
        assert not Department.objects.filter(head_id=attacker.id).exists()

    def test_cannot_delete(self, permissions):
        client, _ = actor_client(*permissions)
        department = make_department()
        assert_denied(client.delete(department_url(department.id)))
        assert Department.objects.filter(id=department.id).exists()


# =============================================================================
# Holders of the capability (directly, by wildcard, or as superuser)
# =============================================================================


def _full_lifecycle(client, new_head):
    created = client.post(DEPARTMENTS_URL, {"name": f"Created {next(_numbers)}"}, format="json")
    assert created.status_code == status.HTTP_201_CREATED, created.data
    department_id = created.data["id"]

    updated = client.patch(
        department_url(department_id),
        {"name": f"Renamed {next(_numbers)}", "description": "updated", "head_id": new_head.id},
        format="json",
    )
    assert updated.status_code == status.HTTP_200_OK, updated.data
    department = Department.objects.get(id=department_id)
    assert department.description == "updated"
    assert department.head_id == new_head.id

    deleted = client.delete(department_url(department_id))
    assert deleted.status_code == status.HTTP_204_NO_CONTENT, getattr(deleted, "data", deleted)
    assert not Department.objects.filter(id=department_id).exists()


class TestActorsWithTheCapability:
    @pytest.mark.parametrize("permissions", [[MANAGE], ["hr.department.*"], ["hr.*"], ["*"]])
    def test_capability_or_wildcard_can_create_update_assign_head_and_delete(self, permissions):
        client, _ = actor_client(*permissions)
        _full_lifecycle(client, make_employee("NewHead"))

    def test_superuser_without_an_employee_profile_can_administer_departments(self):
        superuser = User.objects.create_superuser(
            email=f"root{next(_numbers)}@zchpc.test", password="RootPass123!"
        )
        _full_lifecycle(client_for(superuser), make_employee("NewHead"))

    def test_existing_delete_constraint_still_applies(self):
        """Authorization does not bypass the domain rule against deleting a staffed department."""
        client, _ = actor_client(MANAGE)
        department = make_department()
        staff = make_employee("Staff")
        Employees.objects.filter(pk=staff.pk).update(department=department)

        response = client.delete(department_url(department.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "DEPARTMENT_HAS_EMPLOYEES"
        assert Department.objects.filter(id=department.id).exists()


# =============================================================================
# Ordering, reads, spoofing, and the service boundary itself
# =============================================================================


class TestAuthorizationOrderingAndBoundaries:
    def test_authorization_is_checked_before_the_department_is_looked_up(self):
        without, _ = actor_client("hr.employee.view")
        with_capability, _ = actor_client(MANAGE)
        missing = department_url(999999)

        assert_denied(without.patch(missing, {"name": "X"}, format="json"))
        assert_denied(without.delete(missing))
        assert with_capability.patch(missing, {"name": "X"}, format="json").status_code == 404
        assert with_capability.delete(missing).status_code == 404

    def test_reads_still_need_only_hr_module_access(self):
        client, _ = actor_client("hr.employee.view")
        department = make_department()
        assert client.get(DEPARTMENTS_URL).status_code == status.HTTP_200_OK
        assert client.get(department_url(department.id)).status_code == status.HTTP_200_OK

    def test_actor_identity_in_the_body_is_ignored(self):
        """Naming a capability holder as the actor in the payload changes nothing."""
        client, attacker = actor_client("hr.employee.view")
        _, manager = actor_client(MANAGE)
        existing_head = make_employee("Head")
        department = make_department(head=existing_head)
        spoof = {
            "actor_id": manager.id, "employee_id": manager.id,
            "user_id": str(manager.user_id), "actor_employee_id": manager.id,
        }

        assert_denied(client.post(DEPARTMENTS_URL, {"name": "Spoofed F8", **spoof}, format="json"))
        assert_denied(client.patch(
            department_url(department.id), {"head_id": attacker.id, **spoof}, format="json"
        ))
        assert_denied(client.generic(
            "DELETE", department_url(department.id), data='{"actor_id": %d}' % manager.id,
            content_type="application/json",
        ))
        assert not Department.objects.filter(name="Spoofed F8").exists()
        assert_unchanged(department, existing_head.id)

    @pytest.mark.parametrize("actor_permissions", [PermissionSet.empty(), None])
    def test_service_refuses_an_actor_without_the_capability(self, actor_permissions):
        service = department_service()
        department = make_department()

        with pytest.raises(AuthorizationError) as create:
            service.create_department(CreateDepartmentCommand(name="Direct F8"), actor_permissions)
        with pytest.raises(AuthorizationError):
            service.update_department(
                UpdateDepartmentCommand(department_id=department.id, name="Direct rename"),
                actor_permissions,
            )
        with pytest.raises(AuthorizationError):
            service.delete_department(department.id, actor_permissions)

        assert create.value.code == "DEPARTMENT_ADMINISTRATION_NOT_AUTHORIZED"
        assert not Department.objects.filter(name="Direct F8").exists()
        assert_unchanged(department, None)

    def test_service_defaults_to_no_permissions_when_called_without_an_actor(self):
        with pytest.raises(AuthorizationError):
            department_service().create_department(CreateDepartmentCommand(name="No actor F8"))
