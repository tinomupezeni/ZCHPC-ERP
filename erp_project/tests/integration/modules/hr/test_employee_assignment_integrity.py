"""
AUD-02 F9 (slice 3): assignment references must exist and agree.

Creating an employee already checks that the department and position exist
and that the position belongs to the department (POSITION_DEPARTMENT_MISMATCH).
Updating did not: an unknown department, position or manager reached the
database and failed there (500), and a position from another department was
stored. Both paths now hold the same invariants:

- department_id, position_id and reports_to_id name records that exist
  (404 otherwise, nothing written);
- a position given belongs to the employee's department - the one in the
  same request, or the one they are in (POSITION_DEPARTMENT_MISMATCH);
- reports_to keeps its existing rules: not yourself (INVALID_REPORTS_TO),
  not an archived employee; a deactivated manager is allowed.

Who may change these fields is not decided here (see the F9 report). The
actor is a full-access employee throughout. reports_to cycles are not
judged either: that is an open business decision.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Department, Employees, Position, Role

User = get_user_model()

PASSWORD = "AssignPass12345!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
MISSING = 987654

# EmployeeId accepts only EMP + digits.
_numbers = count(92501)


def make_employee(label, *permissions, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    user = User.objects.create_user(email=email, password=PASSWORD)
    role = None
    if permissions:
        role = Role.objects.create(
            name=f"ROLE_{label}_{next(_numbers)}", display_name=label, permissions=list(permissions)
        )
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, role=role,
        employee_id=f"EMP{next(_numbers)}", **extra,
    )


def department():
    return Department.objects.create(name=f"Dept{next(_numbers)}")


def position(dept=None):
    return Position.objects.create(title=f"Pos{next(_numbers)}", department=dept)


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def edit(actor, target, body):
    return client_for(actor.user).patch(f"{EMPLOYEES_URL}{target.pk}/", body, format="json")


def create(actor, **body):
    email = f"hire{next(_numbers)}@zchpc.test"
    response = client_for(actor.user).post(
        EMPLOYEES_URL, {"first_name": "New", "surname": "Hire", "email": email, **body}, format="json"
    )
    return response, email


def snapshot(employee):
    return Employees.objects.filter(pk=employee.pk).values(
        "first_name", "department_id", "position_id", "reports_to_id", "employee_type"
    ).get()


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


# =============================================================================
# Unknown references are 404, and nothing is written
# =============================================================================


@pytest.mark.django_db(transaction=True)
class TestUnknownReferences:
    @pytest.mark.parametrize("field", ["position_id", "department_id", "reports_to_id"])
    def test_on_update(self, field):
        boss = make_employee("Boss", "*")
        target = make_employee("Target", "hr.employee.view")
        before = snapshot(target)
        response = edit(boss, target, {"first_name": "Changed", field: MISSING})
        assert response.status_code == status.HTTP_404_NOT_FOUND, getattr(response, "data", None)
        assert snapshot(target) == before

    def test_reports_to_on_create(self):
        response, email = create(make_employee("Boss", "*"), reports_to_id=MISSING)
        assert response.status_code == status.HTTP_404_NOT_FOUND, getattr(response, "data", None)
        assert not Employees.objects.filter(email=email).exists()
        assert not User.objects.filter(email=email).exists()

    @pytest.mark.parametrize("field", ["position_id", "department_id"])
    def test_on_create_already_404(self, field):
        response, email = create(make_employee("Boss", "*"), **{field: MISSING})
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not Employees.objects.filter(email=email).exists()


# =============================================================================
# A position belongs to the employee's department
# =============================================================================


@pytest.mark.django_db
class TestPositionBelongsToDepartment:
    def test_update_to_another_departments_position(self):
        boss = make_employee("Boss", "*")
        home, other = department(), department()
        target = make_employee("Target", "hr.employee.view", department=home)
        before = snapshot(target)
        response = edit(boss, target, {"position_id": position(other).pk})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "POSITION_DEPARTMENT_MISMATCH"
        assert snapshot(target) == before

    def test_update_with_a_department_the_position_is_not_in(self):
        boss = make_employee("Boss", "*")
        home, other = department(), department()
        target = make_employee("Target", "hr.employee.view", department=home)
        response = edit(boss, target, {"department_id": other.pk, "position_id": position(home).pk})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert response.data["code"] == "POSITION_DEPARTMENT_MISMATCH"

    def test_update_to_a_position_in_their_department(self):
        boss = make_employee("Boss", "*")
        home = department()
        target = make_employee("Target", "hr.employee.view", department=home)
        role_position = position(home)
        assert edit(boss, target, {"position_id": role_position.pk}).status_code == status.HTTP_200_OK
        assert snapshot(target)["position_id"] == role_position.pk

    def test_moving_department_and_position_together(self):
        boss = make_employee("Boss", "*")
        home, other = department(), department()
        target = make_employee("Target", "hr.employee.view", department=home)
        new_position = position(other)
        response = edit(boss, target, {"department_id": other.pk, "position_id": new_position.pk})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert (snapshot(target)["department_id"], snapshot(target)["position_id"]) == (
            other.pk, new_position.pk,
        )

    def test_create_already_refuses_a_mismatch(self):
        home, other = department(), department()
        response, _ = create(make_employee("Boss", "*"), department_id=home.pk, position_id=position(other).pk)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "POSITION_DEPARTMENT_MISMATCH"


# =============================================================================
# reports_to keeps its existing rules
# =============================================================================


@pytest.mark.django_db
class TestReportsToRulesAreKept:
    def test_not_yourself(self):
        boss = make_employee("Boss", "*")
        target = make_employee("Target", "hr.employee.view")
        response = edit(boss, target, {"reports_to_id": target.pk})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "INVALID_REPORTS_TO"

    def test_not_an_archived_employee(self):
        boss = make_employee("Boss", "*")
        target, manager = make_employee("Target", "hr.employee.view"), make_employee("Gone", "hr.employee.view")
        lifecycle().archive(manager.pk)
        response = edit(boss, target, {"reports_to_id": manager.pk})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"

    def test_a_deactivated_manager_is_allowed(self):
        boss = make_employee("Boss", "*")
        target, manager = make_employee("Target", "hr.employee.view"), make_employee("Away", "hr.employee.view")
        lifecycle().deactivate(manager.pk)
        assert edit(boss, target, {"reports_to_id": manager.pk}).status_code == status.HTTP_200_OK
        assert snapshot(target)["reports_to_id"] == manager.pk

    def test_an_existing_active_manager(self):
        boss = make_employee("Boss", "*")
        target, manager = make_employee("Target", "hr.employee.view"), make_employee("Lead", "hr.employee.view")
        assert edit(boss, target, {"reports_to_id": manager.pk}).status_code == status.HTTP_200_OK


# =============================================================================
# employee_type keeps its validation
# =============================================================================


@pytest.mark.django_db
class TestEmployeeType:
    def test_an_unknown_value_is_a_400(self):
        boss = make_employee("Boss", "*")
        target = make_employee("Target", "hr.employee.view")
        assert edit(boss, target, {"employee_type": "Volunteer"}).status_code == status.HTTP_400_BAD_REQUEST

    def test_a_known_value(self):
        boss = make_employee("Boss", "*")
        target = make_employee("Target", "hr.employee.view")
        assert edit(boss, target, {"employee_type": "Contract"}).status_code == status.HTTP_200_OK
