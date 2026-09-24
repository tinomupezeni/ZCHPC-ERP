"""
Regression tests for AUD-01 R2: EmployeeDetailView PATCH/PUT allowed any
authenticated caller to set role_id/department_id on any employee's record,
with no authorization check beyond DRF's IsAuthenticated and RBACMiddleware's
coarse "does this role hold anything in the hr module" gate.

Remediation: modules.hr.application.services.employee_service.EmployeeService
._authorize_assignment_change now requires the actor's permissions
(modules.hr.application.authorization.EmployeeManagementPermissions
.MANAGE_ASSIGNMENTS = "hr.employee.manage_assignments") before a command
that sets role_id or department_id is allowed to proceed. Every other field
on UpdateEmployeeCommand is unaffected.

Two authentication styles are used deliberately:

- APIRequestFactory + force_authenticate, calling EmployeeDetailView
  directly: this bypasses RBACMiddleware the same way AUD-01's own R2
  runtime verification did, so it proves the fix holds at the application
  layer itself, independent of whatever the coarse HTTP gate happens to do
  for a given role's current permission grants (AUD-01 R1 found none of the
  seeded non-admin roles currently hold any hr.* permission at all, which
  would otherwise mask an application-layer regression by making it look
  blocked when the real reason was the unrelated middleware gate).
- APIClient with a real JWT, exercising the full request path including
  RBACMiddleware: used for the positive/negative "an actor who legitimately
  reaches the hr module" cases, which is the scenario
  EmployeeManagementPermissions actually needs to distinguish between.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.api.views.employee_views import EmployeeDetailView
from modules.hr.infrastructure.persistence.models import Department, Employees, Role

pytestmark = pytest.mark.django_db

User = get_user_model()


def employee_url(employee_id):
    return f"/api/v2/hr/employees/{employee_id}/"


def make_role(name, permissions):
    return Role.objects.create(name=name, display_name=name.title(), permissions=permissions)


def make_employee(first_name, surname, suffix, role=None, department=None):
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
        department=department,
    )


def jwt_client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


class TestApplicationLayerBlocksRoleEscalationRegardlessOfMiddleware:
    """
    Direct reproduction of AUD-01 R2's runtime-verified exploit: an ordinary
    employee PATCHing their own record with role_id set to an ADMIN role's
    id. Uses force_authenticate (bypassing RBACMiddleware) specifically so
    this proves the *application layer* - not the coarse HTTP gate - now
    refuses the change, matching the task's requirement that authorization
    cannot be bypassed simply by calling the API directly.
    """

    def test_ordinary_employee_cannot_escalate_their_own_role(self):
        admin_role = make_role("ADMIN", ["*"])
        staff_role = make_role("REGULAR_STAFF", ["procurement.purchase_request.view"])
        victim = make_employee("Riley", "Requester", "9001", role=staff_role)
        before_role_id = victim.role_id

        factory = APIRequestFactory()
        request = factory.patch(employee_url(victim.id), {"role_id": admin_role.id}, format="json")
        force_authenticate(request, user=victim.user)
        response = EmployeeDetailView.as_view()(request, employee_id=victim.id)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"

        victim.refresh_from_db()
        assert victim.role_id == before_role_id
        assert victim.role_id != admin_role.id

    def test_ordinary_employee_cannot_change_another_employees_role(self):
        admin_role = make_role("ADMIN", ["*"])
        staff_role = make_role("REGULAR_STAFF", [])
        attacker = make_employee("Sam", "Attacker", "9002", role=staff_role)
        victim = make_employee("Vic", "Target", "9003", role=staff_role)
        before_role_id = victim.role_id

        factory = APIRequestFactory()
        request = factory.patch(employee_url(victim.id), {"role_id": admin_role.id}, format="json")
        force_authenticate(request, user=attacker.user)
        response = EmployeeDetailView.as_view()(request, employee_id=victim.id)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        victim.refresh_from_db()
        assert victim.role_id == before_role_id

    def test_ordinary_employee_cannot_change_their_own_department(self):
        staff_role = make_role("REGULAR_STAFF", [])
        finance = Department.objects.create(name="Finance-9004")
        it = Department.objects.create(name="IT-9004")
        victim = make_employee("Dana", "Dept", "9004", role=staff_role, department=it)

        factory = APIRequestFactory()
        request = factory.patch(
            employee_url(victim.id), {"department_id": finance.id}, format="json"
        )
        force_authenticate(request, user=victim.user)
        response = EmployeeDetailView.as_view()(request, employee_id=victim.id)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        victim.refresh_from_db()
        assert victim.department_id == it.id

    def test_ordinary_employee_cannot_change_another_employees_department(self):
        staff_role = make_role("REGULAR_STAFF", [])
        finance = Department.objects.create(name="Finance-9005")
        it = Department.objects.create(name="IT-9005")
        attacker = make_employee("Sam", "Attacker", "9005a", role=staff_role, department=it)
        victim = make_employee("Vic", "Target", "9005b", role=staff_role, department=it)

        factory = APIRequestFactory()
        request = factory.patch(
            employee_url(victim.id), {"department_id": finance.id}, format="json"
        )
        force_authenticate(request, user=attacker.user)
        response = EmployeeDetailView.as_view()(request, employee_id=victim.id)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        victim.refresh_from_db()
        assert victim.department_id == it.id


class TestNonAssignmentFieldsRemainUnaffected:
    """
    The fix must be field-specific: it should not block an employee (or
    anyone else who currently reaches this endpoint) from updating fields
    that were never part of the vulnerability.
    """

    def test_ordinary_employee_can_still_update_their_own_phone_number(self):
        staff_role = make_role("REGULAR_STAFF", [])
        employee = make_employee("Pat", "Phoneowner", "9006", role=staff_role)

        factory = APIRequestFactory()
        request = factory.patch(
            employee_url(employee.id), {"phone": "+263771234567"}, format="json"
        )
        force_authenticate(request, user=employee.user)
        response = EmployeeDetailView.as_view()(request, employee_id=employee.id)
        if hasattr(response, "render"):
            response.render()

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.phone == "+263771234567"


class TestFullRequestPathThroughRbacMiddleware:
    """
    End-to-end coverage through the real URL routing + RBACMiddleware +
    EmployeeDetailView + EmployeeService chain, for an actor whose role
    legitimately reaches the hr module (holds some hr.* permission) but not
    the specific assignment capability - the exact scenario
    EmployeeManagementPermissions exists to distinguish, since simply
    reaching /api/v2/hr/* was never proof of authority to reassign roles.
    """

    def test_narrow_hr_permission_reaches_the_endpoint_but_cannot_reassign_role(self):
        admin_role = make_role("ADMIN-9007", ["*"])
        narrow_role = make_role("HR_DATA_ENTRY-9007", ["hr.employee.view"])
        actor = make_employee("Nora", "NarrowHr", "9007", role=narrow_role)

        client = jwt_client_for(actor)
        response = client.patch(
            employee_url(actor.id), {"role_id": admin_role.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == "EMPLOYEE_ASSIGNMENT_NOT_AUTHORIZED"
        actor.refresh_from_db()
        assert actor.role_id == narrow_role.id

    def test_narrow_hr_permission_can_still_update_ordinary_fields(self):
        narrow_role = make_role("HR_DATA_ENTRY-9008", ["hr.employee.view"])
        actor = make_employee("Nora", "NarrowHr", "9008", role=narrow_role)

        client = jwt_client_for(actor)
        response = client.patch(
            employee_url(actor.id), {"surname": "NarrowHrUpdated"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        actor.refresh_from_db()
        assert actor.surname == "NarrowHrUpdated"


class TestAuthorizedHrAdminCanStillReassignRoleAndDepartment:
    """
    Positive control: the intended workflow (an actor explicitly granted
    the new capability performs a legitimate reassignment, including on
    someone else's record) still works end to end.
    """

    def test_actor_with_manage_assignments_permission_can_reassign_another_employees_role(self):
        target_role = make_role("ACCOUNTANT-9009", ["procurement.purchase_request.view"])
        hr_admin_role = make_role(
            "HR_ADMIN-9009", ["hr.employee.manage_assignments"]
        )
        hr_admin = make_employee("Helen", "Admin", "9009", role=hr_admin_role)
        employee = make_employee("Evan", "Employee", "9109", role=None)

        client = jwt_client_for(hr_admin)
        response = client.patch(
            employee_url(employee.id), {"role_id": target_role.id}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.role_id == target_role.id

    def test_actor_with_manage_assignments_permission_can_reassign_department(self):
        hr_admin_role = make_role(
            "HR_ADMIN-9010", ["hr.employee.manage_assignments"]
        )
        new_department = Department.objects.create(name="Engineering-9010")
        hr_admin = make_employee("Helen", "Admin", "9010", role=hr_admin_role)
        employee = make_employee("Evan", "Employee", "9110", role=None)

        client = jwt_client_for(hr_admin)
        response = client.patch(
            employee_url(employee.id),
            {"department_id": new_department.id},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.department_id == new_department.id

    def test_hr_dot_star_wildcard_also_grants_the_capability(self):
        """
        Permission.matches() already implements app-level wildcards; a role
        deliberately granted the full hr.* wildcard is presumably meant to
        have complete HR authority, so it must not be excluded by this
        narrower, more specific check.
        """
        target_role = make_role("ACCOUNTANT-9011", [])
        hr_wildcard_role = make_role("HR_MANAGER-9011", ["hr.*"])
        hr_admin = make_employee("Wanda", "Wildcard", "9011", role=hr_wildcard_role)
        employee = make_employee("Evan", "Employee", "9111", role=None)

        client = jwt_client_for(hr_admin)
        response = client.patch(
            employee_url(employee.id), {"role_id": target_role.id}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.role_id == target_role.id

    def test_admin_full_wildcard_can_reassign_their_own_role(self):
        """
        An ADMIN actor changing their own role/department is not the
        vulnerability this remediation targets (AUD-01 R2's finding and the
        prompt's security requirements are about *ordinary* employees
        escalating themselves); a holder of the full "*" wildcard must
        continue to be able to perform legitimate self-administration.
        """
        admin_role = make_role("ADMIN-9012", ["*"])
        other_role = make_role("ACCOUNTANT-9012", [])
        admin = make_employee("Adam", "Admin", "9012", role=admin_role)

        client = jwt_client_for(admin)
        response = client.patch(
            employee_url(admin.id), {"role_id": other_role.id}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        admin.refresh_from_db()
        assert admin.role_id == other_role.id


class TestSuperuserWithNoEmployeeProfileRetainsAssignmentAccess:
    """
    REM-05 review finding: this endpoint previously resolved actor
    permissions via permission_set_for_user(request.user) or
    PermissionSet.empty() alone, with no is_superuser check - unlike
    RBACMiddleware's own unconditional superuser bypass. A superuser with
    no linked Employees record (AUD-01 found exactly this live) would
    therefore have been incorrectly denied. Both this file's view
    (employee_views.py) and modules.hr.application.services
    .role_service's view now resolve permissions via the same shared
    modules.hr.application.authorization.resolve_actor_permissions,
    which restores the bypass here too.
    """

    def test_superuser_with_no_employee_profile_can_reassign_an_employees_role(self):
        superuser = User.objects.create_superuser(
            email="rem05.review.superuser@zchpc.test", password="x"
        )
        assert not Employees.objects.filter(user=superuser).exists()

        target_role = make_role("SUPERUSER_TARGET_ROLE", [])
        employee = make_employee("Target", "Employee", "9501", role=None)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(superuser)}")
        response = client.patch(
            employee_url(employee.id), {"role_id": target_role.id}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.role_id == target_role.id

    def test_superuser_with_no_employee_profile_can_reassign_an_employees_department(self):
        from modules.hr.infrastructure.persistence.models import Department

        superuser = User.objects.create_superuser(
            email="rem05.review.superuser2@zchpc.test", password="x"
        )
        assert not Employees.objects.filter(user=superuser).exists()

        target_department = Department.objects.create(name="Superuser Target Dept")
        employee = make_employee("Target", "Employee", "9502", role=None)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(superuser)}")
        response = client.patch(
            employee_url(employee.id),
            {"department_id": target_department.id},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        employee.refresh_from_db()
        assert employee.department_id == target_department.id
