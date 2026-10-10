"""
Regression tests for REM-08: identity user administration.

Before REM-08, /api/v2/auth/users/ was exempt from RBACMiddleware and
authorized only by ``is_staff`` in the view, so a staff account could:

- create a superuser (is_superuser=true), or an employee holding any role
  (role=<ADMIN>) with a password of its choosing, then log in as it;
- grant is_staff to anyone, re-enable a login REM-01 deactivated, and
  hard-delete any account (cascading to its employee record).

Remediation: UserService takes the actor's permissions and is judged by
REM-01's EmployeeAuthorizationPolicy (hr.employee.create / deactivate /
reactivate / delete, plus the "no target above your own permissions" rule);
employee records are created through EmployeeService, atomically with the
login; is_staff / is_superuser are refused by the API; and the middleware
exemption is narrowed to the token endpoints, with users/me/ a personal
resource.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.hr.application.authorization import EmployeeManagementPermissions as EMP
from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.api.views import UserListCreateView
from modules.identity.application.services import (
    CreateUserCommand,
    UpdateUserCommand,
    UserService,
)
from modules.identity.domain.value_objects import PermissionSet
from modules.identity.infrastructure.persistence.user_repository import DjangoUserRepository
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

USERS_URL = "/api/v2/auth/users/"
ME_URL = "/api/v2/auth/users/me/"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PASSWORD = "EmployeePass123!"

# EmployeeId accepts only EMP + digits.
_numbers = count(81001)


def user_url(user_id):
    return f"/api/v2/auth/users/{user_id}/"


def unlock_url(user_id):
    return f"/api/v2/auth/users/{user_id}/unlock/"


def make_role(name, permissions):
    return Role.objects.create(name=name, display_name=name.title(), permissions=permissions)


def make_user(label, *, staff=False, superuser=False):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        return User.objects.create_superuser(email=email, password=PASSWORD)
    return User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)


def make_employee(label, *permissions, staff=False, superuser=False, role=None):
    """A login plus employee record whose role grants exactly ``permissions``."""
    user = make_user(label, staff=staff, superuser=superuser)
    if role is None and permissions:
        role = make_role(f"ROLE_{label}_{next(_numbers)}", list(permissions))
    return Employees.objects.create(
        user=user,
        first_name=label,
        surname="Person",
        email=user.email,
        employee_id=f"EMP{next(_numbers)}",
        role=role,
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def new_login(label, **extra):
    return {
        "first_name": "New",
        "last_name": label,
        "email": f"new.{label.lower()}@zchpc.test",
        "password": "ChosenPass123!",
        **extra,
    }


def login(email, password):
    return APIClient().post(LOGIN_URL, {"email": email, "password": password}, format="json")


def assert_nothing_created(payload):
    assert not User.objects.filter(email__iexact=payload["email"]).exists()
    assert not Employees.objects.filter(email__iexact=payload["email"]).exists()


def fresh(user):
    return User.objects.get(pk=user.pk)


# =============================================================================
# Creation - authorization
# =============================================================================


class TestCreateAuthorization:
    def test_unauthenticated_request_is_denied(self):
        payload = new_login("A01")
        assert APIClient().post(USERS_URL, payload, format="json").status_code == 401
        assert_nothing_created(payload)

    def test_ordinary_hr_user_without_create_capability_is_denied(self):
        actor = make_employee("Plain", "hr.employee.view")
        payload = new_login("A02")
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_CREATE_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_staff_only_account_is_denied(self):
        staff = make_user("Staffonly", staff=True)
        payload = new_login("A03")
        response = client_for(staff).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert_nothing_created(payload)

    def test_staff_flag_adds_nothing_to_an_hr_role_without_the_capability(self):
        actor = make_employee("Staffhr", "hr.employee.view", staff=True)
        payload = new_login("A04")
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_CREATE_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_actor_with_create_capability_creates_a_plain_login(self):
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("A05")
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        created = User.objects.get(email=payload["email"])
        assert not created.is_staff and not created.is_superuser
        assert not Employees.objects.filter(user=created).exists()

    def test_department_creates_the_employee_record_through_employee_service(self):
        department = Department.objects.create(name="Dept-A06")
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("A06", department=department.id)
        users_before = User.objects.count()
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        created = User.objects.get(email=payload["email"])
        employee = Employees.objects.get(user=created)
        assert employee.department_id == department.id
        assert employee.role_id is None
        assert employee.employee_id.startswith("EMP")
        # No second, signal-provisioned login.
        assert User.objects.count() == users_before + 1

    def test_superuser_keeps_full_provisioning_ability(self):
        admin_role = make_role("ADMIN_A07", ["*"])
        root = make_user("Root", superuser=True)
        payload = new_login("A07", role=admin_role.id)
        response = client_for(root).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Employees.objects.get(email=payload["email"]).role_id == admin_role.id

    def test_application_layer_denies_when_middleware_is_bypassed(self):
        staff = make_user("Bypass", staff=True)
        payload = new_login("A08")
        request = APIRequestFactory().post(USERS_URL, payload, format="json")
        force_authenticate(request, user=staff)
        response = UserListCreateView.as_view()(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert_nothing_created(payload)


# =============================================================================
# Creation - privilege injection
# =============================================================================


class TestPrivilegeFlagInjection:
    @pytest.mark.parametrize("flag", ["is_superuser", "is_staff"])
    def test_privileged_flag_is_rejected_even_for_an_authorized_creator(self, flag):
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login(f"B{flag[3:6]}", **{flag: True})
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert flag in response.data
        assert_nothing_created(payload)

    def test_superuser_cannot_mint_a_superuser_through_the_api_either(self):
        root = make_user("Root", superuser=True)
        payload = new_login("B02", is_superuser=True)
        response = client_for(root).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert_nothing_created(payload)

    def test_explicit_false_flags_are_still_accepted(self):
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("B03", is_staff=False, is_superuser=False)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_service_cannot_express_privileged_flags(self):
        with pytest.raises(TypeError):
            CreateUserCommand(email="x@zchpc.test", first_name="X", last_name="Y", is_superuser=True)


# =============================================================================
# Creation - role assignment (REM-01 rules, via EmployeeService)
# =============================================================================


class TestCreateRoleAssignment:
    def test_role_needs_manage_assignments(self):
        role = make_role("PLAIN_C01", [])
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("C01", role=role.id)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        assert_nothing_created(payload)

    def test_role_above_the_actors_authority_is_denied(self):
        admin_role = make_role("ADMIN_C02", ["*"])
        actor = make_employee("Hradmin", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, "hr.*")
        payload = new_login("C02", role=admin_role.id)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ROLE_EXCEEDS_ACTOR_AUTHORITY"
        assert_nothing_created(payload)

    def test_role_within_the_actors_authority_is_assigned(self):
        clerk = make_role("CLERK_C03", ["procurement.purchase_request.view"])
        actor = make_employee("Hradmin", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, "procurement.*")
        payload = new_login("C03", role=clerk.id)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        employee = Employees.objects.get(email=payload["email"])
        assert employee.role_id == clerk.id
        assert employee.user.email == payload["email"]

    def test_missing_role_is_400_and_leaves_nothing(self):
        actor = make_employee("Hradmin", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS)
        payload = new_login("C04", role=987654)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "INVALID_ROLE"
        assert_nothing_created(payload)

    def test_missing_department_leaves_nothing(self):
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("C05", department=987654)
        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.data
        assert_nothing_created(payload)

    def test_existing_login_email_is_a_conflict(self):
        actor = make_employee("Creator", EMP.CREATE)
        existing = make_user("Existing")
        response = client_for(actor.user).post(
            USERS_URL, new_login("C06", email=existing.email.upper()), format="json"
        )
        assert response.status_code == status.HTTP_409_CONFLICT, response.data

    def test_existing_employee_email_rolls_the_login_back(self):
        department = Department.objects.create(name="Dept-C07")
        actor = make_employee("Creator", EMP.CREATE)
        payload = new_login("C07", department=department.id)
        # An employee record with this email but no login: the signal
        # provisions one on create, so unlink it and delete it.
        old = Employees.objects.create(
            first_name="Old", surname="Record", email=payload["email"],
            employee_id=f"EMP{next(_numbers)}",
        )
        Employees.objects.filter(pk=old.pk).update(user=None)
        User.objects.filter(email=payload["email"]).delete()
        assert Employees.objects.filter(pk=old.pk).exists()

        response = client_for(actor.user).post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "DUPLICATE_EMAIL"
        assert not User.objects.filter(email=payload["email"]).exists()


class TestCreateIsAtomic:
    def test_employee_failure_rolls_back_the_login(self, monkeypatch):
        from modules.hr.application.services.employee_service import EmployeeService

        def boom(self, *args, **kwargs):
            raise RuntimeError("employee write failed")

        monkeypatch.setattr(EmployeeService, "create_employee", boom)
        department = Department.objects.create(name="Dept-D01")
        command = CreateUserCommand(
            email="atomic.d01@zchpc.test", first_name="A", last_name="Tomic",
            department_id=department.id,
        )
        with pytest.raises(RuntimeError):
            UserService(DjangoUserRepository()).create_user(
                command, actor_permissions=PermissionSet.full_access()
            )
        assert not User.objects.filter(email="atomic.d01@zchpc.test").exists()
        assert not Employees.objects.filter(email="atomic.d01@zchpc.test").exists()


# =============================================================================
# Configurable RBAC: capability granted through the Roles API, end to end
# =============================================================================


class TestAdministratorConfiguredCapability:
    def test_a_custom_role_granted_the_capability_can_provision_logins(self):
        root = make_user("Root", superuser=True)
        admin = client_for(root)

        created_role = admin.post(
            "/api/v2/hr/roles/",
            {"name": "ONBOARDING_CLERK_E01", "permissions": [EMP.CREATE]},
            format="json",
        )
        assert created_role.status_code == status.HTTP_201_CREATED, created_role.data

        clerk = make_employee("Clerk")
        assigned = admin.patch(
            f"/api/v2/hr/employees/{clerk.id}/", {"role_id": created_role.data["id"]}, format="json"
        )
        assert assigned.status_code == status.HTTP_200_OK, assigned.data

        token = login(clerk.user.email, PASSWORD)
        assert token.status_code == status.HTTP_200_OK, token.data
        clerk_client = APIClient()
        clerk_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
        payload = new_login("E01")
        response = clerk_client.post(USERS_URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert User.objects.filter(email=payload["email"]).exists()


# =============================================================================
# PATCH /users/{id}/
# =============================================================================


class TestUpdate:
    @pytest.mark.parametrize("flag", ["is_staff", "is_superuser"])
    def test_privileged_flags_are_rejected(self, flag):
        root = make_user("Root", superuser=True)
        target = make_user("Target")
        response = client_for(root).patch(user_url(target.id), {flag: True}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert not getattr(fresh(target), flag)

    def test_deactivation_without_capability_is_denied(self):
        actor = make_employee("Plain", "hr.employee.view", staff=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).patch(user_url(target.user.id), {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_DEACTIVATE_NOT_AUTHORIZED"
        assert fresh(target.user).is_active

    def test_authorized_deactivation_follows_rem01_policy(self):
        actor = make_employee("Offboarder", EMP.DEACTIVATE, "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).patch(user_url(target.user.id), {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert not fresh(target.user).is_active

    def test_deactivating_a_more_privileged_account_is_denied(self):
        actor = make_employee("Offboarder", EMP.DEACTIVATE, "hr.*")
        admin = make_employee("Admin", "*")
        response = client_for(actor.user).patch(user_url(admin.user.id), {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert fresh(admin.user).is_active

    def test_deactivating_yourself_is_denied(self):
        actor = make_employee("Self", EMP.DEACTIVATE, "*")
        response = client_for(actor.user).patch(user_url(actor.user.id), {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert fresh(actor.user).is_active

    def test_unauthorized_reactivation_is_denied(self):
        actor = make_employee("Offboarder", EMP.DEACTIVATE, "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        User.objects.filter(pk=target.user.pk).update(is_active=False)
        response = client_for(actor.user).patch(user_url(target.user.id), {"is_active": True}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_REACTIVATE_NOT_AUTHORIZED"
        assert not fresh(target.user).is_active

    def test_authorized_reactivation_succeeds(self):
        actor = make_employee("Reactivator", EMP.REACTIVATE, "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        User.objects.filter(pk=target.user.pk).update(is_active=False)
        response = client_for(actor.user).patch(user_url(target.user.id), {"is_active": True}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert fresh(target.user).is_active

    def test_reactivating_a_more_privileged_account_is_denied(self):
        actor = make_employee("Reactivator", EMP.REACTIVATE, "hr.*")
        admin = make_employee("Admin", "*")
        User.objects.filter(pk=admin.user.pk).update(is_active=False)
        response = client_for(actor.user).patch(user_url(admin.user.id), {"is_active": True}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert not fresh(admin.user).is_active

    def test_own_name_change_still_works(self):
        actor = make_employee("Self", "hr.employee.view")
        response = client_for(actor.user).patch(user_url(actor.user.id), {"first_name": "Renamed"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert fresh(actor.user).first_name == "Renamed"

    def test_renaming_someone_else_needs_the_create_capability(self):
        actor = make_employee("Plain", "hr.employee.view", staff=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).patch(user_url(target.user.id), {"first_name": "X"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


# =============================================================================
# DELETE /users/{id}/  and  POST /users/{id}/unlock/
# =============================================================================


class TestDelete:
    """
    Changed by AUD-02 Slice 4: accounts are no longer deleted through the
    API at all, so REM-08's delete authorization (hr.employee.delete, no
    self-deletion, no deleting anyone above you) has nothing left to guard.
    Every caller - including those REM-08 allowed - is refused with 405 and
    nothing changes.
    """

    def test_staff_without_capability_is_refused(self):
        actor = make_employee("Staff", "hr.employee.view", staff=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).delete(user_url(target.user.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert User.objects.filter(pk=target.user.pk).exists()
        assert Employees.objects.filter(pk=target.pk).exists()

    def test_privileged_account_is_refused(self):
        actor = make_employee("Deleter", EMP.DELETE, "hr.*")
        root = make_user("Root", superuser=True)
        response = client_for(actor.user).delete(user_url(root.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert User.objects.filter(pk=root.pk).exists()

    def test_own_account_is_refused(self):
        actor = make_employee("Deleter", EMP.DELETE, "*")
        response = client_for(actor.user).delete(user_url(actor.user.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert User.objects.filter(pk=actor.user.pk).exists()

    def test_former_delete_capability_no_longer_deletes(self):
        actor = make_employee("Deleter", EMP.DELETE, "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).delete(user_url(target.user.id))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert User.objects.filter(pk=target.user.pk).exists()
        assert Employees.objects.filter(pk=target.pk).exists()


class TestUnlock:
    def test_staff_without_capability_cannot_unlock(self):
        actor = make_employee("Staff", "hr.employee.view", staff=True)
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).post(unlock_url(target.user.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_reactivate_capability_unlocks(self):
        actor = make_employee("Unlocker", EMP.REACTIVATE, "hr.employee.view")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(actor.user).post(unlock_url(target.user.id))
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_lock_state_is_visible_and_unlock_clears_it(self):
        """B8: synergy shows Unlock only for a locked account, so the user
        responses carry lockout_until."""
        from datetime import timedelta
        from django.utils import timezone

        actor = make_employee("Unlocker", EMP.REACTIVATE, "hr.employee.view")
        target = make_employee("Locked", "hr.employee.view")
        User.objects.filter(pk=target.user.pk).update(
            failed_attempts=5, lockout_until=timezone.now() + timedelta(minutes=15)
        )
        client = client_for(actor.user)

        detail = client.get(user_url(target.user.id))
        listed = {u["id"]: u for u in client.get(USERS_URL).data}
        assert detail.data["lockout_until"] is not None
        assert listed[str(target.user.id)]["lockout_until"] is not None

        unlocked = client.post(unlock_url(target.user.id))
        assert unlocked.status_code == status.HTTP_200_OK, unlocked.data
        assert unlocked.data["lockout_until"] is None
        assert client.get(user_url(target.user.id)).data["lockout_until"] is None


# =============================================================================
# Service layer fails closed without an actor
# =============================================================================


class TestServiceLayerFailsClosed:
    def test_every_mutation_requires_actor_permissions(self):
        service = UserService(DjangoUserRepository())
        target = make_user("Target")
        with pytest.raises(AuthorizationError):
            service.create_user(CreateUserCommand(email="svc@zchpc.test", first_name="S", last_name="V"))
        with pytest.raises(AuthorizationError):
            service.update_user(UpdateUserCommand(user_id=target.id, is_active=False))
        with pytest.raises(AuthorizationError):
            service.update_user(UpdateUserCommand(user_id=target.id, is_active=True))
        with pytest.raises(AuthorizationError):
            service.update_user(UpdateUserCommand(user_id=target.id, first_name="X"))
        assert not hasattr(service, "delete_user")  # AUD-02: no delete at all
        with pytest.raises(AuthorizationError):
            service.unlock_user(target.id)
        assert not User.objects.filter(email="svc@zchpc.test").exists()
        assert User.objects.filter(pk=target.pk, is_active=True, first_name="").exists()


# =============================================================================
# Middleware exemption
# =============================================================================


class TestMiddlewareBoundary:
    def test_token_and_refresh_remain_public(self):
        user = make_user("Loginonly")
        assert login(user.email, PASSWORD).status_code == status.HTTP_200_OK
        refresh = APIClient().post(REFRESH_URL, {"refresh": str(RefreshToken.for_user(user))}, format="json")
        assert refresh.status_code == status.HTTP_200_OK, refresh.data

    def test_me_stays_available_to_ordinary_users(self):
        procurement_only = make_employee("Buyer", "procurement.purchase_request.view")
        assert client_for(procurement_only.user).get(ME_URL).status_code == status.HTTP_200_OK
        no_profile = make_user("Noprofile")
        assert client_for(no_profile).get(ME_URL).status_code == status.HTTP_200_OK
        assert APIClient().get(ME_URL).status_code == status.HTTP_401_UNAUTHORIZED

    def test_legacy_identity_wildcard_does_not_open_user_administration(self):
        legacy_staff = make_employee("Legacy", "identity.*", "self.*", "portal.*")
        response = client_for(legacy_staff.user).post(USERS_URL, new_login("M01"), format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_account_without_any_role_is_stopped_at_the_gate(self):
        staff = make_user("Norole", staff=True)
        assert client_for(staff).get(USERS_URL).status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# The original attack chains, over HTTP
# =============================================================================


class TestOriginalAttackChainsAreBroken:
    def _attackers(self):
        staff_only = make_user("Attacker", staff=True)
        staff_with_hr = make_employee("Attackerhr", "hr.employee.view", staff=True)
        return [client_for(staff_only), client_for(staff_with_hr.user)]

    def test_chain1_staff_cannot_mint_a_superuser(self):
        for i, attacker in enumerate(self._attackers()):
            payload = new_login(f"X1{i}", is_superuser=True)
            response = attacker.post(USERS_URL, payload, format="json")
            assert response.status_code in (400, 403), response.data
            assert login(payload["email"], payload["password"]).status_code == 401
            assert_nothing_created(payload)
        assert not User.objects.filter(is_superuser=True).exists()

    def test_chain2_staff_cannot_create_an_admin_employee(self):
        admin_role = make_role("ADMIN_X2", ["*"])
        attackers = self._attackers() + [
            client_for(make_employee("Hradmin", EMP.CREATE, EMP.MANAGE_ASSIGNMENTS, "hr.*", staff=True).user)
        ]
        for i, attacker in enumerate(attackers):
            payload = new_login(f"X2{i}", role=admin_role.id)
            response = attacker.post(USERS_URL, payload, format="json")
            assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
            assert login(payload["email"], payload["password"]).status_code == 401
            assert_nothing_created(payload)
        assert not Employees.objects.filter(role=admin_role).exists()

    def test_staff_cannot_grant_staff_to_another_account(self):
        victim = make_user("Victim")
        for attacker in self._attackers():
            response = attacker.patch(user_url(victim.id), {"is_staff": True}, format="json")
            assert response.status_code in (400, 403), response.data
        assert not fresh(victim).is_staff

    def test_staff_cannot_revive_a_login_rem01_deactivated(self):
        hr = make_employee("Offboarder", EMP.DEACTIVATE, "hr.employee.view")
        leaver = make_employee("Leaver", "hr.employee.view")
        rem01 = client_for(hr.user).delete(f"/api/v2/hr/employees/{leaver.id}/")
        assert rem01.status_code == status.HTTP_200_OK, rem01.data
        assert not fresh(leaver.user).is_active

        for attacker in self._attackers():
            response = attacker.patch(user_url(leaver.user.id), {"is_active": True}, format="json")
            assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
            assert attacker.post(unlock_url(leaver.user.id)).status_code == status.HTTP_403_FORBIDDEN
        assert not fresh(leaver.user).is_active
        assert login(leaver.user.email, PASSWORD).status_code == 401
