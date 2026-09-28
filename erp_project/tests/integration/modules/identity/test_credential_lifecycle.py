"""
REM-07: automatic account password provisioning.

Before REM-07, every login provisioned for a new employee (hr.signals) got
the employee's surname as its password: deterministic, never shown, never
required to change, and restored by reactivation. The portal login (EC
number + password) also bypassed the main login's lockout and audit log.

Now:
- provisioning uses the identity module's random generator; the one-time
  temporary password is returned once to the authorized creator;
- the account is must_change_password and RBACMiddleware confines it to
  users/me/ and password/change/ until the owner replaces the password;
- change_password is self-service, needs the current password, applies
  AUTH_PASSWORD_VALIDATORS, clears the flag and - via SIMPLE_JWT
  CHECK_REVOKE_TOKEN - revokes every earlier token;
- reactivation issues a new temporary password; unlock touches only the
  lockout;
- migration identity 0005 flags existing surname-password accounts;
- the portal login authenticates through the identity AuthService.
"""

import logging
from importlib import import_module
from itertools import count

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from modules.hr.application.authorization import EmployeeManagementPermissions as EMP
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.identity.infrastructure.persistence.models import AuditLog

pytestmark = pytest.mark.django_db

User = get_user_model()

EMPLOYEES_URL = "/api/v2/hr/employees/"
USERS_URL = "/api/v2/auth/users/"
ME_URL = "/api/v2/auth/users/me/"
CHANGE_URL = "/api/v2/auth/password/change/"
LOGIN_URL = "/api/v2/auth/token/"
REFRESH_URL = "/api/v2/auth/token/refresh/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
PORTAL_ME_URL = "/api/v2/portal/auth/me/"
PASSWORD = "Str0ng-Initial-Passw0rd"
NEW_PASSWORD = "Another-Str0ng-Passw0rd!"

_numbers = count(71001)


def make_role(name, permissions):
    return Role.objects.create(name=f"{name}_{next(_numbers)}", permissions=list(permissions))


def make_employee(label, *permissions, password=PASSWORD, must_change=False, superuser=False):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=password)
    else:
        user = User.objects.create_user(email=email, password=password)
    if must_change:
        User.objects.filter(pk=user.pk).update(must_change_password=True)
        user.refresh_from_db()
    role = make_role(f"ROLE_{label}", permissions) if permissions else None
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email,
        employee_id=f"EMP{n}", role=role,
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def bearer(access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def login(email, password):
    return APIClient().post(LOGIN_URL, {"email": email, "password": password}, format="json")


def portal_login(ec_number, password):
    return APIClient().post(
        PORTAL_LOGIN_URL, {"ec_number": ec_number, "password": password}, format="json"
    )


def hr_creator():
    return client_for(make_employee("Creator", EMP.CREATE, "hr.employee.view").user)


def hire(creator, surname="Moyo", **extra):
    n = next(_numbers)
    payload = {"first_name": "New", "surname": surname, "email": f"hire{n}@zchpc.test", **extra}
    response = creator.post(EMPLOYEES_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    employee = Employees.objects.select_related("user").get(pk=response.data["id"])
    return response, employee


# =============================================================================
# Provisioning
# =============================================================================


class TestProvisioning:
    def test_new_employee_gets_a_random_temporary_password_not_the_surname(self):
        response, employee = hire(hr_creator(), surname="Chikwanha")
        temporary = response.data["temporary_password"]

        assert temporary and temporary != "Chikwanha"
        assert login(employee.email, "Chikwanha").status_code == status.HTTP_401_UNAUTHORIZED
        assert portal_login(employee.employee_id, "Chikwanha").status_code == status.HTTP_401_UNAUTHORIZED
        ok = login(employee.email, temporary)
        assert ok.status_code == status.HTTP_200_OK, ok.data
        assert ok.data["user"]["must_change_password"] is True
        assert employee.user.must_change_password is True

    def test_temporary_passwords_differ_between_employees(self):
        creator = hr_creator()
        passwords = {hire(creator, surname="Same")[0].data["temporary_password"] for _ in range(5)}
        assert len(passwords) == 5

    def test_provisioning_uses_the_shared_generator_and_no_employee_data(self, monkeypatch):
        import modules.identity.application.services as identity_services

        calls = []

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return "Gener4ted-Only-Here!"

        monkeypatch.setattr(identity_services, "generate_temp_password", spy)
        response, employee = hire(hr_creator(), surname="Ndlovu", employee_id="EMP88888")
        assert calls == [((), {})]  # called with nothing derived from the employee
        assert response.data["temporary_password"] == "Gener4ted-Only-Here!"
        assert employee.user.check_password("Gener4ted-Only-Here!")

    def test_temporary_password_is_stored_only_as_a_hash(self):
        response, employee = hire(hr_creator())
        temporary = response.data["temporary_password"]
        employee.user.refresh_from_db()
        assert temporary not in employee.user.password
        assert employee.user.password.startswith(("pbkdf2_", "argon2", "bcrypt", "scrypt"))
        assert employee.user.check_password(temporary)

    def test_temporary_password_is_not_logged(self, caplog):
        caplog.set_level(logging.DEBUG)
        response, _ = hire(hr_creator())
        assert response.data["temporary_password"] not in caplog.text

    def test_temporary_password_is_exposed_only_in_the_creation_response(self):
        creator = hr_creator()
        response, employee = hire(creator)
        temporary = response.data["temporary_password"]
        for url in (EMPLOYEES_URL, f"{EMPLOYEES_URL}{employee.id}/"):
            later = creator.get(url)
            assert temporary not in later.content.decode()
            assert "temporary_password" not in later.content.decode()

    def test_employee_without_email_gets_no_login_and_no_password(self):
        creator = hr_creator()
        response = creator.post(EMPLOYEES_URL, {"first_name": "No", "surname": "Mail"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["temporary_password"] is None

    def test_identity_api_logins_are_also_forced_to_change(self):
        creator = client_for(make_employee("Creator", EMP.CREATE).user)
        generated = creator.post(
            USERS_URL, {"email": "gen@zchpc.test", "first_name": "G", "last_name": "En"}, format="json"
        )
        chosen = creator.post(
            USERS_URL,
            {"email": "cho@zchpc.test", "first_name": "C", "last_name": "Ho", "password": PASSWORD},
            format="json",
        )
        assert generated.status_code == chosen.status_code == status.HTTP_201_CREATED
        assert "password" not in generated.data and "password" not in chosen.data
        assert generated.data["temporary_password"]
        assert chosen.data["temporary_password"] is None
        assert generated.data["must_change_password"] is chosen.data["must_change_password"] is True
        assert User.objects.get(email="cho@zchpc.test").must_change_password is True


# =============================================================================
# First-login confinement
# =============================================================================


class TestFirstLoginConfinement:
    def test_confined_account_reaches_only_me_and_password_change(self):
        employee = make_employee("Fresh", "hr.employee.view", "portal.*", must_change=True)
        client = client_for(employee.user)

        me = client.get(ME_URL)
        assert me.status_code == status.HTTP_200_OK
        assert me.data["must_change_password"] is True
        for url in (EMPLOYEES_URL, "/api/v2/portal/notifications/", "/api/v2/auth/logs/"):
            blocked = client.get(url)
            assert blocked.status_code == status.HTTP_403_FORBIDDEN, url
            assert blocked.json()["code"] == "PASSWORD_CHANGE_REQUIRED", url
        # The change endpoint is reachable (400 here only because the body is empty).
        assert client.post(CHANGE_URL, {}, format="json").status_code == status.HTTP_400_BAD_REQUEST

    def test_superuser_bypass_does_not_widen_the_confinement(self):
        root = make_employee("Root", superuser=True, must_change=True)
        blocked = client_for(root.user).get(EMPLOYEES_URL)
        assert blocked.status_code == status.HTTP_403_FORBIDDEN
        assert blocked.json()["code"] == "PASSWORD_CHANGE_REQUIRED"

    def test_main_login_reports_and_enforces_the_state(self):
        employee = make_employee("Fresh", "hr.employee.view", must_change=True)
        token = login(employee.email, PASSWORD)
        assert token.status_code == status.HTTP_200_OK
        assert token.data["user"]["must_change_password"] is True
        assert bearer(token.data["access"]).get(EMPLOYEES_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_portal_login_reports_and_enforces_the_state(self):
        employee = make_employee("Fresh", "hr.employee.view", must_change=True)
        token = portal_login(employee.employee_id, PASSWORD)
        assert token.status_code == status.HTTP_200_OK, token.data
        assert token.data["must_change_password"] is True
        client = bearer(token.data["access"])
        assert client.get(PORTAL_ME_URL).data["must_change_password"] is True
        assert client.get(EMPLOYEES_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_normal_account_is_not_confined(self):
        employee = make_employee("Normal", "hr.employee.view")
        assert client_for(employee.user).get(EMPLOYEES_URL).status_code == status.HTTP_200_OK


# =============================================================================
# Password change
# =============================================================================


class TestPasswordChange:
    def test_successful_change_clears_the_state_and_revokes_old_tokens(self):
        employee = make_employee("Fresh", "hr.employee.view", must_change=True)
        old = login(employee.email, PASSWORD).data
        old_client = bearer(old["access"])

        changed = old_client.post(
            CHANGE_URL, {"current_password": PASSWORD, "new_password": NEW_PASSWORD}, format="json"
        )
        assert changed.status_code == status.HTTP_200_OK, changed.data
        assert changed.data["must_change_password"] is False
        employee.user.refresh_from_db()
        assert employee.user.must_change_password is False

        # Tokens issued before the change are revoked ...
        assert old_client.get(ME_URL).status_code == status.HTTP_401_UNAUTHORIZED
        refreshed = APIClient().post(REFRESH_URL, {"refresh": old["refresh"]}, format="json")
        if refreshed.status_code == status.HTTP_200_OK:
            assert bearer(refreshed.data["access"]).get(ME_URL).status_code == status.HTTP_401_UNAUTHORIZED
        # ... the fresh ones returned work, with normal access ...
        assert bearer(changed.data["access"]).get(EMPLOYEES_URL).status_code == status.HTTP_200_OK
        # ... and only the new password logs in.
        assert login(employee.email, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
        assert login(employee.email, NEW_PASSWORD).data["user"]["must_change_password"] is False

    @pytest.mark.parametrize(
        "body, code",
        [
            ({"new_password": NEW_PASSWORD}, None),  # current password missing
            ({"current_password": "wrong-password", "new_password": NEW_PASSWORD}, "INVALID_CURRENT_PASSWORD"),
            ({"current_password": PASSWORD, "new_password": PASSWORD}, "PASSWORD_UNCHANGED"),
            ({"current_password": PASSWORD, "new_password": "password123"}, "INVALID_NEW_PASSWORD"),
            ({"current_password": PASSWORD, "new_password": "84736251940"}, "INVALID_NEW_PASSWORD"),
        ],
    )
    def test_rejected_changes_leave_the_account_as_it_was(self, body, code):
        employee = make_employee("Fresh", "hr.employee.view", must_change=True)
        response = client_for(employee.user).post(CHANGE_URL, body, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        if code:
            assert response.data["code"] == code
        employee.user.refresh_from_db()
        assert employee.user.must_change_password is True
        assert employee.user.check_password(PASSWORD)

    def test_similarity_to_the_account_is_rejected(self):
        employee = make_employee("Fresh", "hr.employee.view", must_change=True)
        response = client_for(employee.user).post(
            CHANGE_URL, {"current_password": PASSWORD, "new_password": employee.email}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "INVALID_NEW_PASSWORD"

    def test_cannot_change_another_users_password(self):
        attacker = make_employee("Attacker", "hr.employee.view")
        victim = make_employee("Victim", "hr.employee.view")
        response = client_for(attacker.user).post(
            CHANGE_URL,
            {"current_password": PASSWORD, "new_password": NEW_PASSWORD,
             "user_id": str(victim.user.id), "email": victim.email},
            format="json",
        )
        # Acts on the caller alone: the attacker's own password changed, the victim's did not.
        assert response.status_code == status.HTTP_200_OK
        victim.user.refresh_from_db()
        assert victim.user.check_password(PASSWORD)
        attacker.user.refresh_from_db()
        assert attacker.user.check_password(NEW_PASSWORD)

    def test_unauthenticated_change_is_rejected(self):
        response = APIClient().post(
            CHANGE_URL, {"current_password": PASSWORD, "new_password": NEW_PASSWORD}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Lifecycle: deactivation, reactivation, unlock
# =============================================================================


class TestLifecycle:
    def _reactivator(self):
        return client_for(make_employee("Reactivator", EMP.REACTIVATE, "hr.employee.view").user)

    def test_deactivated_account_cannot_log_in_anywhere(self):
        employee = make_employee("Leaver", "hr.employee.view")
        User.objects.filter(pk=employee.user.pk).update(is_active=False)
        assert login(employee.email, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
        assert portal_login(employee.employee_id, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED

    def test_reactivation_issues_a_new_temporary_password(self):
        employee = make_employee("Returner", "hr.employee.view")
        User.objects.filter(pk=employee.user.pk).update(is_active=False)

        response = self._reactivator().patch(
            f"{USERS_URL}{employee.user.id}/", {"is_active": True}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        temporary = response.data["temporary_password"]
        assert temporary and temporary != PASSWORD
        assert response.data["must_change_password"] is True

        assert login(employee.email, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
        again = login(employee.email, temporary)
        assert again.status_code == status.HTTP_200_OK
        assert again.data["user"]["must_change_password"] is True

    def test_patching_an_already_active_account_issues_nothing(self):
        employee = make_employee("Active", "hr.employee.view")
        response = self._reactivator().patch(
            f"{USERS_URL}{employee.user.id}/", {"is_active": True}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "temporary_password" not in response.data
        assert login(employee.email, PASSWORD).status_code == status.HTTP_200_OK

    def test_unlock_changes_only_the_lockout(self):
        employee = make_employee("Locked", "hr.employee.view", must_change=True)
        for _ in range(5):
            login(employee.email, "wrong-password")
        assert login(employee.email, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
        before_hash = User.objects.get(pk=employee.user.pk).password

        response = self._reactivator().post(f"{USERS_URL}{employee.user.id}/unlock/")
        assert response.status_code == status.HTTP_200_OK, response.data

        after = User.objects.get(pk=employee.user.pk)
        assert after.password == before_hash
        assert after.must_change_password is True
        assert "temporary_password" not in response.data
        assert login(employee.email, PASSWORD).status_code == status.HTTP_200_OK


# =============================================================================
# Existing surname-password accounts (identity migration 0005)
# =============================================================================


_flag_migration = import_module("modules.identity.migrations.0005_flag_surname_passwords")


class TestSurnamePasswordMigration:
    def test_flags_only_surname_password_accounts_and_is_idempotent(self):
        legacy = make_employee("Legacy", password="Person")  # surname is "Person"
        strong = make_employee("Strong")
        no_login = Employees.objects.create(
            first_name="No", surname="Login", employee_id=f"EMP{next(_numbers)}"
        )
        hashes = {u.pk: u.password for u in User.objects.all()}

        _flag_migration.flag_surname_passwords(django_apps, None)
        _flag_migration.flag_surname_passwords(django_apps, None)

        assert User.objects.get(pk=legacy.user.pk).must_change_password is True
        assert User.objects.get(pk=strong.user.pk).must_change_password is False
        assert no_login.user_id is None
        assert {u.pk: u.password for u in User.objects.all()} == hashes


# =============================================================================
# Portal login: brute-force protection and audit
# =============================================================================


class TestPortalLoginProtection:
    def test_portal_failures_lock_the_account_and_are_audited(self):
        employee = make_employee("Target", "hr.employee.view")
        for _ in range(5):
            assert portal_login(employee.employee_id, "wrong-password").status_code == 401

        assert portal_login(employee.employee_id, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
        assert AuditLog.objects.filter(
            username_attempted=employee.email, event_type="FAILED"
        ).count() >= 5
        assert AuditLog.objects.filter(user=employee.user, event_type="LOCKOUT").exists()

    def test_portal_success_is_audited(self):
        employee = make_employee("Target", "hr.employee.view")
        assert portal_login(employee.employee_id, PASSWORD).status_code == status.HTTP_200_OK
        assert AuditLog.objects.filter(user=employee.user, event_type="SUCCESS").exists()

    def test_unknown_ec_number_is_audited(self):
        assert portal_login("EMP99999", "whatever").status_code == status.HTTP_401_UNAUTHORIZED
        assert AuditLog.objects.filter(username_attempted="EMP99999", event_type="FAILED").exists()

    def test_main_login_lockout_is_intact(self):
        employee = make_employee("Target", "hr.employee.view")
        for _ in range(5):
            login(employee.email, "wrong-password")
        assert login(employee.email, PASSWORD).status_code == status.HTTP_401_UNAUTHORIZED
