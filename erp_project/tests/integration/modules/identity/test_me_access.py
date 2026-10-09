"""
GET /api/v2/auth/users/me/access/ - what the caller may do (INT-01 §2).

The front ends shape their menus from this one summary, so these tests pin:

- it describes the authenticated caller only, and nothing beyond its fields;
- permissions are exactly the grants RBACMiddleware reads, for every seeded role;
- department headship is the recorded Department.head;
- the AUD-02 lifecycle rule refuses a login whose employee has left;
- active_modules carries the installed module identifiers synergy filters on.

Authentication uses real JWTs, because the route is gated by RBACMiddleware
before DRF's view-level authentication runs.
"""

from io import StringIO
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Department, Employees, Role
from modules.identity.infrastructure.persistence.models import SystemModule
from modules.identity.infrastructure.route_access import permission_set_for_user
from modules.procurement.management.commands.seed_pr_test_data import ACTORS

pytestmark = pytest.mark.django_db

ACCESS_URL = "/api/v2/auth/users/me/access/"
FIELDS = {"role", "permissions", "is_department_head", "headed_department_ids", "active_modules"}
# Installed by identity migration 0003; the synergy navConfig moduleIdentifier
# values (hr, payroll, accounts, procurement, sales, inventory) are filtered
# against this list, and sales/inventory have no backend module yet.
SEEDED_ACTIVE_MODULES = ["accounts", "hr", "payroll", "procurement"]
PASSWORD = "AccessPass123!"

User = get_user_model()
_numbers = count(1)


def make_employee(label, permissions=(), department=None, role=None):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password=PASSWORD)
    if role is None and permissions:
        role = Role.objects.create(name=f"ROLE_{label}_{n}", permissions=list(permissions))
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email,
        employee_id=f"EMP{n}", role=role, department=department,
    )


def client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def access_of(user):
    response = client_for(user).get(ACCESS_URL)
    assert response.status_code == 200, response.content
    return response.json()


class TestCallerOnly:
    def test_unauthenticated_is_refused(self):
        assert APIClient().get(ACCESS_URL).status_code == 401

    def test_returns_exactly_the_summary_fields(self):
        employee = make_employee("Fields", ["leave.request.create"])

        assert set(access_of(employee.user)) == FIELDS

    def test_a_user_id_in_the_query_is_ignored(self):
        caller = make_employee("Caller", ["leave.request.create"])
        other = make_employee("Other", ["*"])

        response = client_for(caller.user).get(ACCESS_URL, {"user_id": other.user_id})

        assert response.status_code == 200
        assert response.json()["permissions"] == ["leave.request.create"]

    def test_there_is_no_route_for_another_users_access(self):
        caller = make_employee("Prober", ["*"])
        other = make_employee("Target", ["leave.request.create"])

        response = client_for(caller.user).get(f"/api/v2/auth/users/{other.user_id}/access/")

        assert response.status_code in (403, 404)

    def test_reachable_without_any_identity_or_hr_grant(self):
        # A personal resource: a role granting nothing in identity still reads it.
        employee = make_employee("Narrow", ["procurement.purchase_request.view"])

        assert access_of(employee.user)["permissions"] == ["procurement.purchase_request.view"]

    def test_a_temporary_password_confines_the_caller_to_changing_it(self):
        employee = make_employee("Temporary", ["leave.request.create"])
        User.objects.filter(pk=employee.user_id).update(must_change_password=True)

        response = client_for(employee.user).get(ACCESS_URL)

        assert response.status_code == 403
        assert response.json()["code"] == "PASSWORD_CHANGE_REQUIRED"


class TestSeededRoles:
    @pytest.fixture
    def seeded(self):
        call_command("seed_pr_test_data", stdout=StringIO())
        return {
            spec["key"]: Employees.objects.select_related("user", "department").get(
                email=spec["email"]
            )
            for spec in ACTORS
        }

    @pytest.mark.parametrize("spec", ACTORS, ids=[spec["key"] for spec in ACTORS])
    def test_each_seeded_actor_gets_its_roles_permissions(self, seeded, spec):
        employee = seeded[spec["key"]]

        access = access_of(employee.user)

        assert access["role"] == spec["role_name"]
        assert access["permissions"] == list(spec["permissions"])
        assert access["permissions"] == permission_set_for_user(employee.user).to_list()

    @pytest.mark.parametrize("spec", ACTORS, ids=[spec["key"] for spec in ACTORS])
    def test_only_the_seeded_department_head_is_a_head(self, seeded, spec):
        employee = seeded[spec["key"]]

        access = access_of(employee.user)

        assert access["is_department_head"] is spec["is_department_head"]
        expected = [employee.department_id] if spec["is_department_head"] else []
        assert access["headed_department_ids"] == expected

    def test_the_migration_seeded_hr_role_gets_its_permissions(self):
        role = Role.objects.get(name="HUMAN_RESOURCES")
        employee = make_employee("Hr", role=role)

        access = access_of(employee.user)

        assert access["role"] == "HUMAN_RESOURCES"
        assert access["permissions"] == list(role.permissions)
        assert access["permissions"]

    def test_the_seeded_admin_gets_full_access(self):
        call_command("seed_admin", stdout=StringIO())
        admin = User.objects.get(email="admin@zchpc.ac.zw")

        access = access_of(admin)

        assert access["role"] == "ADMIN"
        assert access["permissions"] == ["*"]

    def test_a_superuser_without_an_employee_record_gets_full_access(self):
        # Mirrors RBACMiddleware's superuser bypass (resolve_actor_permissions).
        admin = User.objects.create_superuser(email="bootstrap@zchpc.test", password=PASSWORD)

        access = access_of(admin)

        assert access["role"] is None
        assert access["permissions"] == ["*"]
        assert access["is_department_head"] is False


class TestDepartmentHead:
    def test_the_recorded_head_gets_their_department(self):
        department = Department.objects.create(name="Finance")
        head = make_employee("Head", ["procurement.purchase_request.department_head_approve"],
                             department=department)
        department.head = head
        department.save(update_fields=["head"])

        access = access_of(head.user)

        assert access["is_department_head"] is True
        assert access["headed_department_ids"] == [department.pk]

    def test_every_headed_department_is_listed(self):
        first = Department.objects.create(name="Audit")
        second = Department.objects.create(name="Legal")
        head = make_employee("Twohead", ["leave.request.create"], department=first)
        Department.objects.filter(pk__in=[first.pk, second.pk]).update(head=head)

        assert access_of(head.user)["headed_department_ids"] == sorted([first.pk, second.pk])

    def test_a_member_of_a_headed_department_is_not_a_head(self):
        department = Department.objects.create(name="Stores")
        head = make_employee("Storeshead", ["leave.request.create"], department=department)
        member = make_employee("Member", ["leave.request.create"], department=department)
        department.head = head
        department.save(update_fields=["head"])

        access = access_of(member.user)

        assert access["is_department_head"] is False
        assert access["headed_department_ids"] == []

    def test_a_manager_role_name_alone_does_not_make_a_head(self):
        # INT-01 Q2 default: headship is Department.head, not the role name.
        manager = make_employee("Deptmanager", role=Role.objects.create(
            name="DEPARTMENT_MANAGER_X", permissions=["leave.*"]))

        assert access_of(manager.user)["is_department_head"] is False


class TestLifecycle:
    @pytest.mark.parametrize("lifecycle_status", ["DEACTIVATED", "ARCHIVED"])
    def test_an_employee_not_in_active_employment_is_refused(self, lifecycle_status):
        employee = make_employee("Leaver", ["leave.request.create"])
        client = client_for(employee.user)  # token issued while employed
        Employees.objects.filter(pk=employee.pk).update(
            lifecycle_status=lifecycle_status, is_active=False
        )

        assert client.get(ACCESS_URL).status_code == 401

    def test_a_disabled_login_is_refused(self):
        employee = make_employee("Disabled", ["leave.request.create"])
        client = client_for(employee.user)
        User.objects.filter(pk=employee.user_id).update(is_active=False)

        assert client.get(ACCESS_URL).status_code == 401


class TestActiveModules:
    def test_lists_the_installed_modules_for_a_non_admin(self):
        # B4: synergy's /auth/modules/active/ is admin-only; this is not.
        employee = make_employee("Staff", ["leave.request.create"])

        assert access_of(employee.user)["active_modules"] == SEEDED_ACTIVE_MODULES

    def test_an_uninstalled_module_is_left_out(self):
        SystemModule.objects.filter(identifier="payroll").update(is_active=False)
        employee = make_employee("Afteruninstall", ["leave.request.create"])

        assert access_of(employee.user)["active_modules"] == ["accounts", "hr", "procurement"]

    def test_matches_the_admin_active_modules_listing(self):
        admin = User.objects.create_superuser(email="modadmin@zchpc.test", password=PASSWORD)

        listing = client_for(admin).get("/api/v2/auth/modules/active/").json()

        assert access_of(admin)["active_modules"] == sorted(m["identifier"] for m in listing)
