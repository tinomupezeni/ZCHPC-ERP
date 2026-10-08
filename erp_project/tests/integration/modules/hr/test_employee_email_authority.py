"""
AUD-02 F9: who may change another employee's email.

Employee.email is the HR contact address; the login's own email is separate
and cannot be changed after creation, so changing Employee.email moves no
sign-in, recovery or authority. It was left unclassified by F1 and was
editable on anyone by any actor past the hr (or bff) gate.

Approved policy: Employee.email is an ordinary employee attribute. Changing
another employee's needs authority over them (covers on their effective
permissions) - no capability, manage_assignments neither needed nor enough -
on PATCH /hr/employees/<id>/ and PUT /bff/employees/<uuid>/ alike (the BFF
writes it through EmployeeService). Refusal is 403
EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY, judged before the email's own
validation and uniqueness, which are unchanged (test_bff_email_integrity,
test_employee_login_attachment_integrity).

Every HTTP request carries a real JWT, so RBACMiddleware is on the path.
"""

from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import EmployeeService, UpdateEmployeeCommand
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import AuthorizationError

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "EmailAuthPass123!"
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

VIEWER = ("hr.employee.view", "bff.employee.view")
PEER = ("hr.employee.view", "bff.employee.view", "hr.employee.create")
# Covers VIEWER and PEER targets without holding manage_assignments.
SENIOR = ("hr.employee.view", "bff.employee.view", "hr.employee.create", "hr.role.manage")

# EmployeeId accepts only EMP + digits.
_numbers = count(88501)


def make_employee(label, *permissions, superuser=False):
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
        user=user, first_name=label, surname="Person", email=email, phone="0771234567",
        role=role, employee_id=f"EMP{next(_numbers)}",
    )


def new_email():
    return f"changed{next(_numbers)}@zchpc.test"


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def hr_patch(actor, target, body):
    return client_for(actor.user).patch(f"/api/v2/hr/employees/{target.pk}/", body, format="json")


def bff_put(actor, target, body):
    return client_for(actor.user).put(f"/api/v2/bff/employees/{target.uuid}/", body, format="json")


PATHS = {"hr": hr_patch, "bff": bff_put}


def stored_email(employee):
    return Employees.objects.get(pk=employee.pk).email


def login_email(employee):
    return User.objects.get(pk=employee.user_id).email


def assert_refused(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, getattr(response, "data", None)
    assert response.data["code"] == EXCEEDS


def assert_changed(response, target, email):
    assert response.status_code == status.HTTP_200_OK, getattr(response, "data", None)
    assert stored_email(target) == email


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


# =============================================================================
# Lower authority cannot change a higher target's email
# =============================================================================


class TestLowerAuthorityIsRefused:
    @pytest.mark.parametrize("path", PATHS)
    def test_lower_authority_cannot_change_a_higher_employees_email(self, path):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        before = stored_email(target)
        assert_refused(PATHS[path](actor, target, {"email": new_email()}))
        assert stored_email(target) == before

    @pytest.mark.parametrize("path", PATHS)
    def test_a_superuser_linked_employee_is_protected(self, path):
        actor, target = make_employee("Clerk", *SENIOR), make_employee("Root", superuser=True)
        before = stored_email(target)
        assert_refused(PATHS[path](actor, target, {"email": new_email()}))
        assert stored_email(target) == before

    def test_manage_assignments_does_not_replace_target_authority(self):
        actor = make_employee("Assigner", *VIEWER, "hr.employee.manage_assignments")
        target = make_employee("Admin", "*")
        before = stored_email(target)
        assert_refused(hr_patch(actor, target, {"email": new_email()}))
        assert stored_email(target) == before

    def test_authority_is_judged_before_the_emails_own_checks(self):
        """A refused actor learns nothing about which addresses are taken."""
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        taken = make_employee("Other", *VIEWER)
        assert_refused(hr_patch(actor, target, {"email": taken.email}))

    def test_the_service_refuses_without_http(self):
        target = make_employee("Admin", "*")
        before = stored_email(target)
        with pytest.raises(AuthorizationError) as raised:
            employee_service().update_employee(
                UpdateEmployeeCommand(employee_id=target.pk, email=new_email()),
                actor_permissions=PermissionSet.from_list(list(VIEWER)),
            )
        assert raised.value.code == EXCEEDS
        assert stored_email(target) == before


# =============================================================================
# Covered targets stay editable - with no capability
# =============================================================================


class TestCoveredTargetsAreEditable:
    @pytest.mark.parametrize("path", PATHS)
    def test_self(self, path):
        actor = make_employee("Self", *VIEWER)
        email = new_email()
        assert_changed(PATHS[path](actor, actor, {"email": email}), actor, email)

    @pytest.mark.parametrize("path", PATHS)
    def test_peer(self, path):
        actor, target = make_employee("Peera", *PEER), make_employee("Peerb", *PEER)
        email = new_email()
        assert_changed(PATHS[path](actor, target, {"email": email}), target, email)

    @pytest.mark.parametrize("path", PATHS)
    def test_higher_authority_without_manage_assignments(self, path):
        actor, target = make_employee("Senior", *SENIOR), make_employee("Clerk", *VIEWER)
        email = new_email()
        assert_changed(PATHS[path](actor, target, {"email": email}), target, email)

    @pytest.mark.parametrize("path", PATHS)
    def test_superuser(self, path):
        actor, target = make_employee("Root", superuser=True), make_employee("Admin", "*")
        email = new_email()
        assert_changed(PATHS[path](actor, target, {"email": email}), target, email)

    def test_the_login_email_is_untouched(self):
        actor, target = make_employee("Senior", *SENIOR), make_employee("Clerk", *VIEWER)
        before = login_email(target)
        email = new_email()
        assert_changed(hr_patch(actor, target, {"email": email}), target, email)
        assert login_email(target) == before


# =============================================================================
# Other ordinary fields keep their rule
# =============================================================================


class TestOtherFieldsUnchanged:
    def test_an_ordinary_field_is_still_refused_on_a_higher_target(self):
        actor, target = make_employee("Clerk", *VIEWER), make_employee("Admin", "*")
        assert_refused(hr_patch(actor, target, {"phone": "0770000000"}))
