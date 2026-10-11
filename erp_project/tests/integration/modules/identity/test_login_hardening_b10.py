"""
B10: login hardening.

Before B10 the main login told a caller why it refused: "Account is
deactivated" or "Account is locked until <time>" for a known account, and
"Invalid email or password" otherwise - so the response revealed which
emails had accounts and what state they were in. Neither login was rate
limited; only the per-account lockout (5 failed passwords) slowed guessing.

Now:
- every refusal - unknown login, wrong password, locked, deactivated login,
  employee not in active employment - gets the same status and body, per
  app (main: "Invalid email or password"; portal: "Invalid EC number or
  password"); each refusal is still audited as a failed login;
- both logins share one per-address budget (REST_FRAMEWORK
  DEFAULT_THROTTLE_RATES["login"]); past it, every attempt gets 429, even
  with the right password;
- a normal login, and the REM-07 first login (covered end to end in
  test_credential_lifecycle.TestFirstLoginEndToEnd), still work.
"""

from datetime import timedelta
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from modules.hr.domain.value_objects import EmployeeLifecycleStatus
from modules.hr.infrastructure.persistence.models import Employees
from modules.identity.api.throttles import LoginRateThrottle
from modules.identity.infrastructure.persistence.models import AuditLog

pytestmark = pytest.mark.django_db

User = get_user_model()

LOGIN_URL = "/api/v2/auth/token/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
PASSWORD = "Str0ng-Initial-Passw0rd"

_numbers = count(74001)


def make_employee(label):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password=PASSWORD)
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}",
    )


def locked(employee):
    User.objects.filter(pk=employee.user_id).update(
        failed_attempts=5, lockout_until=timezone.now() + timedelta(minutes=15)
    )
    return employee


def deactivated_login(employee):
    User.objects.filter(pk=employee.user_id).update(is_active=False)
    return employee


def not_in_active_employment(employee):
    # The login itself stays enabled; only the employment says no.
    Employees.objects.filter(pk=employee.pk).update(
        is_active=False, lifecycle_status=EmployeeLifecycleStatus.DEACTIVATED.value
    )
    return employee


def login(email, password, client=None):
    return (client or APIClient()).post(
        LOGIN_URL, {"email": email, "password": password}, format="json"
    )


def portal_login(ec_number, password, client=None):
    return (client or APIClient()).post(
        PORTAL_LOGIN_URL, {"ec_number": ec_number, "password": password}, format="json"
    )


def refusal(response):
    return response.status_code, response.json()


# =============================================================================
# One message for every refusal (no account enumeration)
# =============================================================================


class TestMainLoginGivesOneMessage:
    def test_every_refusal_is_identical(self):
        wrong = make_employee("Wrong")
        responses = {
            "unknown": login("nobody-here@zchpc.test", PASSWORD),
            "wrong password": login(wrong.email, "Not-The-Passw0rd"),
            # The right password: only the account state could tell these apart.
            "locked": login(locked(make_employee("Locked")).email, PASSWORD),
            "deactivated": login(deactivated_login(make_employee("Off")).email, PASSWORD),
            "not employed": login(not_in_active_employment(make_employee("Gone")).email, PASSWORD),
        }

        expected = (status.HTTP_401_UNAUTHORIZED, {"detail": "Invalid email or password"})
        assert {name: refusal(r) for name, r in responses.items()} == {
            name: expected for name in responses
        }

    def test_a_refusal_is_still_audited_against_the_account(self):
        employee = locked(make_employee("Locked"))
        login(employee.email, PASSWORD)

        assert AuditLog.objects.filter(
            username_attempted=employee.email, user=employee.user, event_type="FAILED"
        ).exists()


class TestPortalLoginGivesOneMessage:
    def test_every_refusal_is_identical(self):
        wrong = make_employee("Wrong")
        no_login = Employees.objects.create(
            first_name="No", surname="Login", email="nologin@zchpc.test",
            employee_id=f"EMP{next(_numbers)}",
        )
        responses = {
            "unknown": portal_login("EMP99999", PASSWORD),
            "no login": portal_login(no_login.employee_id, PASSWORD),
            "wrong password": portal_login(wrong.employee_id, "Not-The-Passw0rd"),
            "locked": portal_login(locked(make_employee("Locked")).employee_id, PASSWORD),
            "deactivated": portal_login(deactivated_login(make_employee("Off")).employee_id, PASSWORD),
            "not employed": portal_login(
                not_in_active_employment(make_employee("Gone")).employee_id, PASSWORD
            ),
        }

        expected = (status.HTTP_401_UNAUTHORIZED, {"error": "Invalid EC number or password"})
        assert {name: refusal(r) for name, r in responses.items()} == {
            name: expected for name in responses
        }


# =============================================================================
# Throttle
# =============================================================================


class TestLoginThrottle:
    def test_login_has_a_configured_rate(self):
        from django.conf import settings

        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][LoginRateThrottle.scope]

    @pytest.fixture
    def tight(self, monkeypatch):
        monkeypatch.setattr(LoginRateThrottle, "THROTTLE_RATES", {"login": "3/min"})

    def test_main_login_is_throttled_after_the_budget(self, tight):
        employee = make_employee("Guess")
        codes = [login(employee.email, f"Wrong-{i}").status_code for i in range(3)]
        assert codes == [401, 401, 401]

        # Past the budget even the right password is refused, before any check.
        response = login(employee.email, PASSWORD)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_portal_login_is_throttled_after_the_budget(self, tight):
        employee = make_employee("Guess")
        codes = [portal_login(employee.employee_id, f"Wrong-{i}").status_code for i in range(3)]
        assert codes == [401, 401, 401]
        assert portal_login(employee.employee_id, PASSWORD).status_code == 429

    def test_both_logins_share_one_budget(self, tight):
        employee = make_employee("Both")
        login(employee.email, "Wrong-1")
        portal_login(employee.employee_id, "Wrong-2")
        login(employee.email, "Wrong-3")

        assert portal_login(employee.employee_id, PASSWORD).status_code == 429
        assert login(employee.email, PASSWORD).status_code == 429

    def test_successful_logins_count_too(self, tight):
        employee = make_employee("Busy")
        codes = [login(employee.email, PASSWORD).status_code for _ in range(4)]
        assert codes == [200, 200, 200, 429]

    def test_another_address_keeps_its_own_budget(self, tight):
        employee = make_employee("Other")
        for i in range(3):
            login(employee.email, f"Wrong-{i}", client=APIClient(REMOTE_ADDR="10.0.0.1"))
        assert login(employee.email, "x", client=APIClient(REMOTE_ADDR="10.0.0.1")).status_code == 429

        response = login(employee.email, PASSWORD, client=APIClient(REMOTE_ADDR="10.0.0.2"))
        assert response.status_code == status.HTTP_200_OK

    def test_throttled_attempts_do_not_touch_the_account(self, tight):
        employee = make_employee("Spared")
        for i in range(3):
            login(employee.email, f"Wrong-{i}")
        for i in range(5):
            assert login(employee.email, f"Wrong-more-{i}").status_code == 429

        employee.user.refresh_from_db()
        assert employee.user.failed_attempts == 3
        assert employee.user.lockout_until is None


# =============================================================================
# Normal logins still work
# =============================================================================


class TestNormalLogin:
    def test_main_login_succeeds(self):
        employee = make_employee("Normal")
        response = login(employee.email, PASSWORD)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access"] and response.data["refresh"]
        assert response.data["user"]["email"] == employee.email

    def test_portal_login_succeeds(self):
        employee = make_employee("Normal")
        response = portal_login(employee.employee_id, PASSWORD)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["access"] and response.data["refresh"]
        assert response.data["employee"]["employee_id"] == employee.employee_id
