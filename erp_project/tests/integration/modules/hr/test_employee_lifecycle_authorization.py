"""
Regression tests for REM-01: employee creation, role assignment and
deactivation authorization.

The audit demonstrated this chain with an actor holding only
hr.employee.view:

    POST /hr/employees/ with role_id=<ADMIN>
      -> post_save signal creates a login (password = surname)
      -> log in as the new employee, who resolves to "*"
      -> administer roles, assign ADMIN elsewhere, deactivate others.

Remediation (modules.hr.application.authorization.EmployeeAuthorizationPolicy,
called by EmployeeService):

- creation needs hr.employee.create;
- any role_id (create or update) needs hr.employee.manage_assignments, must
  exist, and may only grant permissions the actor already holds
  (PermissionSet.covers), with self-escalation reported separately;
- deactivation needs hr.employee.deactivate, refuses the actor's own record
  and anyone holding permissions the actor lacks, and disables the linked
  login in the same transaction.

Same two authentication styles as the sibling REM-01/REM-05 files: real JWTs
through RBACMiddleware for the deployed path, and force_authenticate / direct
service calls to prove the application layer holds on its own.
"""

from importlib import import_module
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.hr.api.views.employee_views import (
    EmployeeDetailView,
    EmployeeListCreateView,
    get_employee_service,
)
from modules.hr.application.authorization import (
    EmployeeManagementPermissions as EMP,
    RoleManagementPermissions,
)
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

EMPLOYEES_URL = "/api/v2/hr/employees/"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PASSWORD = "EmployeePass123!"

# EmployeeId accepts only EMP + digits.
_ec_numbers = count(70001)


def employee_url(employee_id):
    return f"/api/v2/hr/employees/{employee_id}/"


def role_url(role_id):
    return f"/api/v2/hr/roles/{role_id}/"


def make_role(name, permissions):
    return Role.objects.create(name=name, display_name=name.title(), permissions=permissions)


def make_employee(first_name, surname, suffix, role=None, department=None, superuser=False):
    email = f"{first_name.lower()}.{surname.lower()}{suffix}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
        user = User.objects.create_user(email=email, password=PASSWORD)
    return Employees.objects.create(
        user=user,
        first_name=first_name,
        surname=surname,
        email=email,
        employee_id=f"EMP{next(_ec_numbers)}",
        role=role,
        department=department,
    )


def actor_with(*permissions, suffix):
    """An employee whose role grants exactly these permissions, plus a JWT client."""
    role = make_role(f"ACTOR_{suffix}", list(permissions))
    employee = make_employee("Actor", "Person", suffix, role=role)
    return jwt_client_for(employee.user), employee


def jwt_client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def new_hire(suffix, **extra):
    return {
        "first_name": "New",
        "surname": f"Hire{suffix}",
        "email": f"new.hire{suffix}@zchpc.test".lower(),
        **extra,
    }


def login(email, password):
    return APIClient().post(LOGIN_URL, {"email": email, "password": password}, format="json")


def login_is_active(employee):
    return User.objects.get(pk=employee.user_id).is_active


def assert_nothing_created(payload):
    assert not Employees.objects.filter(email=payload["email"]).exists()
    assert not User.objects.filter(email=payload["email"]).exists()


# =============================================================================
# A. Employee creation
# =============================================================================


class TestEmployeeCreation:
    def test_unauthenticated_request_is_denied(self):
        payload = new_hire("C01")
        response = APIClient().post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert_nothing_created(payload)

    def test_actor_without_create_capability_is_denied(self):
        client, _ = actor_with("hr.employee.view", suffix="C02")
        payload = new_hire("C02")
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_CREATE_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_actor_with_create_capability_can_create_an_employee(self):
        client, _ = actor_with(EMP.CREATE, suffix="C03")
        department = Department.objects.create(name="Dept-C03")
        # The admin UI's create payload always carries department_id; initial
        # placement is part of creation, not a reassignment.
        payload = new_hire("C03", department_id=department.id)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        created = Employees.objects.get(email=payload["email"])
        assert created.role_id is None
        assert created.department_id == department.id

    def test_privileged_role_id_cannot_ride_along_with_create_capability(self):
        admin_role = make_role("ADMIN_C04", ["*"])
        client, _ = actor_with(EMP.CREATE, suffix="C04")
        payload = new_hire("C04", role_id=admin_role.id)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_any_role_id_needs_manage_assignments(self):
        plain_role = make_role("PLAIN_C05", [])
        client, _ = actor_with(EMP.CREATE, suffix="C05")
        payload = new_hire("C05", role_id=plain_role.id)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_actor_with_manage_assignments_can_assign_a_role_within_their_authority(self):
        target_role = make_role("CLERK_C06", ["procurement.purchase_request.view"])
        client, _ = actor_with(
            EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, "procurement.*", suffix="C06"
        )
        payload = new_hire("C06", role_id=target_role.id)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Employees.objects.get(email=payload["email"]).role_id == target_role.id

    def test_actor_cannot_assign_a_role_beyond_their_authority(self):
        target_role = make_role("FINANCE_C07", ["payroll.run.process"])
        client, _ = actor_with(EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, suffix="C07")
        payload = new_hire("C07", role_id=target_role.id)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ROLE_EXCEEDS_ACTOR_AUTHORITY"
        assert_nothing_created(payload)

    def test_self_role_assignment_via_own_login_email_is_rejected(self):
        """
        modules.hr.signals links a new record to an existing login with the
        same email, so creating a record carrying the actor's own email with
        a role is a self-assignment.
        """
        admin_role = make_role("ADMIN_C08", ["*"])
        client, actor = actor_with(EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, suffix="C08")
        before = Employees.objects.count()
        response = client.post(
            EMPLOYEES_URL,
            {"first_name": "Me", "surname": "Again", "email": actor.user.email.upper(),
             "role_id": admin_role.id},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_SELF_ROLE_ESCALATION"
        assert Employees.objects.count() == before
        actor.refresh_from_db()
        assert actor.role.permissions == [EMP.CREATE, EMP.MANAGE_ASSIGNMENTS]

    def test_invalid_role_id_returns_a_controlled_validation_error(self):
        client, _ = actor_with(EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, suffix="C09")
        payload = new_hire("C09", role_id=987654)
        response = client.post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "INVALID_ROLE"
        assert_nothing_created(payload)

    def test_invalid_role_id_without_capability_is_still_403(self):
        """Capability first: no probing which role ids exist."""
        client, _ = actor_with(EMP.CREATE, suffix="C10")
        response = client.post(EMPLOYEES_URL, new_hire("C10", role_id=987654), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_application_layer_denies_even_when_middleware_is_bypassed(self):
        admin_role = make_role("ADMIN_C11", ["*"])
        _, actor = actor_with("hr.employee.view", suffix="C11")
        payload = new_hire("C11", role_id=admin_role.id)
        request = APIRequestFactory().post(EMPLOYEES_URL, payload, format="json")
        force_authenticate(request, user=actor.user)
        response = EmployeeListCreateView.as_view()(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert_nothing_created(payload)

    def test_service_without_actor_permissions_fails_closed(self):
        from modules.hr.application.services import CreateEmployeeCommand

        with pytest.raises(AuthorizationError):
            get_employee_service().create_employee(
                CreateEmployeeCommand(first_name="No", surname="Actor")
            )
        assert not Employees.objects.filter(first_name="No", surname="Actor").exists()

    def test_superuser_without_employee_record_can_create_with_admin_role(self):
        admin_role = make_role("ADMIN_C12", ["*"])
        superuser = User.objects.create_superuser(email="rem01.su.c12@zchpc.test", password="x")
        payload = new_hire("C12", role_id=admin_role.id)
        response = jwt_client_for(superuser).post(EMPLOYEES_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Employees.objects.get(email=payload["email"]).role_id == admin_role.id


# =============================================================================
# B. Employee update - role assignment boundary
# =============================================================================


class TestEmployeeUpdateRoleBoundary:
    def test_allowed_role_assignment_succeeds(self):
        target_role = make_role("CLERK_U01", ["hr.employee.view"])
        client, _ = actor_with(EMP.MANAGE_ASSIGNMENTS, "hr.employee.view", suffix="U01")
        target = make_employee("Tina", "Target", "U01T")
        response = client.patch(employee_url(target.id), {"role_id": target_role.id}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.role_id == target_role.id

    def test_roles_with_any_api_accepted_name_can_be_assigned(self):
        """The Roles API allows names like these; lookup must not reject them."""
        target_role = make_role("Data Entry - Night Shift", ["hr.employee.view"])
        client, _ = actor_with(EMP.MANAGE_ASSIGNMENTS, "hr.employee.view", suffix="U11")
        target = make_employee("Tina", "Target", "U11T")
        response = client.patch(employee_url(target.id), {"role_id": target_role.id}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_role_with_permissions_the_actor_lacks_is_rejected(self):
        role_admin = make_role("ROLEADMIN_U02", [RoleManagementPermissions.MANAGE])
        client, _ = actor_with(EMP.MANAGE_ASSIGNMENTS, suffix="U02")
        target = make_employee("Tina", "Target", "U02T")
        response = client.patch(employee_url(target.id), {"role_id": role_admin.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ROLE_EXCEEDS_ACTOR_AUTHORITY"
        target.refresh_from_db()
        assert target.role_id is None

    def test_assigning_admin_to_another_employee_is_rejected(self):
        admin_role = make_role("ADMIN_U03", ["*"])
        client, _ = actor_with(EMP.MANAGE_ASSIGNMENTS, "hr.*", suffix="U03")
        target = make_employee("Tina", "Target", "U03T")
        response = client.patch(employee_url(target.id), {"role_id": admin_role.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        target.refresh_from_db()
        assert target.role_id is None

    def test_self_role_escalation_is_rejected(self):
        admin_role = make_role("ADMIN_U04", ["*"])
        client, actor = actor_with(EMP.MANAGE_ASSIGNMENTS, suffix="U04")
        before = actor.role_id
        response = client.patch(employee_url(actor.id), {"role_id": admin_role.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_SELF_ROLE_ESCALATION"
        actor.refresh_from_db()
        assert actor.role_id == before

    def test_self_lateral_move_to_a_role_the_actor_fully_holds_is_allowed(self):
        """Self-assignment is refused only when it would grant something new."""
        narrower = make_role("NARROWER_U05", [EMP.MANAGE_ASSIGNMENTS])
        client, actor = actor_with(EMP.MANAGE_ASSIGNMENTS, "hr.employee.view", suffix="U05")
        response = client.patch(employee_url(actor.id), {"role_id": narrower.id}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        actor.refresh_from_db()
        assert actor.role_id == narrower.id

    @pytest.mark.parametrize(
        "case, actor_permissions, role_permissions, allowed",
        [
            (1, ["hr.*"], ["hr.employee.view", "hr.role.manage"], True),
            (2, ["hr.*"], ["hr.employee.*"], True),
            (3, ["hr.*"], ["hr.*"], True),
            (4, ["hr.*"], ["*"], False),
            (5, ["hr.*"], ["payroll.run.process"], False),
            (6, ["hr.employee.*", "procurement.*"], ["procurement.purchase_request.*"], True),
            (7, ["hr.employee.*"], ["hr.*"], False),
            (8, ["hr.employee.*", "?"], ["*"], False),  # "?" must not "cover" "*"
            (9, ["hr.employee.*", "hr.?"], ["hr.*"], False),
            (10, ["*"], ["*"], True),
        ],
    )
    def test_wildcard_semantics(self, case, actor_permissions, role_permissions, allowed):
        suffix = f"W{case:02d}"
        target_role = make_role(f"TARGET_{suffix}", role_permissions)
        perms = actor_permissions if "*" in actor_permissions else [*actor_permissions, EMP.MANAGE_ASSIGNMENTS]
        client, _ = actor_with(*perms, suffix=suffix)
        target = make_employee("Tina", "Target", f"{suffix}T")
        response = client.patch(employee_url(target.id), {"role_id": target_role.id}, format="json")
        expected = status.HTTP_200_OK if allowed else status.HTTP_403_FORBIDDEN
        assert response.status_code == expected, response.data

    def test_superuser_can_assign_admin(self):
        admin_role = make_role("ADMIN_U06", ["*"])
        superuser = User.objects.create_superuser(email="rem01.su.u06@zchpc.test", password="x")
        target = make_employee("Tina", "Target", "U06T")
        response = jwt_client_for(superuser).patch(
            employee_url(target.id), {"role_id": admin_role.id}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.role_id == admin_role.id

    def test_department_change_still_requires_manage_assignments(self):
        department = Department.objects.create(name="Dept-U07")
        client, _ = actor_with(EMP.CREATE, EMP.DEACTIVATE, "hr.employee.view", suffix="U07")
        target = make_employee("Tina", "Target", "U07T")
        response = client.patch(
            employee_url(target.id), {"department_id": department.id}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        target.refresh_from_db()
        assert target.department_id is None

    def test_invalid_role_id_on_update_is_a_validation_error_not_a_500(self):
        client, _ = actor_with(EMP.MANAGE_ASSIGNMENTS, suffix="U08")
        target = make_employee("Tina", "Target", "U08T")
        response = client.patch(employee_url(target.id), {"role_id": 987654}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "INVALID_ROLE"

    def test_put_is_held_to_the_same_boundary(self):
        admin_role = make_role("ADMIN_U09", ["*"])
        client, actor = actor_with(EMP.MANAGE_ASSIGNMENTS, suffix="U09")
        response = client.put(employee_url(actor.id), {"role_id": admin_role.id}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_bff_profile_update_ignores_role_id(self):
        """The BFF write path does not accept role/department at all."""
        admin_role = make_role("ADMIN_U10", ["*"])
        client, actor = actor_with("bff.employee.view", "hr.employee.view", suffix="U10")
        client.put(f"/api/v2/bff/employees/{actor.uuid}/", {"role_id": admin_role.id}, format="json")
        actor.refresh_from_db()
        assert actor.role_id != admin_role.id


# =============================================================================
# C. Deactivation
# =============================================================================


class TestDeactivation:
    def test_unauthenticated_request_is_denied(self):
        target = make_employee("Tina", "Target", "D01T")
        response = APIClient().delete(employee_url(target.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        target.refresh_from_db()
        assert target.is_active

    def test_actor_without_deactivate_capability_is_denied(self):
        client, _ = actor_with("hr.employee.view", EMP.CREATE, suffix="D02")
        target = make_employee("Tina", "Target", "D02T")
        response = client.delete(employee_url(target.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_DEACTIVATE_NOT_AUTHORIZED"
        target.refresh_from_db()
        assert target.is_active and login_is_active(target)

    def test_capability_is_checked_before_the_target_is_looked_up(self):
        client, _ = actor_with("hr.employee.view", suffix="D03")
        assert client.delete(employee_url(987654)).status_code == status.HTTP_403_FORBIDDEN
        client, _ = actor_with(EMP.DEACTIVATE, suffix="D03b")
        assert client.delete(employee_url(987654)).status_code == status.HTTP_404_NOT_FOUND

    def test_authorized_actor_deactivates_employee_and_login(self):
        staff_role = make_role("STAFF_D04", ["hr.employee.view"])
        client, _ = actor_with(EMP.DEACTIVATE, "hr.employee.view", suffix="D04")
        target = make_employee("Tina", "Target", "D04T", role=staff_role)
        response = client.delete(employee_url(target.id), {"reason": "Left"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        target.user.refresh_from_db()
        assert target.is_active is False
        assert target.user.is_active is False

    def test_employee_without_login_can_be_deactivated(self):
        client, _ = actor_with(EMP.DEACTIVATE, suffix="D05")
        target = Employees.objects.create(
            first_name="No", surname="Login", email="no.login.d05@zchpc.test", employee_id=f"EMP{next(_ec_numbers)}"
        )
        # The post_save signal would have provisioned a login; detach it to
        # cover a record that genuinely has none.
        Employees.objects.filter(pk=target.pk).update(user=None)
        response = client.delete(employee_url(target.id))
        assert response.status_code == status.HTTP_200_OK, response.data
        target.refresh_from_db()
        assert target.is_active is False

    def test_cannot_deactivate_an_admin(self):
        admin_role = make_role("ADMIN_D06", ["*"])
        client, _ = actor_with(EMP.DEACTIVATE, "hr.*", suffix="D06")
        admin = make_employee("Ada", "Admin", "D06T", role=admin_role)
        response = client.delete(employee_url(admin.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        admin.refresh_from_db()
        assert admin.is_active and login_is_active(admin)

    def test_cannot_deactivate_an_employee_linked_to_a_superuser(self):
        client, _ = actor_with(EMP.DEACTIVATE, "hr.*", suffix="D07")
        root = make_employee("Root", "User", "D07T", superuser=True)
        response = client.delete(employee_url(root.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        root.refresh_from_db()
        assert root.is_active and login_is_active(root)

    def test_cannot_deactivate_self_even_with_full_access(self):
        client, actor = actor_with("*", suffix="D08")
        response = client.delete(employee_url(actor.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_SELF_DEACTIVATION"
        actor.refresh_from_db()
        assert actor.is_active and login_is_active(actor)

    def test_full_access_actor_can_deactivate_an_admin(self):
        admin_role = make_role("ADMIN_D09", ["*"])
        client, _ = actor_with("*", suffix="D09")
        admin = make_employee("Ada", "Admin", "D09T", role=admin_role)
        response = client.delete(employee_url(admin.id))
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_body_supplied_actor_identity_is_ignored(self):
        client, actor = actor_with(EMP.DEACTIVATE, suffix="D10")
        response = client.delete(
            employee_url(actor.id),
            {"actor_employee_id": 0, "actor_id": 0, "reason": "x"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_SELF_DEACTIVATION"

    def test_application_layer_denies_even_when_middleware_is_bypassed(self):
        _, actor = actor_with("hr.employee.view", suffix="D11")
        target = make_employee("Tina", "Target", "D11T")
        request = APIRequestFactory().delete(employee_url(target.id))
        force_authenticate(request, user=actor.user)
        response = EmployeeDetailView.as_view()(request, employee_id=target.id)
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        target.refresh_from_db()
        assert target.is_active

    def test_service_without_actor_permissions_fails_closed(self):
        target = make_employee("Tina", "Target", "D12T")
        with pytest.raises(AuthorizationError):
            get_employee_service().deactivate_employee(target.id)
        target.refresh_from_db()
        assert target.is_active


class TestDeactivationRevokesAccess:
    """
    SimpleJWT 5.5.1 (requirements.txt) defaults CHECK_USER_IS_ACTIVE=True
    and this project does not override it: JWTAuthentication.get_user and
    TokenRefreshSerializer both reject an inactive user. These tests prove
    that against the real request path rather than assuming it.
    """

    def _deactivated_target(self, suffix):
        target_role = make_role(f"HRVIEW_{suffix}", ["hr.employee.view"])
        target = make_employee("Tina", "Target", f"{suffix}T", role=target_role)
        access_before = jwt_client_for(target.user)
        refresh_before = str(RefreshToken.for_user(target.user))
        assert access_before.get(EMPLOYEES_URL).status_code == status.HTTP_200_OK

        client, _ = actor_with(EMP.DEACTIVATE, "hr.employee.view", suffix=suffix)
        assert client.delete(employee_url(target.id)).status_code == status.HTTP_200_OK
        return target, access_before, refresh_before

    def test_password_login_is_rejected_after_deactivation(self):
        target, _, _ = self._deactivated_target("R01")
        response = login(target.user.email, PASSWORD)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.data

    def test_access_token_issued_before_deactivation_stops_working(self):
        _, access_before, _ = self._deactivated_target("R02")
        assert access_before.get(EMPLOYEES_URL).status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_issued_before_deactivation_cannot_mint_access(self):
        _, _, refresh_before = self._deactivated_target("R03")
        response = APIClient().post(REFRESH_URL, {"refresh": refresh_before}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.data
        assert "access" not in response.data


class TestDeactivationIsAtomic:
    def test_login_disable_failure_rolls_back_the_employee_change(self, monkeypatch):
        from modules.hr.application.services.employee_service import EmployeeService

        def boom(self, user_id):
            raise RuntimeError("identity write failed")

        monkeypatch.setattr(EmployeeService, "_disable_login", boom)
        target = make_employee("Tina", "Target", "A01T")

        with pytest.raises(RuntimeError):
            get_employee_service().deactivate_employee(
                target.id, actor_permissions=PermissionSet.full_access()
            )

        target.refresh_from_db()
        target.user.refresh_from_db()
        assert target.is_active is True
        assert target.user.is_active is True


# =============================================================================
# Critical regression: the audit's full escalation chain, over HTTP
# =============================================================================


class TestAuditEscalationChainIsBroken:
    """
    Replays the audit's multi-request chain and asserts the attacker cannot
    progress past any step, for three levels of attacker capability.
    """

    def _victim_and_admin(self, suffix):
        admin_role = make_role(f"ADMIN_{suffix}", ["*"])
        victim_role = make_role(f"STAFF_{suffix}", ["hr.employee.view"])
        victim = make_employee("Vic", "Victim", f"{suffix}V", role=victim_role)
        return admin_role, victim

    def _attempt_chain(self, attacker_client, attacker, admin_role, victim, suffix):
        real_admin = make_employee("Ada", "Admin", f"{suffix}A", role=admin_role)
        surname = f"Chain{suffix}"
        email = f"chain.{suffix.lower()}@zchpc.test"

        # Step 1: create an employee carrying the ADMIN role.
        step1 = attacker_client.post(
            EMPLOYEES_URL,
            {"first_name": "Evil", "surname": surname, "email": email, "role_id": admin_role.id},
            format="json",
        )
        assert step1.status_code == status.HTTP_403_FORBIDDEN, step1.data
        assert not Employees.objects.filter(email=email).exists()
        assert not User.objects.filter(email=email).exists()

        # Step 2: authenticate as that employee (surname is the provisioned
        # password, REM-07) - there is no such account.
        step2 = login(email, surname)
        assert step2.status_code == status.HTTP_401_UNAUTHORIZED, step2.data

        # Step 3: privileged actions with the attacker's own, unescalated
        # session: role administration, ADMIN assignment, deactivation.
        own_role = attacker.role
        step3a = attacker_client.patch(role_url(own_role.id), {"permissions": ["*"]}, format="json")
        assert step3a.status_code == status.HTTP_403_FORBIDDEN, step3a.data
        step3b = attacker_client.patch(employee_url(victim.id), {"role_id": admin_role.id}, format="json")
        assert step3b.status_code == status.HTTP_403_FORBIDDEN, step3b.data
        step3c = attacker_client.patch(employee_url(attacker.id), {"role_id": admin_role.id}, format="json")
        assert step3c.status_code == status.HTTP_403_FORBIDDEN, step3c.data
        step3d = attacker_client.delete(employee_url(real_admin.id))
        assert step3d.status_code == status.HTTP_403_FORBIDDEN, step3d.data

        own_role.refresh_from_db()
        attacker.refresh_from_db()
        victim.refresh_from_db()
        real_admin.refresh_from_db()
        assert "*" not in own_role.permissions
        assert attacker.role_id != admin_role.id
        assert victim.role_id != admin_role.id
        assert real_admin.is_active and login_is_active(real_admin)
        assert list(Employees.objects.filter(role=admin_role)) == [real_admin]

    def test_view_only_hr_actor_cannot_escalate(self):
        admin_role, victim = self._victim_and_admin("E01")
        client, attacker = actor_with("hr.employee.view", suffix="E01")
        self._attempt_chain(client, attacker, admin_role, victim, "E01")

    def test_creator_without_assignment_capability_cannot_escalate(self):
        admin_role, victim = self._victim_and_admin("E02")
        client, attacker = actor_with("hr.employee.view", EMP.CREATE, suffix="E02")
        self._attempt_chain(client, attacker, admin_role, victim, "E02")

    def test_full_employee_administrator_below_admin_cannot_escalate(self):
        admin_role, victim = self._victim_and_admin("E03")
        client, attacker = actor_with(
            "hr.employee.view", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, EMP.DEACTIVATE, suffix="E03"
        )
        self._attempt_chain(client, attacker, admin_role, victim, "E03")

    def test_an_account_the_creator_may_legitimately_create_has_no_privilege(self):
        """
        The creator can still create a plain employee (and, until REM-07,
        knows its password), but that login carries no role and so reaches
        nothing privileged.
        """
        client, _ = actor_with("hr.employee.view", EMP.CREATE, suffix="E04")
        payload = new_hire("E04")
        assert client.post(EMPLOYEES_URL, payload, format="json").status_code == 201

        token = login(payload["email"], payload["surname"])
        assert token.status_code == status.HTTP_200_OK, token.data
        new_client = APIClient()
        new_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        assert new_client.get("/api/v2/hr/roles/").status_code == status.HTTP_403_FORBIDDEN
        assert new_client.post(
            "/api/v2/hr/roles/", {"name": "PWNED_E04", "permissions": ["*"]}, format="json"
        ).status_code == status.HTTP_403_FORBIDDEN
        assert not Role.objects.filter(name="PWNED_E04").exists()


# =============================================================================
# Migration 0020
# =============================================================================

_migration = import_module("modules.hr.migrations.0020_seed_employee_lifecycle_permissions")


class _Apps:
    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("hr", "Role")
        return Role


class TestLifecyclePermissionMigration:
    def test_grants_only_to_explicit_assignment_administrators_and_is_idempotent(self):
        admin_of_employees = make_role("EMP_ADMIN_M01", ["hr.employee.view", EMP.MANAGE_ASSIGNMENTS])
        partially = make_role("PARTIAL_M01", [EMP.MANAGE_ASSIGNMENTS, EMP.CREATE])
        unrelated = make_role("UNRELATED_M01", ["hr.employee.view", "hr.role.manage"])

        _migration.grant(_Apps(), None)
        _migration.grant(_Apps(), None)

        for role in (admin_of_employees, partially, unrelated):
            role.refresh_from_db()
        assert admin_of_employees.permissions == [
            "hr.employee.view", EMP.MANAGE_ASSIGNMENTS, EMP.CREATE, EMP.DEACTIVATE
        ]
        assert partially.permissions == [EMP.MANAGE_ASSIGNMENTS, EMP.CREATE, EMP.DEACTIVATE]
        assert unrelated.permissions == ["hr.employee.view", "hr.role.manage"]

    def test_reverse_removes_only_the_strings_it_owns(self):
        role = make_role("EMP_ADMIN_M02", ["hr.employee.view", EMP.MANAGE_ASSIGNMENTS])
        other = make_role("OTHER_M02", [EMP.CREATE])  # not targeted: no manage_assignments

        _migration.grant(_Apps(), None)
        _migration.revoke(_Apps(), None)

        role.refresh_from_db()
        other.refresh_from_db()
        assert role.permissions == ["hr.employee.view", EMP.MANAGE_ASSIGNMENTS]
        assert other.permissions == [EMP.CREATE]
