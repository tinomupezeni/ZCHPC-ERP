"""
AUD-01 final review findings F1 and F2.

F1 - role administration had no permission ceiling: an actor holding only
hr.role.manage could PATCH their own role to ["*"] and, on the same token,
reach payroll data, deactivate ADMINs and strip the ADMIN role. Now a role may
only be written with permissions the actor holds, and only changed or deleted
by an actor holding everything it currently grants (RoleService, via
PermissionSet.covers).

F2 - role/department assignment ignored the target's current authority: an
actor with hr.employee.manage_assignments could demote an ADMIN, or move them
to another department, as long as the new role was within the actor's own
ceiling. Now changing an existing employee's role or department also needs the
actor to hold every permission the target currently holds
(EmployeeAuthorizationPolicy.authorize_assignment_target).
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.authorization import (
    EmployeeManagementPermissions as EMP,
    RoleManagementPermissions,
)
from modules.hr.application.services import (
    CreateRoleCommand,
    EmployeeService,
    RoleService,
    UpdateEmployeeCommand,
    UpdateRoleCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError, ValidationError

pytestmark = pytest.mark.django_db

User = get_user_model()
MANAGE_ROLES = RoleManagementPermissions.MANAGE
_numbers = count(81001)


def make_role(label, permissions):
    return Role.objects.create(name=f"{label}_{next(_numbers)}", permissions=list(permissions))


def make_employee(label, *permissions, role=None, superuser=False, department=None):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    create = User.objects.create_superuser if superuser else User.objects.create_user
    user = create(email=email, password="EmployeePass123!")
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}",
        role=role or make_role(f"ROLE_{label}", permissions), department=department,
    )


def make_department():
    return Department.objects.create(name=f"Dept {next(_numbers)}")


def client_for(employee_or_user):
    user = getattr(employee_or_user, "user", employee_or_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def role_url(role_id):
    return f"/api/v2/hr/roles/{role_id}/"


def employee_url(employee_id):
    return f"/api/v2/hr/employees/{employee_id}/"


def bank_url(employee):
    return f"/api/v2/payroll/bank-accounts/{employee.uuid}/"


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


# =============================================================================
# F1 - role permission ceiling
# =============================================================================


class TestRoleManagerCannotGrantWhatTheyDoNotHold:
    def test_original_attack_chain_is_blocked(self):
        """hr.role.manage -> PATCH own role to ["*"] -> privileged payroll access."""
        attacker = make_employee("Mallory", MANAGE_ROLES)
        victim = make_employee("Victim")
        client = client_for(attacker)
        assert client.get(bank_url(victim)).status_code == status.HTTP_403_FORBIDDEN

        response = client.patch(role_url(attacker.role_id), {"permissions": ["*"]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "ROLE_PERMISSIONS_EXCEED_ACTOR_AUTHORITY"
        attacker.role.refresh_from_db()
        assert attacker.role.permissions == [MANAGE_ROLES]
        # Same token, still no payroll access.
        assert client.get(bank_url(victim)).status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "granted",
        [["*"], ["payroll.*"], ["hr.*"], [EMP.MANAGE_ASSIGNMENTS], ["h*"], ["?"], ["[a-z]*"]],
    )
    def test_cannot_add_permissions_to_own_role(self, granted):
        attacker = make_employee("Mallory", MANAGE_ROLES)
        response = client_for(attacker).patch(
            role_url(attacker.role_id), {"permissions": [MANAGE_ROLES, *granted]}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        attacker.role.refresh_from_db()
        assert attacker.role.permissions == [MANAGE_ROLES]

    def test_cannot_grant_unheld_permissions_to_another_role(self):
        attacker = make_employee("Mallory", MANAGE_ROLES)
        other = make_role("OTHER", [])
        response = client_for(attacker).patch(
            role_url(other.id), {"permissions": ["payroll.bank.view"]}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        other.refresh_from_db()
        assert other.permissions == []

    def test_cannot_create_a_role_with_unheld_permissions(self):
        attacker = make_employee("Mallory", MANAGE_ROLES)
        response = client_for(attacker).post(
            "/api/v2/hr/roles/", {"name": "SMUGGLED_F1", "permissions": ["*"]}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert not Role.objects.filter(name="SMUGGLED_F1").exists()

    def test_cannot_modify_rename_or_delete_a_more_privileged_role(self):
        attacker = make_employee("Mallory", MANAGE_ROLES)
        admin_role = make_role("ADMIN", ["*"])
        client = client_for(attacker)

        strip = client.patch(role_url(admin_role.id), {"permissions": []}, format="json")
        rename = client.patch(role_url(admin_role.id), {"name": "NOT_ADMIN"}, format="json")
        delete = client.delete(role_url(admin_role.id))

        for response in (strip, rename, delete):
            assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
            assert response.data["code"] == "ROLE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        admin_role.refresh_from_db()
        assert admin_role.permissions == ["*"]
        assert admin_role.name.startswith("ADMIN_")

    @pytest.mark.parametrize("permissions", ["portal.*", {"a": "*"}, [""], ["  "], [None], ["*", 3]])
    def test_permissions_must_be_a_list_of_non_empty_strings(self, permissions):
        """A bare string was stored as-is and read per character ("portal.*" -> "*")."""
        admin = make_employee("Admin", "*")
        target = make_role("TARGET", ["portal.notification.view"])
        response = client_for(admin).patch(role_url(target.id), {"permissions": permissions}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "INVALID_ROLE_PERMISSIONS"
        target.refresh_from_db()
        assert target.permissions == ["portal.notification.view"]

    def test_service_layer_enforces_the_ceiling_without_http(self):
        manager = PermissionSet.from_list([MANAGE_ROLES])
        role = make_role("SVC", [MANAGE_ROLES])
        with pytest.raises(AuthorizationError) as exc:
            RoleService().update_role(
                UpdateRoleCommand(role_id=role.id, permissions=["*"], permissions_provided=True),
                actor_permissions=manager,
            )
        assert exc.value.code == "ROLE_PERMISSIONS_EXCEED_ACTOR_AUTHORITY"
        with pytest.raises(AuthorizationError):
            RoleService().create_role(CreateRoleCommand(name="SVC_NEW", permissions=["*"]), manager)
        with pytest.raises(ValidationError):
            RoleService().create_role(CreateRoleCommand(name="SVC_STR", permissions="*"), manager)
        role.refresh_from_db()
        assert role.permissions == [MANAGE_ROLES]


class TestRoleAdministrationWithinTheCeilingStillWorks:
    def test_can_grant_preserve_and_narrow_held_permissions(self):
        manager = make_employee("Helen", MANAGE_ROLES, "procurement.purchase_request.view")
        target = make_role("TARGET", [])
        client = client_for(manager)

        grant = client.patch(
            role_url(target.id), {"permissions": ["procurement.purchase_request.view"]}, format="json"
        )
        assert grant.status_code == status.HTTP_200_OK, grant.data
        created = client.post("/api/v2/hr/roles/", {"name": "WITHIN_F1", "permissions": [MANAGE_ROLES]}, format="json")
        assert created.status_code == status.HTTP_201_CREATED, created.data
        assert client.delete(role_url(target.id)).status_code == status.HTTP_204_NO_CONTENT
        # Own role: resubmitting the same set, then narrowing it, is allowed.
        own = [MANAGE_ROLES, "procurement.purchase_request.view"]
        assert client.patch(role_url(manager.role_id), {"permissions": own}, format="json").status_code == 200
        assert client.patch(role_url(manager.role_id), {"permissions": [MANAGE_ROLES]}, format="json").status_code == 200
        # Having narrowed itself, it no longer covers roles granting more.
        wider = make_role("WIDER", ["procurement.purchase_request.view"])
        assert client.delete(role_url(wider.id)).status_code == status.HTTP_403_FORBIDDEN

    def test_app_wildcard_holder_can_grant_within_it_only(self):
        manager = make_employee("Legacy", "hr.*")
        target = make_role("TARGET", [])
        client = client_for(manager)
        assert client.patch(role_url(target.id), {"permissions": ["hr.employee.view", "hr.*"]}, format="json").status_code == 200
        assert client.patch(role_url(target.id), {"permissions": ["payroll.bank.view"]}, format="json").status_code == 403
        assert client.patch(role_url(target.id), {"permissions": ["*"]}, format="json").status_code == 403

    @pytest.mark.parametrize("superuser", [False, True])
    def test_full_access_actor_can_grant_wildcard_and_manage_admin_role(self, superuser):
        actor = make_employee("Root", "*", superuser=superuser)
        admin_role = make_role("ADMIN", ["*"])
        target = make_role("TARGET", [])
        client = client_for(actor)
        assert client.patch(role_url(target.id), {"permissions": ["*"]}, format="json").status_code == 200
        assert client.patch(role_url(admin_role.id), {"description": "maintained"}, format="json").status_code == 200
        assert client.delete(role_url(target.id)).status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# F2 - target authority on role/department assignment
# =============================================================================


def clerk(*extra):
    """A lower-authority actor holding the assignment capability."""
    return make_employee("Clerk", EMP.MANAGE_ASSIGNMENTS, "hr.employee.view", *extra)


class TestLowerAuthorityActorCannotReassignAHigherTarget:
    def test_clerk_cannot_demote_admin(self):
        actor = clerk()
        admin = make_employee("Admin", "*")
        admin_role_id = admin.role_id
        low = make_role("LOW", ["hr.employee.view"])

        response = client_for(actor).patch(employee_url(admin.id), {"role_id": low.id}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        admin.refresh_from_db()
        assert admin.role_id == admin_role_id

    def test_clerk_cannot_move_admin_between_departments(self):
        actor = clerk()
        home = make_department()
        admin = make_employee("Admin", "*", department=home)

        response = client_for(actor).patch(
            employee_url(admin.id), {"department_id": make_department().id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        admin.refresh_from_db()
        assert admin.department_id == home.id

    def test_clerk_cannot_reassign_a_superuser_linked_employee(self):
        actor = clerk()
        root = make_employee("Root", "hr.employee.view", superuser=True)
        role_id = root.role_id
        response = client_for(actor).patch(
            employee_url(root.id), {"role_id": make_role("LOW", []).id}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        root.refresh_from_db()
        assert root.role_id == role_id

    def test_target_with_any_unheld_permission_is_protected(self):
        """Not a role-name comparison: one permission the actor lacks is enough."""
        actor = clerk()
        peer = make_employee("Peer", "hr.employee.view", "payroll.payslip.view")
        response = client_for(actor).patch(
            employee_url(peer.id), {"department_id": make_department().id}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_actor_identity_comes_from_the_token_not_the_body(self):
        actor = clerk()
        admin = make_employee("Admin", "*")
        role_id = admin.role_id
        low = make_role("LOW", [])
        response = client_for(actor).patch(
            employee_url(admin.id),
            {"role_id": low.id, "actor_id": admin.id, "actor_employee_id": admin.id,
             "user_id": str(admin.user_id), "employee_id": admin.employee_id},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        admin.refresh_from_db()
        assert admin.role_id == role_id

    def test_target_substitution_is_judged_per_target(self):
        """The same request that succeeds on a lower employee fails on the ADMIN."""
        actor = clerk()
        low = make_role("LOW", ["hr.employee.view"])
        junior = make_employee("Junior", "hr.employee.view")
        admin = make_employee("Admin", "*")
        client = client_for(actor)
        assert client.patch(employee_url(junior.id), {"role_id": low.id}, format="json").status_code == 200
        assert client.patch(employee_url(admin.id), {"role_id": low.id}, format="json").status_code == 403

    def test_service_layer_enforces_target_authority_without_http(self):
        admin = make_employee("Admin", "*")
        with pytest.raises(AuthorizationError) as exc:
            employee_service().update_employee(
                UpdateEmployeeCommand(employee_id=admin.id, role_id=make_role("LOW", []).id),
                actor_permissions=PermissionSet.from_list([EMP.MANAGE_ASSIGNMENTS]),
            )
        assert exc.value.code == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"


class TestLegitimateAssignmentsStillWork:
    def test_higher_authority_actor_can_reassign_lower_employee(self):
        actor = clerk()
        junior = make_employee("Junior", "hr.employee.view")
        low = make_role("LOW", [])
        dept = make_department()
        response = client_for(actor).patch(
            employee_url(junior.id), {"role_id": low.id, "department_id": dept.id}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        junior.refresh_from_db()
        assert (junior.role_id, junior.department_id) == (low.id, dept.id)

    @pytest.mark.parametrize("superuser", [False, True])
    def test_full_access_actor_can_demote_and_move_admin(self, superuser):
        actor = make_employee("Root", "*", superuser=superuser)
        admin = make_employee("Admin", "*")
        low = make_role("LOW", [])
        dept = make_department()
        response = client_for(actor).patch(
            employee_url(admin.id), {"role_id": low.id, "department_id": dept.id}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_self_changes_keep_their_existing_rules(self):
        admin = make_employee("Admin", "*")
        low = make_role("LOW", ["hr.employee.view"])
        # Self-demotion and a self department move stay allowed ...
        assert client_for(admin).patch(employee_url(admin.id), {"department_id": make_department().id}, format="json").status_code == 200
        assert client_for(admin).patch(employee_url(admin.id), {"role_id": low.id}, format="json").status_code == 200
        # ... self-escalation stays refused (REM-01).
        actor = clerk()
        response = client_for(actor).patch(employee_url(actor.id), {"role_id": make_role("TOP", ["*"]).id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_SELF_ROLE_ESCALATION"

    def test_resubmitting_a_targets_current_assignment_changes_nothing_and_is_allowed(self):
        """Edit forms send role/department with every save; an unchanged value is not a reassignment."""
        actor = clerk()
        dept = make_department()
        admin = make_employee("Admin", "*", department=dept)
        response = client_for(actor).patch(
            employee_url(admin.id), {"department_id": dept.id}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        admin.refresh_from_db()
        assert admin.department_id == dept.id

    def test_nonexistent_target_is_still_not_found(self):
        response = client_for(clerk()).patch(
            employee_url(999999), {"department_id": make_department().id}, format="json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.data

    def test_nonexistent_target_without_the_capability_is_still_forbidden(self):
        weak = make_employee("Weak", "hr.employee.view")
        response = client_for(weak).patch(employee_url(999999), {"department_id": 1}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


# =============================================================================
# Alternate paths that could change a role or department
# =============================================================================


class TestAlternatePathsCannotReassign:
    def test_identity_user_update_ignores_role_and_department(self):
        actor = make_employee("Ident", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, "hr.employee.view")
        admin = make_employee("Admin", "*", department=make_department())
        before = (admin.role_id, admin.department_id)
        client_for(actor).patch(
            f"/api/v2/auth/users/{admin.user_id}/",
            {"role": make_role("LOW", []).id, "role_id": 1, "department": make_department().id, "department_id": 1},
            format="json",
        )
        admin.refresh_from_db()
        assert (admin.role_id, admin.department_id) == before

    def test_bff_profile_update_ignores_role_and_department(self):
        actor = make_employee("Bff", "bff.employee.edit")
        admin = make_employee("Admin", "*", department=make_department())
        before = (admin.role_id, admin.department_id)
        client_for(actor).put(
            f"/api/v2/bff/employees/{admin.uuid}/",
            {"role_id": make_role("LOW", []).id, "department_id": make_department().id},
            format="json",
        )
        admin.refresh_from_db()
        assert (admin.role_id, admin.department_id) == before
