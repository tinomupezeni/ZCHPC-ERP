"""
AUD-02 F8: the BFF profile write is held to the HR API's target authority.

PUT /api/v2/bff/employees/<uuid>/ used to write first_name, surname and phone
straight through the ORM, so any holder of a bff.* grant could change them on
anyone - bypassing F1, which refuses the same edit on PATCH /hr/employees/<id>/.
Those three fields now go through EmployeeService.update_employee, so the BFF
inherits F1 exactly: editing another employee's needs covering them, else 403
EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY, and nothing in the request - payroll
sections included - is written.

Out of this slice: the employee email (classified later, by F9), payroll's own
target rule, and the frontend's call shape.

Every request carries a real JWT, so RBACMiddleware is on the path.
"""

from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.bff.orchestrators.employee_orchestrator import EmployeeOrchestrator
from modules.hr.application.services import EmployeeLifecycleService
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.identity.domain.value_objects import PermissionSet
from modules.payroll.application.authorization import PayrollActor
from modules.payroll.infrastructure.persistence.models import EmployeeBankAccount, PayrollProfile
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "BffAuthPass123!"
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
BFF = "bff.employee.view"  # any bff.* grant opens the route

F8_EDITS = {
    "first_name": {"first_name": "Changed"},
    "surname": {"surname": "Changed"},
    "phone": {"phone": "0779999999"},
}

# EmployeeId accepts only EMP + digits.
_numbers = count(94001)


def make_employee(label, *permissions, staff=False, superuser=False):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
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


def bff_put(actor, target, body):
    return client_for(actor.user).put(f"/api/v2/bff/employees/{target.uuid}/", body, format="json")


def hr_patch(actor, target, body):
    return client_for(actor.user).patch(f"/api/v2/hr/employees/{target.pk}/", body, format="json")


def snapshot(employee):
    return Employees.objects.filter(pk=employee.pk).values(
        "first_name", "surname", "phone", "email", "role_id", "department_id"
    ).get()


def assert_refused(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
    assert response.data["code"] == EXCEEDS


def lifecycle():
    return EmployeeLifecycleService(employee_repository=DjangoEmployeeRepository())


# =============================================================================
# Lower authority cannot edit a higher target through the BFF
# =============================================================================


class TestLowerAuthorityIsRefused:
    @pytest.mark.parametrize("field", list(F8_EDITS))
    def test_each_f8_field_is_protected(self, field):
        actor = make_employee("Clerk", BFF)
        target = make_employee("Admin", "*")
        before = snapshot(target)
        assert_refused(bff_put(actor, target, F8_EDITS[field]))
        assert snapshot(target) == before

    def test_full_access_target(self):
        actor = make_employee("Clerk", BFF, "hr.employee.view")
        target = make_employee("Admin", "*")
        assert_refused(bff_put(actor, target, {"first_name": "B", "surname": "C", "phone": "0770000000"}))
        assert Employees.objects.get(pk=target.pk).first_name == "Admin"

    def test_superuser_linked_target(self):
        actor = make_employee("Clerk", "bff.x")
        target = make_employee("Root", superuser=True)
        assert_refused(bff_put(actor, target, {"surname": "Pwned"}))
        assert Employees.objects.get(pk=target.pk).surname == "Person"

    def test_higher_target_holding_one_unheld_permission(self):
        actor = make_employee("Clerk", BFF, "hr.employee.view")
        target = make_employee("Peerplus", BFF, "hr.employee.view", "hr.role.manage")
        assert_refused(bff_put(actor, target, {"phone": "0770000000"}))

    def test_deactivated_higher_target_stays_protected(self):
        actor = make_employee("Clerk", BFF)
        target = make_employee("Admin", "*")
        lifecycle().deactivate(target.pk)
        assert_refused(bff_put(actor, target, {"first_name": "Changed"}))

    def test_staff_flag_adds_no_authority(self):
        actor = make_employee("Staff", BFF, staff=True)
        target = make_employee("Admin", "*")
        assert_refused(bff_put(actor, target, {"first_name": "Changed"}))


# =============================================================================
# Covered targets stay editable
# =============================================================================


class TestCoveredTargetsAreEditable:
    def test_equal_authority(self):
        actor = make_employee("Peera", BFF, "hr.employee.view")
        target = make_employee("Peerb", BFF, "hr.employee.view")
        response = bff_put(actor, target, {"first_name": "Edited", "phone": "0770000001"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert snapshot(target)["first_name"] == "Edited"
        assert snapshot(target)["phone"] == "0770000001"

    def test_higher_authority_on_lower(self):
        actor = make_employee("Manager", "bff.*", "hr.employee.*")
        target = make_employee("Clerk", BFF)
        response = bff_put(actor, target, {"surname": "Edited"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert snapshot(target)["surname"] == "Edited"

    def test_self(self):
        actor = make_employee("Self", BFF)
        response = bff_put(actor, actor, {"first_name": "Myself"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert snapshot(actor)["first_name"] == "Myself"

    def test_full_access_actor(self):
        actor = make_employee("Admina", "*")
        target = make_employee("Adminb", "*")
        assert bff_put(actor, target, {"first_name": "Edited"}).status_code == status.HTTP_200_OK

    def test_superuser(self):
        actor = make_employee("Root", superuser=True)
        target = make_employee("Rootb", superuser=True)
        response = bff_put(actor, target, {"first_name": "Edited"})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert snapshot(target)["first_name"] == "Edited"

    def test_partial_update_changes_only_what_is_sent(self):
        actor = make_employee("Manager", "bff.*", "hr.employee.*")
        target = make_employee("Clerk", BFF)
        before = snapshot(target)
        assert bff_put(actor, target, {"surname": "Only"}).status_code == status.HTTP_200_OK
        after = snapshot(target)
        assert after["surname"] == "Only"
        assert {k: v for k, v in after.items() if k != "surname"} == {
            k: v for k, v in before.items() if k != "surname"
        }


# =============================================================================
# The BFF and the HR API answer alike
# =============================================================================


class TestParityWithTheHrApi:
    @pytest.mark.parametrize(
        "actor_permissions, target_permissions, expected",
        [
            ([BFF, "hr.employee.view"], ["*"], status.HTTP_403_FORBIDDEN),
            (["bff.*", "hr.employee.*"], [BFF, "hr.employee.view"], status.HTTP_200_OK),
            ([BFF, "hr.employee.view"], [BFF, "hr.employee.view"], status.HTTP_200_OK),
        ],
        ids=["lower-on-higher", "higher-on-lower", "equal"],
    )
    @pytest.mark.parametrize("field", list(F8_EDITS))
    def test_same_actor_same_target_same_answer(
        self, field, actor_permissions, target_permissions, expected
    ):
        actor = make_employee("Actor", *actor_permissions)
        target = make_employee("Target", *target_permissions)
        hr = hr_patch(actor, target, F8_EDITS[field])
        bff = bff_put(actor, target, F8_EDITS[field])
        assert hr.status_code == bff.status_code == expected
        if expected == status.HTTP_403_FORBIDDEN:
            assert hr.data["code"] == bff.data["code"] == EXCEEDS


# =============================================================================
# A refused request changes nothing
# =============================================================================


class TestMixedRequestsAreAtomic:
    def test_refused_hr_field_with_authorized_payroll_writes_neither(self):
        actor = make_employee(
            "Payclerk", BFF, "payroll.profile.manage", "payroll.profile.view",
            "payroll.bank.manage", "payroll.bank.view",
        )
        target = make_employee("Admin", "*")
        PayrollProfile.objects.create(employee=target, usd_salary=Decimal("1000.00"))
        EmployeeBankAccount.objects.create(
            employee=target, bank_name="Bank", account_number="ACC-1", is_primary=True
        )
        before = snapshot(target)
        response = bff_put(
            actor, target,
            {"first_name": "Hijacked", "usd_salary": "9999.00", "bank_account": "ACC-2"},
        )
        assert_refused(response)
        assert snapshot(target) == before
        assert PayrollProfile.objects.get(employee=target).usd_salary == Decimal("1000.00")
        assert EmployeeBankAccount.objects.get(employee=target).account_number == "ACC-1"

    def test_refused_hr_field_with_email_writes_neither(self):
        actor = make_employee("Clerk", BFF)
        target = make_employee("Admin", "*")
        before = snapshot(target)
        assert_refused(bff_put(actor, target, {"phone": "0770000000", "email": "x94@zchpc.test"}))
        assert snapshot(target) == before

    def test_invalid_hr_value_is_a_400_and_writes_nothing(self):
        actor = make_employee("Payclerk", "bff.*", "hr.employee.*", "payroll.profile.manage")
        target = make_employee("Clerk", BFF)
        PayrollProfile.objects.create(employee=target, usd_salary=Decimal("1000.00"))
        before = snapshot(target)
        response = bff_put(actor, target, {"first_name": "Valid", "phone": "12", "usd_salary": "5.00"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert snapshot(target) == before
        assert PayrollProfile.objects.get(employee=target).usd_salary == Decimal("1000.00")


# =============================================================================
# Boundaries of this slice
# =============================================================================


class TestSliceBoundaries:
    def test_email_is_judged_by_the_same_rule_since_f9(self):
        """
        F8 left email unclassified; AUD-02 F9 made it an ordinary field, and
        the BFF - writing it through EmployeeService - judges it the same way
        (test_employee_email_authority).
        """
        actor = make_employee("Clerk", BFF)
        target = make_employee("Admin", "*")
        before = snapshot(target)
        assert_refused(bff_put(actor, target, {"email": f"moved{next(_numbers)}@zchpc.test"}))
        assert snapshot(target) == before

    def test_archived_target_keeps_its_existing_answers(self):
        target = make_employee("Archived", "*")
        lifecycle().archive(target.pk)
        plain = make_employee("Clerk", BFF)
        historian = make_employee("Historian", BFF, "hr.employee.view_archived")
        assert bff_put(plain, target, {"first_name": "X"}).status_code == status.HTTP_404_NOT_FOUND
        response = bff_put(historian, target, {"first_name": "X"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "EMPLOYEE_ARCHIVED"

    def test_orchestrator_enforces_it_without_http(self):
        target = make_employee("Admin", "*")
        actor = PayrollActor(
            employee_id=None,
            permissions=PermissionSet.from_list([BFF]),
            is_superuser=False,
            is_authenticated=True,
        )
        with pytest.raises(AuthorizationError) as raised:
            EmployeeOrchestrator.update_full_profile(target.uuid, {"first_name": "X"}, actor)
        assert raised.value.code == EXCEEDS
        assert snapshot(target)["first_name"] == "Admin"
