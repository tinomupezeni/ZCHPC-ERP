"""
AUD-02 F9 slice 2: position, employee type and reporting line need authority
over the employee - and nothing more.

Policy (Model B, F9 slice 2 reconnaissance): position_id, employee_type and
reports_to_id grant no runtime authority (structural_assignments: reports_to
"carries no runtime authority anywhere"; leave review consults no reporting
line; position is a display title), so they sit with F1's ordinary fields:

- the coarse hr gate is the prerequisite, and authority over the target
  (covers, on its effective permissions) is the rule - else 403
  EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY, nothing written;
- hr.employee.manage_assignments is NOT required: that capability guards
  role and department, which do carry authority, and is not broadened.

Self, peers and higher-on-lower are covered. Every case uses valid
references (a position in the target's department, an active manager who is
not the target), so a refusal can only come from authorization; the
reference rules themselves are tested in test_employee_assignment_integrity.

Every HTTP request carries a real JWT, so RBACMiddleware is on the path.
"""

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
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "PlacementPass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

VIEWER = ("hr.employee.view",)
PEER = ("hr.employee.view", "hr.employee.create")
# Covers VIEWER and PEER targets without holding manage_assignments.
SENIOR = ("hr.employee.view", "hr.employee.create", "hr.role.manage")

FIELDS = ("position_id", "employee_type", "reports_to_id")

# EmployeeId accepts only EMP + digits.
_numbers = count(90501)


def make_employee(label, *permissions, superuser=False):
    """An employee in their own department, whose role grants exactly ``permissions``."""
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
        department=Department.objects.create(name=f"Dept{next(_numbers)}"),
        employee_id=f"EMP{next(_numbers)}",
    )


def valid_change(field, target):
    """A value for ``field`` that passes every reference rule for ``target``."""
    if field == "position_id":
        return Position.objects.create(title=f"Pos{next(_numbers)}", department_id=target.department_id).pk
    if field == "employee_type":
        return "Contract"  # make_employee leaves the default, Full-time
    return make_employee("Manager", *VIEWER).pk


def valid_changes(target):
    return {field: valid_change(field, target) for field in FIELDS}


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def edit(actor, target, body):
    return client_for(actor.user).patch(f"{EMPLOYEES_URL}{target.pk}/", body, format="json")


def placement(employee):
    return Employees.objects.filter(pk=employee.pk).values(*FIELDS).get()


def assert_refused(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, getattr(response, "data", None)
    assert response.data["code"] == EXCEEDS


def assert_applied(response, target, body):
    assert response.status_code == status.HTTP_200_OK, getattr(response, "data", None)
    stored = placement(target)
    assert {field: stored[field] for field in body} == body


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


# =============================================================================
# Lower authority cannot change a higher target's placement
# =============================================================================


class TestLowerAuthorityIsRefused:
    def test_lower_authority_cannot_update_position_on_higher_authority_employee(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, {"position_id": valid_change("position_id", target)}))
        assert placement(target) == before

    def test_lower_authority_cannot_update_employee_type_on_higher_authority_employee(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, {"employee_type": valid_change("employee_type", target)}))
        assert placement(target) == before

    def test_lower_authority_cannot_update_reports_to_on_higher_authority_employee(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, {"reports_to_id": valid_change("reports_to_id", target)}))
        assert placement(target) == before

    def test_lower_authority_cannot_make_a_higher_target_report_to_themselves(self):
        """The privilege-flavoured case: re-pointing a superior under oneself."""
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, {"reports_to_id": actor.pk}))
        assert placement(target) == before

    @pytest.mark.parametrize("field", FIELDS)
    def test_a_superuser_linked_target_is_protected(self, field):
        actor, target = make_employee("Clerk", *SENIOR), make_employee("Root", superuser=True)
        before = placement(target)
        assert_refused(edit(actor, target, {field: valid_change(field, target)}))
        assert placement(target) == before

    @pytest.mark.parametrize("field", FIELDS)
    def test_a_deactivated_higher_target_stays_protected(self, field):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository()).deactivate(target.pk)
        before = placement(target)
        assert_refused(edit(actor, target, {field: valid_change(field, target)}))
        assert placement(target) == before

    @pytest.mark.parametrize("field", FIELDS)
    def test_the_assignment_capability_does_not_replace_target_authority(self, field):
        actor = make_employee("Assigner", *VIEWER, "hr.employee.manage_assignments")
        target = make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, {field: valid_change(field, target)}))
        assert placement(target) == before


# =============================================================================
# Covered targets stay editable - without manage_assignments
# =============================================================================


class TestCoveredTargetsAreEditable:
    @pytest.mark.parametrize("field", FIELDS)
    def test_peer(self, field):
        actor, target = make_employee("Peera", *PEER), make_employee("Peerb", *PEER)
        body = {field: valid_change(field, target)}
        assert_applied(edit(actor, target, body), target, body)

    @pytest.mark.parametrize("field", FIELDS)
    def test_higher_authority_on_lower(self, field):
        actor, target = make_employee("Senior", *SENIOR), make_employee("Clerk", *VIEWER)
        body = {field: valid_change(field, target)}
        assert_applied(edit(actor, target, body), target, body)

    @pytest.mark.parametrize("field", FIELDS)
    def test_self(self, field):
        actor = make_employee("Self", *VIEWER)
        body = {field: valid_change(field, actor)}
        assert_applied(edit(actor, actor, body), actor, body)

    def test_superuser(self):
        actor, target = make_employee("Root", superuser=True), make_employee("Admin", "*")
        body = valid_changes(target)
        assert_applied(edit(actor, target, body), target, body)

    def test_assignment_fields_do_not_require_manage_assignments(self):
        """Model B: covering the target is enough; manage_assignments is not broadened."""
        actor, target = make_employee("Senior", *SENIOR), make_employee("Clerk", *VIEWER)
        assert not PermissionSet.from_list(list(SENIOR)).has_permission("hr.employee.manage_assignments")
        body = valid_changes(target)
        assert_applied(edit(actor, target, body), target, body)


# =============================================================================
# A refused request changes nothing
# =============================================================================


class TestAtomicity:
    def test_assignment_field_updates_are_atomic_when_target_authority_fails(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = placement(target)
        assert_refused(edit(actor, target, valid_changes(target)))
        assert placement(target) == before

    def test_with_an_ordinary_field_the_whole_request_is_refused(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = (placement(target), Employees.objects.get(pk=target.pk).first_name)
        body = {"first_name": "Changed", **valid_changes(target)}
        assert_refused(edit(actor, target, body))
        assert (placement(target), Employees.objects.get(pk=target.pk).first_name) == before


# =============================================================================
# Enforced by the service, not the view
# =============================================================================


class TestServiceLevelEnforcement:
    @pytest.mark.parametrize("field", FIELDS)
    def test_service_refuses_a_lower_actor_without_http(self, field):
        target = make_employee("Admin", "*")
        before = placement(target)
        with pytest.raises(AuthorizationError) as raised:
            employee_service().update_employee(
                UpdateEmployeeCommand(employee_id=target.pk, **{field: valid_change(field, target)}),
                actor_permissions=PermissionSet.from_list(list(VIEWER)),
            )
        assert raised.value.code == EXCEEDS
        assert placement(target) == before
