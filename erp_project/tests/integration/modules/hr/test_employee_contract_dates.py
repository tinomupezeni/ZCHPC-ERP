"""
AUD-02 F9: employee contract dates (contract_from, contract_to).

Create stored the dates as given, with no ordering check. Update accepted
them (200) and dropped them: EmployeeService.update_employee never read
them, although the domain already defines Employee.update_contract - with
its INVALID_CONTRACT_DATES rule - and ContractUpdatedEvent for exactly that.

Approved for this slice:

- the dates are ordinary employee attributes: changing another employee's
  needs authority over them (covers), no capability - manage_assignments is
  neither needed nor enough;
- the domain's rule holds on create and update alike: contract_to before
  contract_from is 400 INVALID_CONTRACT_DATES, nothing written; equal dates
  are valid;
- null and omission keep today's meaning ("not mentioned"), and the dates
  are still not returned by the API - both deliberately unchanged here.

Stored values are read from the database because no response carries them.
Every HTTP request carries a real JWT, so RBACMiddleware is on the path.
"""

from datetime import date
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeService, UpdateEmployeeCommand
from modules.hr.domain.events import ContractUpdatedEvent
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.domain.value_objects import PermissionSet

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "ContractPass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
INVALID = "INVALID_CONTRACT_DATES"

VIEWER = ("hr.employee.view",)
SENIOR = ("hr.employee.view", "hr.employee.create", "hr.role.manage")

JAN_2026, DEC_2026 = date(2026, 1, 1), date(2026, 12, 31)

# EmployeeId accepts only EMP + digits.
_numbers = count(89501)

# Fixed by the next commit ("enforce contract date integrity").
F9_FIX = pytest.mark.xfail(strict=True, reason="AUD-02 F9 contract dates: not yet fixed")


def make_employee(label, *permissions, superuser=False, **extra):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
    if superuser:
        user = User.objects.create_superuser(email=email, password=PASSWORD)
    else:
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


def on_contract(label="Target", *permissions):
    """An employee already holding a 2026 contract."""
    return make_employee(label, *(permissions or VIEWER), contract_from=JAN_2026, contract_to=DEC_2026)


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def edit(actor, target, body):
    return client_for(actor.user).patch(f"{EMPLOYEES_URL}{target.pk}/", body, format="json")


def contract(employee):
    row = Employees.objects.filter(pk=employee.pk).values("contract_from", "contract_to").get()
    return row["contract_from"], row["contract_to"]


def assert_status(response, expected):
    assert response.status_code == expected, getattr(response, "data", None)


class RecordingBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


def employee_service(event_bus=None):
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
        event_bus=event_bus,
    )


# =============================================================================
# Update: valid dates are stored
# =============================================================================


class TestUpdateStoresDates:
    @F9_FIX
    def test_both_dates(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {"contract_from": "2027-01-01", "contract_to": "2027-12-31"}), 200)
        assert contract(target) == (date(2027, 1, 1), date(2027, 12, 31))

    @F9_FIX
    def test_only_contract_from(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {"contract_from": "2026-06-01"}), 200)
        assert contract(target) == (date(2026, 6, 1), DEC_2026)

    @F9_FIX
    def test_only_contract_to(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {"contract_to": "2027-06-30"}), 200)
        assert contract(target) == (JAN_2026, date(2027, 6, 30))

    @F9_FIX
    def test_equal_dates_are_valid(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {"contract_from": "2027-03-01", "contract_to": "2027-03-01"}), 200)
        assert contract(target) == (date(2027, 3, 1), date(2027, 3, 1))

    @F9_FIX
    def test_other_fields_are_untouched(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        before = Employees.objects.filter(pk=target.pk).values("first_name", "surname", "phone").get()
        assert_status(edit(boss, target, {"contract_to": "2027-06-30"}), 200)
        assert Employees.objects.filter(pk=target.pk).values("first_name", "surname", "phone").get() == before
        assert contract(target) == (JAN_2026, date(2027, 6, 30))

    def test_the_response_still_carries_no_contract_dates(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        response = edit(boss, target, {"contract_to": "2027-06-30"})
        assert "contract_from" not in response.data and "contract_to" not in response.data


# =============================================================================
# Update: the domain's ordering rule, judged on the resulting dates
# =============================================================================


class TestUpdateOrdering:
    @F9_FIX
    def test_end_before_start_in_one_request(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        response = edit(boss, target, {"contract_from": "2027-06-01", "contract_to": "2027-01-01"})
        assert_status(response, 400)
        assert response.data["code"] == INVALID
        assert contract(target) == (JAN_2026, DEC_2026)

    @F9_FIX
    def test_an_end_before_the_existing_start(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        response = edit(boss, target, {"contract_to": "2025-12-31"})
        assert_status(response, 400)
        assert response.data["code"] == INVALID
        assert contract(target) == (JAN_2026, DEC_2026)

    @F9_FIX
    def test_a_start_after_the_existing_end(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        response = edit(boss, target, {"contract_from": "2027-01-01"})
        assert_status(response, 400)
        assert response.data["code"] == INVALID
        assert contract(target) == (JAN_2026, DEC_2026)

    @F9_FIX
    def test_a_refusal_writes_nothing_else_in_the_request(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        response = edit(boss, target, {"first_name": "Changed", "contract_to": "2025-12-31"})
        assert_status(response, 400)
        assert Employees.objects.get(pk=target.pk).first_name == "Target"


# =============================================================================
# Null and omission keep today's meaning
# =============================================================================


class TestNullAndOmissionAreUnchanged:
    @pytest.mark.parametrize("field", ["contract_from", "contract_to"])
    def test_null_leaves_the_date_as_it_is(self, field):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {field: None}), 200)
        assert contract(target) == (JAN_2026, DEC_2026)

    def test_omitting_them_leaves_them_as_they_are(self):
        boss, target = make_employee("Boss", "*"), on_contract()
        assert_status(edit(boss, target, {"phone": "0771234567"}), 200)
        assert contract(target) == (JAN_2026, DEC_2026)


# =============================================================================
# Authorization: covers(target), no capability
# =============================================================================


class TestAuthorization:
    @F9_FIX
    def test_self(self):
        actor = on_contract("Self", *VIEWER)
        assert_status(edit(actor, actor, {"contract_to": "2027-06-30"}), 200)
        assert contract(actor)[1] == date(2027, 6, 30)

    @F9_FIX
    def test_a_covered_target_without_manage_assignments(self):
        actor, target = make_employee("Senior", *SENIOR), on_contract("Clerk", *VIEWER)
        assert_status(edit(actor, target, {"contract_to": "2027-06-30"}), 200)
        assert contract(target)[1] == date(2027, 6, 30)

    @F9_FIX
    @pytest.mark.parametrize(
        "permissions",
        [VIEWER, (*VIEWER, "hr.employee.manage_assignments")],
        ids=["lower", "lower-with-manage-assignments"],
    )
    def test_a_target_not_covered_is_refused(self, permissions):
        actor, target = make_employee("Clerk", *permissions), on_contract("Admin", "*")
        response = edit(actor, target, {"contract_from": "2026-02-01", "contract_to": "2026-11-30"})
        assert_status(response, 403)
        assert response.data["code"] == EXCEEDS
        assert contract(target) == (JAN_2026, DEC_2026)

    @F9_FIX
    def test_superuser(self):
        actor, target = make_employee("Root", superuser=True), on_contract("Admin", "*")
        assert_status(edit(actor, target, {"contract_to": "2027-06-30"}), 200)
        assert contract(target)[1] == date(2027, 6, 30)


# =============================================================================
# Create: the same rule
# =============================================================================


class TestCreate:
    def _create(self, **dates):
        email = f"hire{next(_numbers)}@zchpc.test"
        response = client_for(make_employee("Boss", "*").user).post(
            EMPLOYEES_URL, {"first_name": "New", "surname": "Hire", "email": email, **dates}, format="json"
        )
        return response, email

    def test_valid_dates_are_stored(self):
        response, email = self._create(contract_from="2026-01-01", contract_to="2026-12-31")
        assert_status(response, 201)
        assert contract(Employees.objects.get(email=email)) == (JAN_2026, DEC_2026)

    def test_equal_dates_are_valid(self):
        response, _ = self._create(contract_from="2026-01-01", contract_to="2026-01-01")
        assert_status(response, 201)

    @F9_FIX
    def test_end_before_start_is_refused_and_nothing_is_created(self):
        response, email = self._create(contract_from="2026-12-31", contract_to="2026-01-01")
        assert_status(response, 400)
        assert response.data["code"] == INVALID
        assert not Employees.objects.filter(email=email).exists()
        assert not User.objects.filter(email=email).exists()


# =============================================================================
# The domain's ContractUpdatedEvent
# =============================================================================


class TestContractUpdatedEvent:
    @F9_FIX
    def test_published_when_the_dates_are_updated(self):
        target, bus = on_contract(), RecordingBus()
        employee_service(bus).update_employee(
            UpdateEmployeeCommand(employee_id=target.pk, contract_to=date(2027, 6, 30)),
            actor_permissions=PermissionSet.full_access(),
        )
        events = [e for e in bus.events if isinstance(e, ContractUpdatedEvent)]
        assert len(events) == 1
        assert (events[0].employee_id, events[0].contract_from, events[0].contract_to) == (
            target.pk, JAN_2026, date(2027, 6, 30),
        )

    def test_not_published_for_other_changes(self):
        target, bus = on_contract(), RecordingBus()
        employee_service(bus).update_employee(
            UpdateEmployeeCommand(employee_id=target.pk, surname="Changed"),
            actor_permissions=PermissionSet.full_access(),
        )
        assert not [e for e in bus.events if isinstance(e, ContractUpdatedEvent)]
