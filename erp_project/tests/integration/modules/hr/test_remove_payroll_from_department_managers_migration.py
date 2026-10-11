"""
hr.0025: department heads lose payroll.* (INT-01 Q1).

Migration 0017 gave MANAGER and DEPARTMENT_MANAGER the legacy map's grants,
payroll.* included, so department heads could reach every payroll route.
0025 removes exactly payroll.* from those two roles (by 0017's name
normalisation) and leaves every other grant; the reverse adds it back.

Same convention as test_seed_hr_role_migration.py: the migration's own
forward/reverse functions are imported via importlib and run against the
real Role model.
"""

from importlib import import_module
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role

_migration = import_module("modules.hr.migrations.0025_remove_payroll_from_department_managers")

pytestmark = pytest.mark.django_db

User = get_user_model()

# The grants 0017 copied onto both roles.
LEGACY_MANAGER_GRANTS = [
    "hr.*", "attendance.*", "leave.*", "payroll.*", "reports.*", "identity.*", "portal.*",
]
WITHOUT_PAYROLL = [p for p in LEGACY_MANAGER_GRANTS if p != "payroll.*"]

PAYROLL_URL = "/api/v2/payroll/payslips/"
HR_URL = "/api/v2/hr/employees/"
ACCESS_URL = "/api/v2/auth/users/me/access/"

_numbers = count(77001)


class _Apps:
    def get_model(self, app_label, model_name):
        assert (app_label, model_name) == ("hr", "Role")
        return Role


def forward():
    _migration.remove_payroll(_Apps(), None)


def reverse():
    _migration.restore_payroll(_Apps(), None)


def role(name, permissions):
    obj, _ = Role.objects.update_or_create(name=name, defaults={"permissions": list(permissions)})
    return obj


def perms(obj):
    obj.refresh_from_db()
    return obj.permissions


def client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


def make_employee(role_obj):
    n = next(_numbers)
    email = f"head{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="Str0ng-Initial-Passw0rd")
    return Employees.objects.create(
        user=user, first_name="Head", surname="Person", email=email, employee_id=f"EMP{n}",
        role=role_obj,
    )


class TestForward:
    @pytest.mark.parametrize("name", ["DEPARTMENT_MANAGER", "MANAGER"])
    def test_removes_exactly_payroll_wildcard(self, name):
        target = role(name, LEGACY_MANAGER_GRANTS)
        forward()
        assert perms(target) == WITHOUT_PAYROLL

    @pytest.mark.parametrize("name", ["Department Manager", "department-manager", "manager"])
    def test_matches_names_as_0017_did(self, name):
        target = role(name, ["leave.*", "payroll.*"])
        forward()
        assert perms(target) == ["leave.*"]

    def test_other_roles_keep_payroll(self):
        accountant = role("ACCOUNTANT", ["payroll.*", "accounts.*"])
        hr = role("HUMAN_RESOURCES", ["hr.*", "payroll.*"])
        general_manager = role("GENERAL_MANAGER", ["payroll.*"])  # not a department manager
        role("DEPARTMENT_MANAGER", LEGACY_MANAGER_GRANTS)

        forward()

        assert perms(accountant) == ["payroll.*", "accounts.*"]
        assert perms(hr) == ["hr.*", "payroll.*"]
        assert perms(general_manager) == ["payroll.*"]

    def test_narrower_payroll_grants_and_full_access_are_left_alone(self):
        narrow = role("DEPARTMENT_MANAGER", ["payroll.payslip.view", "leave.*"])
        full = role("MANAGER", ["*"])
        forward()
        assert perms(narrow) == ["payroll.payslip.view", "leave.*"]
        assert perms(full) == ["*"]

    def test_running_twice_changes_nothing_more(self):
        target = role("DEPARTMENT_MANAGER", LEGACY_MANAGER_GRANTS)
        forward()
        forward()
        assert perms(target) == WITHOUT_PAYROLL


class TestReverse:
    def test_adds_payroll_back(self):
        target = role("DEPARTMENT_MANAGER", LEGACY_MANAGER_GRANTS)
        forward()
        reverse()
        assert sorted(perms(target)) == sorted(LEGACY_MANAGER_GRANTS)

    def test_does_not_duplicate_and_leaves_other_roles(self):
        target = role("MANAGER", ["payroll.*", "leave.*"])
        staff = role("REGULAR_STAFF", ["portal.*"])
        reverse()
        assert perms(target) == ["payroll.*", "leave.*"]
        assert perms(staff) == ["portal.*"]


class TestAccessAfterTheMigration:
    """End to end, through RBACMiddleware with a real token."""

    def test_department_head_loses_payroll_routes_and_keeps_the_rest(self):
        head = make_employee(role("DEPARTMENT_MANAGER", LEGACY_MANAGER_GRANTS))
        assert client_for(head).get(PAYROLL_URL).status_code != 403

        forward()

        client = client_for(head)
        assert client.get(PAYROLL_URL).status_code == 403
        assert client.get(HR_URL).status_code != 403
        access = client.get(ACCESS_URL)
        assert access.status_code == 200
        assert "payroll.*" not in access.data["permissions"]
        assert "leave.*" in access.data["permissions"]

    def test_manager_role_loses_payroll_routes(self):
        manager = make_employee(role("MANAGER", LEGACY_MANAGER_GRANTS))
        forward()
        assert client_for(manager).get(PAYROLL_URL).status_code == 403
