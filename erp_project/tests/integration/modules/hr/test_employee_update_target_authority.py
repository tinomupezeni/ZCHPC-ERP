"""
AUD-02 F1: editing another employee's ordinary fields needs authority over them.

PATCH/PUT /api/v2/hr/employees/<id>/ carrying any ordinary field - first_name,
surname, date_of_birth, gender, marital_status, phone, emergency contact -
needs the actor to cover the employee as they stand (PermissionSet.covers on
EmployeeService._effective_permissions), the same target authority F7 put on
renaming another login. There is no capability for it: reaching the hr routes
is the prerequisite. Refusal is 403 EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY,
decided before anything is written.

Self and peers are covered; is_staff is not authority; an archived employee
is refused as EMPLOYEE_ARCHIVED before authority is judged. Position,
employee type, reports_to and email are outside this slice.

Every HTTP request carries a real JWT, so RBACMiddleware is on the path.
"""

from datetime import date
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import (
    EmployeeLifecycleService,
    EmployeeService,
    UpdateEmployeeCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Position, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.domain.value_objects import PermissionSet
from modules.payroll.infrastructure.persistence.models import PayrollProfile
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "UpdateAuthPass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

# One request per ordinary field, so each is shown to be protected on its own.
ORDINARY_EDITS = {
    "first_name": {"first_name": "Changed"},
    "surname": {"surname": "Changed"},
    "date_of_birth": {"date_of_birth": "1980-01-01"},
    "gender": {"gender": "Other"},
    "marital_status": {"marital_status": "Widowed"},
    "phone": {"phone": "0779999999"},
    "emergency_contact_name": {"emergency_contact_name": "Changed"},
    "emergency_contact_number": {"emergency_contact_number": "0778888888"},
    "emergency_contact_relationship": {"emergency_contact_relationship": "Changed"},
}

# EmployeeId accepts only EMP + digits.
_numbers = count(95001)


def make_employee(label, *permissions, staff=False, superuser=False, login=True):
    """An employee whose role grants exactly ``permissions`` (and a login unless told not to)."""
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    user = None
    if login:
        if superuser:
            user = User.objects.create_superuser(email=email, password=PASSWORD)
        else:
            user = User.objects.create_user(email=email, password=PASSWORD, is_staff=staff)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    return Employees.objects.create(
        user=user,
        first_name=label,
        surname="Person",
        email=email,
        phone="0771234567",
        role=role,
        employee_id=f"EMP{next(_numbers)}",
    )


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def edit(actor, target, body):
    return client_for(actor.user).patch(f"{EMPLOYEES_URL}{target.pk}/", body, format="json")


def snapshot(employee):
    row = Employees.objects.get(pk=employee.pk)
    return (
        row.first_name, row.surname, row.date_of_birth, row.gender, row.marital_status,
        row.phone, row.emergency_contact_name, row.emergency_contact_number,
        row.emergency_contact_relationship, row.position_id, row.role_id, row.department_id,
        row.reports_to_id,
    )


def assert_refused(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
    assert response.data["code"] == EXCEEDS


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


# =============================================================================
# Lower authority cannot edit a higher target
# =============================================================================


class TestLowerAuthorityIsRefused:
    @pytest.mark.parametrize("field", list(ORDINARY_EDITS))
    def test_each_ordinary_field_is_protected(self, field):
        actor = make_employee("Clerk", "hr.employee.create")
        target = make_employee("Admin", "*")
        before = snapshot(target)
        assert_refused(edit(actor, target, ORDINARY_EDITS[field]))
        assert snapshot(target) == before

    def test_view_only_actor_cannot_edit_a_full_access_employee(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Admin", "*")
        assert_refused(edit(actor, target, {"first_name": "Renamed", "phone": "0770000000"}))
        assert Employees.objects.get(pk=target.pk).first_name == "Admin"

    def test_cannot_edit_a_superuser_linked_employee(self):
        actor = make_employee("Rolemanager", "hr.role.manage", "hr.employee.view")
        target = make_employee("Root", superuser=True)
        assert_refused(edit(actor, target, {"surname": "Pwned"}))
        assert Employees.objects.get(pk=target.pk).surname == "Person"

    def test_cannot_edit_a_full_access_employee_without_a_login(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Nologin", "*", login=False)
        assert_refused(edit(actor, target, {"first_name": "Renamed"}))
        assert Employees.objects.get(pk=target.pk).first_name == "Nologin"

    def test_one_unheld_permission_is_enough_to_protect_the_target(self):
        actor = make_employee("Clerk", "hr.employee.view", "hr.employee.create")
        target = make_employee("Peerplus", "hr.employee.view", "hr.employee.create", "hr.role.manage")
        assert_refused(edit(actor, target, {"phone": "0770000000"}))

    def test_put_is_judged_like_patch(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Admin", "*")
        response = client_for(actor.user).put(
            f"{EMPLOYEES_URL}{target.pk}/", {"first_name": "Renamed"}, format="json"
        )
        assert_refused(response)

    def test_resending_current_values_is_still_judged(self):
        """Operation-oriented, like F7's rename: sending the field is what counts."""
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Admin", "*")
        assert_refused(edit(actor, target, {"first_name": "Admin", "phone": "0771234567"}))


# =============================================================================
# Covered targets stay editable
# =============================================================================


class TestCoveredTargetsAreEditable:
    def test_equal_authority(self):
        actor = make_employee("Peera", "hr.employee.view", "hr.employee.create")
        target = make_employee("Peerb", "hr.employee.view", "hr.employee.create")
        response = edit(actor, target, {"first_name": "Edited", "phone": "0770000001"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Employees.objects.get(pk=target.pk).first_name == "Edited"

    def test_higher_authority_on_lower(self):
        actor = make_employee("Manager", "hr.employee.*")
        target = make_employee("Clerk", "hr.employee.view")
        response = edit(actor, target, {"surname": "Edited", "marital_status": "Married"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Employees.objects.get(pk=target.pk).surname == "Edited"

    def test_target_holding_nothing_is_covered_by_anyone_past_the_gate(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Norole")
        response = edit(actor, target, {"first_name": "Edited"})
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_self(self):
        actor = make_employee("Self", "hr.employee.view")
        response = edit(actor, actor, {"first_name": "Myself", "phone": "0770000002"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Employees.objects.get(pk=actor.pk).first_name == "Myself"

    def test_full_access_role_on_full_access_target(self):
        actor = make_employee("Admina", "*")
        target = make_employee("Adminb", "*")
        assert edit(actor, target, {"first_name": "Edited"}).status_code == status.HTTP_200_OK

    def test_superuser_on_any_target(self):
        actor = make_employee("Root", superuser=True)
        for target in (make_employee("Admin", "*"), make_employee("Rootb", superuser=True)):
            response = edit(actor, target, {"first_name": "Edited"})
            assert response.status_code == status.HTTP_200_OK, response.data
            assert Employees.objects.get(pk=target.pk).first_name == "Edited"


# =============================================================================
# Platform flag and gate
# =============================================================================


class TestStaffFlagIsNotTargetAuthority:
    def test_staff_with_an_hr_grant_cannot_edit_a_higher_target(self):
        actor = make_employee("Staff", "hr.department.manage", staff=True)
        target = make_employee("Admin", "*")
        assert_refused(edit(actor, target, {"first_name": "Renamed"}))

    def test_staff_without_a_role_is_stopped_at_the_gate(self):
        staff = User.objects.create_user(
            email=f"staff{next(_numbers)}@zchpc.test", password=PASSWORD, is_staff=True
        )
        target = make_employee("Target")
        response = client_for(staff).patch(
            f"{EMPLOYEES_URL}{target.pk}/", {"first_name": "Renamed"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# Lifecycle
# =============================================================================


class TestLifecycle:
    def test_a_deactivated_higher_target_stays_protected(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Admin", "*")
        lifecycle().deactivate(target.pk)
        assert_refused(edit(actor, target, {"first_name": "Renamed"}))

    def test_a_deactivated_covered_target_stays_editable(self):
        actor = make_employee("Manager", "hr.employee.*")
        target = make_employee("Clerk", "hr.employee.view")
        lifecycle().deactivate(target.pk)
        assert edit(actor, target, {"phone": "0770000003"}).status_code == status.HTTP_200_OK

    @pytest.mark.parametrize("permissions", [["hr.employee.view"], ["*"]], ids=["lower", "full"])
    def test_archived_is_refused_as_archived_before_authority(self, permissions):
        actor = make_employee("Actor", *permissions)
        target = make_employee("Admin", "*")
        lifecycle().archive(target.pk)
        response = edit(actor, target, {"first_name": "Renamed"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"


# =============================================================================
# A refused request changes nothing
# =============================================================================


class TestMixedRequestsAreAtomic:
    def test_ordinary_plus_unchecked_field_writes_neither(self):
        actor = make_employee("Viewer", "hr.employee.view")
        target = make_employee("Admin", "*")
        position = Position.objects.create(title=f"Pos{next(_numbers)}")
        before = snapshot(target)
        assert_refused(edit(actor, target, {"first_name": "Renamed", "position_id": position.pk}))
        assert snapshot(target) == before

    def test_ordinary_plus_authorized_payroll_change_writes_neither(self):
        actor = make_employee("Payrollclerk", "hr.employee.view", "payroll.profile.manage")
        target = make_employee("Admin", "*")
        PayrollProfile.objects.create(employee=target, usd_salary=Decimal("1000.00"))
        before = snapshot(target)
        response = edit(actor, target, {"first_name": "Renamed", "usd_salary": "9999.00"})
        assert_refused(response)
        assert snapshot(target) == before
        assert PayrollProfile.objects.get(employee=target).usd_salary == Decimal("1000.00")

    def test_ordinary_plus_role_change_writes_neither(self):
        actor = make_employee(
            "Assigner", "hr.employee.view", "hr.employee.manage_assignments"
        )
        target = make_employee("Admin", "*")
        narrow = Role.objects.create(
            name=f"NARROW_{next(_numbers)}", display_name="Narrow", permissions=["hr.employee.view"]
        )
        before = snapshot(target)
        response = edit(actor, target, {"first_name": "Renamed", "role_id": narrow.pk})
        assert_refused(response)
        assert snapshot(target) == before


# =============================================================================
# Enforced by the service, not the view
# =============================================================================


class TestServiceLevelEnforcement:
    def test_service_refuses_a_lower_actor_without_http(self):
        target = make_employee("Admin", "*")
        with pytest.raises(AuthorizationError) as raised:
            employee_service().update_employee(
                UpdateEmployeeCommand(employee_id=target.pk, first_name="Renamed"),
                actor_permissions=PermissionSet.from_list(["hr.employee.view"]),
            )
        assert raised.value.code == EXCEEDS
        assert Employees.objects.get(pk=target.pk).first_name == "Admin"

    def test_service_with_no_permissions_cannot_edit_a_role_holder(self):
        target = make_employee("Clerk", "hr.employee.view")
        with pytest.raises(AuthorizationError):
            employee_service().update_employee(
                UpdateEmployeeCommand(employee_id=target.pk, date_of_birth=date(1990, 1, 1)),
                actor_permissions=PermissionSet.empty(),
            )

    def test_service_allows_a_covering_actor(self):
        target = make_employee("Clerk", "hr.employee.view")
        employee = employee_service().update_employee(
            UpdateEmployeeCommand(employee_id=target.pk, surname="Edited"),
            actor_permissions=PermissionSet.from_list(["hr.employee.*"]),
        )
        assert employee.surname == "Edited"

    def test_fields_outside_f1_are_not_judged_by_it(self):
        """position, employee type and reports_to keep today's rules (F9's to decide)."""
        target = make_employee("Admin", "*")
        # A position always has a department (domain rule, checked on update
        # since AUD-02 F9); the target has none, so any department fits.
        position = Position.objects.create(
            title=f"Pos{next(_numbers)}",
            department=Department.objects.create(name=f"Dept{next(_numbers)}"),
        )
        employee = employee_service().update_employee(
            UpdateEmployeeCommand(
                employee_id=target.pk, position_id=position.pk, employee_type="Contract"
            ),
            actor_permissions=PermissionSet.from_list(["hr.employee.view"]),
        )
        assert employee.position_id == position.pk
