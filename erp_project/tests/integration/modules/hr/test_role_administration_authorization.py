"""
Regression tests for REM-05: the HR Roles API allowed any authenticated
actor holding any hr.* permission (e.g. hr.employee.view) to create roles,
and to rewrite ANY role's permissions - including their own, another
role's, or the real ADMIN role's - with no authorization beyond
IsAuthenticated + RBACMiddleware's coarse "does this role hold anything in
the hr module" gate. A previous investigation proved this by runtime test:
a low-privilege actor self-granted "*" on their own role, then immediately
used it (via the already-fixed REM-01 boundary) to escalate their
Employees.role_id to ADMIN.

Remediation: modules.hr.application.services.role_service.RoleService now
requires RoleManagementPermissions.MANAGE ("hr.role.manage",
modules.hr.application.authorization.permissions) before create/update/
delete on a Role is allowed to proceed - the boundary this file's tests
exist to prove closes the exact chain above, and that it composes
correctly with REM-01's separate EmployeeManagementPermissions
.MANAGE_ASSIGNMENTS boundary rather than silently subsuming it.

Two authentication styles are used, matching REM-01's own convention:

- Direct RoleService calls (no HTTP at all): proves the *application
  layer* itself rejects an unauthorized actor, independent of whatever a
  future second HTTP entry point might do.
- APIClient + real JWT, through the full URL routing + RBACMiddleware +
  view + service chain: proves the real, deployed request path behaves
  correctly, including for a superuser with no linked Employees record at
  all (AUD-01 found such an account live).
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.authorization import (
    EmployeeManagementPermissions,
    RoleManagementPermissions,
)
from modules.hr.application.services.role_service import (
    CreateRoleCommand,
    RoleService,
    UpdateRoleCommand,
)
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()


def roles_list_url():
    return "/api/v2/hr/roles/"


def role_url(role_id):
    return f"/api/v2/hr/roles/{role_id}/"


def employee_url(employee_id):
    return f"/api/v2/hr/employees/{employee_id}/"


def make_role(name, permissions):
    return Role.objects.create(name=name, display_name=name.title(), permissions=permissions)


def make_employee(first_name, surname, suffix, role=None):
    user = User.objects.create_user(
        email=f"{first_name.lower()}.{surname.lower()}{suffix}@zchpc.test",
        password="EmployeePass123!",
    )
    return Employees.objects.create(
        user=user,
        first_name=first_name,
        surname=surname,
        email=f"{first_name.lower()}.{surname.lower()}{suffix}@zchpc.test",
        employee_id=f"EMP{suffix}",
        role=role,
    )


def jwt_client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


# =============================================================================
# Application-layer: RoleService rejects an unauthorized actor directly
# =============================================================================


class TestServiceLayerRejectsUnauthorizedActor:
    """
    No HTTP involved at all - proves the boundary lives in RoleService
    itself, not only in the view, so a future second entry point (another
    view, a management command, a script) inherits the same protection.
    """

    def test_create_role_without_permission_raises(self):
        with pytest.raises(AuthorizationError) as exc_info:
            RoleService().create_role(
                CreateRoleCommand(name="SHOULD_NOT_EXIST", permissions=["*"]),
                actor_permissions=PermissionSet.from_list(["hr.employee.view"]),
            )
        assert exc_info.value.code == "ROLE_ADMINISTRATION_NOT_AUTHORIZED"
        assert not Role.objects.filter(name="SHOULD_NOT_EXIST").exists()

    def test_update_role_without_permission_raises(self):
        role = make_role("SVC_TARGET", ["hr.employee.view"])
        with pytest.raises(AuthorizationError):
            RoleService().update_role(
                UpdateRoleCommand(role_id=role.id, permissions=["*"], permissions_provided=True),
                actor_permissions=PermissionSet.empty(),
            )
        role.refresh_from_db()
        assert role.permissions == ["hr.employee.view"]

    def test_delete_role_without_permission_raises(self):
        role = make_role("SVC_DELETE_TARGET", [])
        with pytest.raises(AuthorizationError):
            RoleService().delete_role(role.id, actor_permissions=PermissionSet.empty())
        assert Role.objects.filter(id=role.id).exists()

    def test_update_role_with_permission_succeeds(self):
        role = make_role("SVC_TARGET_2", [])
        updated = RoleService().update_role(
            UpdateRoleCommand(role_id=role.id, permissions=["hr.role.manage"], permissions_provided=True),
            actor_permissions=PermissionSet.from_list([RoleManagementPermissions.MANAGE]),
        )
        assert updated.permissions == ["hr.role.manage"]


# =============================================================================
# HTTP-layer: the required negative cases, through the real request path
# =============================================================================


class TestOrdinaryHrCapableActorCannotAdministerRoles:
    """
    An actor holding only hr.employee.view - enough to pass RBACMiddleware's
    coarse "hr" module gate, nothing more - attempts every operation listed
    as a required negative case.
    """

    def _low_priv_client_and_role(self, suffix):
        role = make_role(f"LOW_PRIV_{suffix}", ["hr.employee.view"])
        employee = make_employee("Low", "Priv", suffix, role=role)
        return jwt_client_for(employee.user), role, employee

    def test_cannot_modify_own_role_permissions(self):
        client, role, _ = self._low_priv_client_and_role("A001")
        response = client.patch(role_url(role.id), {"permissions": ["hr.employee.view", "extra"]}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "ROLE_ADMINISTRATION_NOT_AUTHORIZED"
        role.refresh_from_db()
        assert role.permissions == ["hr.employee.view"]

    def test_cannot_modify_another_roles_permissions(self):
        client, _, _ = self._low_priv_client_and_role("A002")
        other_role = make_role("OTHER_ROLE_A002", ["procurement.purchase_request.view"])
        response = client.patch(role_url(other_role.id), {"permissions": ["*"]}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        other_role.refresh_from_db()
        assert other_role.permissions == ["procurement.purchase_request.view"]

    def test_cannot_grant_self_manage_assignments(self):
        client, role, _ = self._low_priv_client_and_role("A003")
        response = client.patch(
            role_url(role.id),
            {"permissions": ["hr.employee.view", EmployeeManagementPermissions.MANAGE_ASSIGNMENTS]},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        role.refresh_from_db()
        assert EmployeeManagementPermissions.MANAGE_ASSIGNMENTS not in role.permissions

    def test_cannot_grant_self_role_management_capability(self):
        """The bootstrap case: cannot grant themselves the very capability that would let them do this legitimately."""
        client, role, _ = self._low_priv_client_and_role("A004")
        response = client.patch(
            role_url(role.id),
            {"permissions": ["hr.employee.view", RoleManagementPermissions.MANAGE]},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        role.refresh_from_db()
        assert RoleManagementPermissions.MANAGE not in role.permissions

    def test_cannot_grant_self_wildcard(self):
        client, role, _ = self._low_priv_client_and_role("A005")
        response = client.patch(role_url(role.id), {"permissions": ["*"]}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        role.refresh_from_db()
        assert role.permissions == ["hr.employee.view"]

    def test_cannot_modify_a_privileged_admin_role(self):
        client, _, _ = self._low_priv_client_and_role("A006")
        admin_role = make_role("ADMIN_A006", ["*"])
        before = list(admin_role.permissions)

        response = client.patch(
            role_url(admin_role.id), {"permissions": ["*", "extra.injected"]}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        admin_role.refresh_from_db()
        assert admin_role.permissions == before

    def test_cannot_strip_permissions_from_a_privileged_admin_role(self):
        client, _, _ = self._low_priv_client_and_role("A007")
        admin_role = make_role("ADMIN_A007", ["*"])

        response = client.patch(role_url(admin_role.id), {"permissions": []}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        admin_role.refresh_from_db()
        assert admin_role.permissions == ["*"]

    def test_cannot_create_a_role_at_all(self):
        client, _, _ = self._low_priv_client_and_role("A008")
        response = client.post(
            roles_list_url(), {"name": "CREATED_BY_LOW_PRIV_A008", "permissions": ["*"]}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert not Role.objects.filter(name="CREATED_BY_LOW_PRIV_A008").exists()

    def test_cannot_delete_a_role(self):
        client, _, _ = self._low_priv_client_and_role("A009")
        victim_role = make_role("DELETE_TARGET_A009", [])
        response = client.delete(role_url(victim_role.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert Role.objects.filter(id=victim_role.id).exists()

    def test_hr_employee_view_alone_does_not_authorize_role_administration(self):
        """Explicit statement of the boundary: this specific narrow permission is not sufficient by itself."""
        client, role, _ = self._low_priv_client_and_role("A010")
        response = client.patch(role_url(role.id), {"description": "harmless metadata edit"}, format="json")
        # Metadata-only edits are gated identically to permission edits in this
        # implementation (REM-05 treats role administration as one capability,
        # per the confirmed "HR administers roles" requirement) - so this is
        # also rejected, proving hr.employee.view confers no role-admin
        # capability of any kind, not just no permissions-editing capability.
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_can_still_list_roles(self):
        """Read access is unaffected - only mutation is gated."""
        client, _, _ = self._low_priv_client_and_role("A011")
        response = client.get(roles_list_url())
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_a_broader_ordinary_hr_permission_set_still_does_not_authorize_role_administration(self):
        """
        Not just the single narrowest permission (hr.employee.view) - an
        actor with a realistic, broader "ordinary HR" grant (several
        hr.employee.* capabilities, none of them hr.role.manage) must still
        be refused. Role administration is a distinct capability, not a
        side effect of accumulating enough ordinary hr.* permissions.
        """
        role = make_role(
            "ORDINARY_HR_A012",
            ["hr.employee.view", "hr.employee.create", "hr.department.view"],
        )
        employee = make_employee("Ordinary", "Hr", "A012", role=role)
        client = jwt_client_for(employee.user)

        response = client.patch(role_url(role.id), {"permissions": [RoleManagementPermissions.MANAGE]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        role.refresh_from_db()
        assert RoleManagementPermissions.MANAGE not in role.permissions


# =============================================================================
# Wildcard semantics: explicitly pinned, not changed
# =============================================================================


class TestWildcardSemanticsArePinnedNotChanged:
    """
    Permission.matches() treats an app-level wildcard (e.g. "hr.*") as
    matching every capability under that prefix, including
    hr.role.manage. This is the platform's existing, global, intentional
    wildcard semantic (already exercised by
    tests/integration/modules/identity/test_rbac_route_access.py's
    test_module_wildcard_semantics_are_preserved for the coarse-gate
    layer) - REM-05 does not change it and must not rely on it changing.
    This test makes the consequence explicit for hr.role.manage
    specifically, so a future change to that global semantic would be
    caught here too, rather than only being noticed as a side effect
    somewhere else.

    The role fixture below represents the scenario named in migration
    0019's own docstring - a role that ended up with a legacy hr.*
    grant from 0017, not a role this repository actually seeds today
    (no live/default role currently holds hr.* - see AUD-01 R1 and the
    REM-05 review investigation). It is not a claim that this is the
    live state of any real role.
    """

    def test_hr_wildcard_satisfies_hr_role_manage_at_the_permission_set_level(self):
        permissions = PermissionSet.from_list(["hr.*"])
        assert permissions.has_permission(RoleManagementPermissions.MANAGE) is True

    def test_a_role_holding_only_the_legacy_hr_wildcard_can_administer_roles_end_to_end(self):
        legacy_role = make_role("LEGACY_HR_WILDCARD_W001", ["hr.*"])
        employee = make_employee("Legacy", "Wildcard", "W001", role=legacy_role)
        client = jwt_client_for(employee.user)
        target = make_role("TARGET_W001", [])

        response = client.patch(role_url(target.id), {"permissions": ["hr.employee.view"]}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.permissions == ["hr.employee.view"]


# =============================================================================
# HTTP-layer: the required positive cases
# =============================================================================


class TestAuthorizedHrRoleAdministratorCanAdministerRoles:
    def _hr_admin_client(self, suffix, role_name="HR_ROLE_ADMIN"):
        role = make_role(f"{role_name}_{suffix}", [RoleManagementPermissions.MANAGE])
        employee = make_employee("Helen", "Admin", suffix, role=role)
        return jwt_client_for(employee.user)

    def test_can_create_a_role(self):
        client = self._hr_admin_client("B001")
        response = client.post(
            roles_list_url(),
            {"name": "NEW_ROLE_B001", "display_name": "New Role", "permissions": ["procurement.purchase_request.view"]},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Role.objects.filter(name="NEW_ROLE_B001").exists()

    def test_can_update_role_metadata(self):
        client = self._hr_admin_client("B002")
        target = make_role("METADATA_TARGET_B002", [])
        response = client.patch(role_url(target.id), {"description": "Updated by HR admin"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.description == "Updated by HR admin"

    def test_can_update_role_permissions(self):
        client = self._hr_admin_client("B003")
        target = make_role("PERM_TARGET_B003", [])
        response = client.patch(
            role_url(target.id), {"permissions": ["procurement.purchase_request.view"]}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.permissions == ["procurement.purchase_request.view"]

    def test_can_delete_a_role(self):
        client = self._hr_admin_client("B004")
        target = make_role("DELETE_TARGET_B004", [])
        response = client.delete(role_url(target.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT, response.data
        assert not Role.objects.filter(id=target.id).exists()

    def test_the_seeded_human_resources_role_itself_works_end_to_end(self):
        """
        Not a synthetic role - the actual HUMAN_RESOURCES role this
        remediation's migration creates, proving the seeded role is not
        just present in the database but functionally correct.
        """
        hr_role = Role.objects.get(name="HUMAN_RESOURCES")
        assert hr_role.permissions == [RoleManagementPermissions.MANAGE]

        hr_employee = make_employee("Real", "HrAdmin", "B005", role=hr_role)
        client = jwt_client_for(hr_employee.user)

        target = make_role("TARGET_FOR_REAL_HR_B005", [])
        response = client.patch(role_url(target.id), {"permissions": ["hr.employee.view"]}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.permissions == ["hr.employee.view"]

    def test_a_non_superuser_employee_holding_bare_wildcard_can_administer_roles(self):
        """
        Full-access ("*") semantics are unchanged by this remediation - a
        role holding it (not a superuser account, an ordinary employee
        whose role happens to carry "*") continues to satisfy every
        capability check, including this new one, exactly as it already
        did for every other permission check in the system.
        """
        full_access_role = make_role("FULL_ACCESS_B006", ["*"])
        employee = make_employee("Fae", "FullAccess", "B006", role=full_access_role)
        client = jwt_client_for(employee.user)

        target = make_role("TARGET_B006", [])
        response = client.patch(role_url(target.id), {"permissions": ["hr.employee.view"]}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.permissions == ["hr.employee.view"]


class TestSuperuserRetainsExistingAccess:
    def test_superuser_with_no_employee_profile_can_administer_roles(self):
        """
        AUD-01 found a live superuser account with no linked Employees
        record at all. REM-05 must not regress that account's ability to
        reach genuinely administrative functionality.
        """
        superuser = User.objects.create_superuser(email="rem05.superuser@zchpc.test", password="x")
        client = jwt_client_for(superuser)
        target = make_role("SUPERUSER_TARGET", [])

        response = client.patch(role_url(target.id), {"permissions": ["*"]}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.permissions == ["*"]


# =============================================================================
# REM-01 / REM-05 composition: the two capabilities remain properly separate
# =============================================================================


class TestRoleAdministrationDoesNotImplyEmployeeAssignmentAuthority:
    """
    hr.role.manage and hr.employee.manage_assignments are deliberately
    distinct capabilities (REM-01 and REM-05 respectively). An actor
    holding one must not be treated as holding the other.
    """

    def test_hr_role_administrator_still_cannot_reassign_employee_roles(self):
        hr_admin_role = make_role("HR_ADMIN_ONLY", [RoleManagementPermissions.MANAGE])
        hr_admin = make_employee("Helen", "RoleOnly", "C001", role=hr_admin_role)
        client = jwt_client_for(hr_admin.user)

        admin_role = make_role("ADMIN_C001", ["*"])
        response = client.patch(employee_url(hr_admin.id), {"role_id": admin_role.id}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        hr_admin.refresh_from_db()
        assert hr_admin.role_id == hr_admin_role.id

    def test_employee_assignment_administrator_still_cannot_administer_roles(self):
        assignment_admin_role = make_role(
            "ASSIGNMENT_ADMIN_ONLY", [EmployeeManagementPermissions.MANAGE_ASSIGNMENTS]
        )
        actor = make_employee("Andy", "AssignOnly", "C002", role=assignment_admin_role)
        client = jwt_client_for(actor.user)

        response = client.patch(
            role_url(assignment_admin_role.id), {"permissions": ["*"]}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assignment_admin_role.refresh_from_db()
        assert assignment_admin_role.permissions == [EmployeeManagementPermissions.MANAGE_ASSIGNMENTS]


# =============================================================================
# The complete escalation chain, reproduced end to end, must remain blocked
# =============================================================================


class TestCompleteEscalationChainRemainsBlocked:
    """
    Direct reproduction of the exact chain the original investigation
    demonstrated: attempt Role.permissions mutation (must be rejected),
    then attempt Employee role mutation with the same, still-unescalated
    session (must also remain rejected, per REM-01).
    """

    def test_low_privilege_actor_cannot_complete_the_escalation_chain(self):
        low_priv_role = make_role("CHAIN_LOW_PRIV", ["hr.employee.view"])
        attacker = make_employee("Chain", "Attacker", "D001", role=low_priv_role)
        client = jwt_client_for(attacker.user)
        admin_role = make_role("ADMIN_D001", ["*"])

        # Step 1: attempt to self-grant "*" via the Roles API.
        step1 = client.patch(role_url(low_priv_role.id), {"permissions": ["*"]}, format="json")
        assert step1.status_code == status.HTTP_403_FORBIDDEN, step1.data
        low_priv_role.refresh_from_db()
        assert low_priv_role.permissions == ["hr.employee.view"]

        # Step 2: using the SAME, still-unescalated session, attempt the
        # employee-role escalation REM-01 protects.
        step2 = client.patch(employee_url(attacker.id), {"role_id": admin_role.id}, format="json")
        assert step2.status_code == status.HTTP_403_FORBIDDEN, step2.data
        attacker.refresh_from_db()
        assert attacker.role_id == low_priv_role.id
        assert attacker.role_id != admin_role.id

    def test_low_privilege_actor_cannot_complete_the_escalation_chain_via_the_narrow_capability(self):
        """
        Same chain as above, but step 1 targets hr.role.manage specifically
        rather than "*" - the more surgical version of the same attack,
        proving the boundary isn't only effective against the broadest
        possible self-grant.
        """
        low_priv_role = make_role("CHAIN_LOW_PRIV_NARROW", ["hr.employee.view"])
        attacker = make_employee("Chain", "AttackerNarrow", "D002", role=low_priv_role)
        client = jwt_client_for(attacker.user)
        admin_role = make_role("ADMIN_D002", ["*"])

        # Step 1: attempt to self-grant exactly hr.role.manage, not "*".
        step1 = client.patch(
            role_url(low_priv_role.id),
            {"permissions": ["hr.employee.view", RoleManagementPermissions.MANAGE]},
            format="json",
        )
        assert step1.status_code == status.HTTP_403_FORBIDDEN, step1.data
        low_priv_role.refresh_from_db()
        assert low_priv_role.permissions == ["hr.employee.view"]
        assert RoleManagementPermissions.MANAGE not in low_priv_role.permissions

        # Step 2: using the SAME, still-unescalated session, attempt the
        # employee-role escalation REM-01 protects.
        step2 = client.patch(employee_url(attacker.id), {"role_id": admin_role.id}, format="json")
        assert step2.status_code == status.HTTP_403_FORBIDDEN, step2.data
        attacker.refresh_from_db()
        assert attacker.role_id == low_priv_role.id
        assert attacker.role_id != admin_role.id
