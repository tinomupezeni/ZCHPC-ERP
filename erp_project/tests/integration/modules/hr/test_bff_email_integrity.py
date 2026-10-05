"""
AUD-02 F9 (slice 4): the BFF cannot store an invalid or taken employee email.

PUT /api/v2/bff/employees/<uuid>/ wrote the employee email straight to the
database. An invalid address was committed and the request then failed in
the response serializer (500); an address held by another employee failed
on the unique index (500). The email now goes through EmployeeService like
the BFF's other HR fields (F8), so it is validated before anything is
written: an invalid address or one another employee holds is a 400, and
nothing in the request - payroll sections included - is saved.

Who may change another employee's email is not decided here: email is not
one of F1's ordinary fields, so it carries no target-authority check on
either path, as before.
"""

from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.payroll.infrastructure.persistence.models import PayrollProfile

User = get_user_model()

PASSWORD = "BffEmailPass123!"
BFF = "bff.employee.view"

# EmployeeId accepts only EMP + digits.
_numbers = count(91501)

# Fixed by the next commit ("validate bff employee email updates").
F9_FIX = pytest.mark.xfail(strict=True, reason="AUD-02 F9 slice 4: not yet fixed")


def make_employee(label, *permissions):
    email = f"{label.lower()}{next(_numbers)}@zchpc.test"
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


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def bff_put(actor, target, body):
    return client_for(actor.user).put(f"/api/v2/bff/employees/{target.uuid}/", body, format="json")


def stored(employee):
    return Employees.objects.filter(pk=employee.pk).values("first_name", "email").get()


@pytest.mark.django_db(transaction=True)
class TestInvalidAndTakenEmails:
    @F9_FIX
    @pytest.mark.parametrize("email", ["not-an-email", ""], ids=["malformed", "blank"])
    def test_an_invalid_email_is_a_400_and_not_stored(self, email):
        actor, target = make_employee("Boss", "bff.*", "*"), make_employee("Target", BFF)
        before = stored(target)
        response = bff_put(actor, target, {"email": email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert stored(target) == before

    @F9_FIX
    @pytest.mark.parametrize("case", ["same", "upper"], ids=["same-case", "different-case"])
    def test_another_employees_email_is_duplicate_email(self, case):
        actor = make_employee("Boss", "bff.*", "*")
        target, other = make_employee("Target", BFF), make_employee("Other", BFF)
        before = stored(target)
        email = other.email if case == "same" else other.email.upper()
        response = bff_put(actor, target, {"email": email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert response.data["code"] == "DUPLICATE_EMAIL"
        assert stored(target) == before

    @F9_FIX
    def test_a_refused_email_writes_nothing_else_in_the_request(self):
        actor = make_employee("Boss", "bff.*", "*")
        target, other = make_employee("Target", BFF), make_employee("Other", BFF)
        PayrollProfile.objects.create(employee=target, usd_salary=Decimal("1000.00"))
        before = stored(target)
        response = bff_put(
            actor, target, {"first_name": "Changed", "email": other.email, "usd_salary": "5.00"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert stored(target) == before
        assert PayrollProfile.objects.get(employee=target).usd_salary == Decimal("1000.00")


@pytest.mark.django_db
class TestValidEmailsAndExistingRules:
    def test_a_valid_email_is_stored(self):
        actor, target = make_employee("Boss", "bff.*", "*"), make_employee("Target", BFF)
        email = f"fresh{next(_numbers)}@zchpc.test"
        response = bff_put(actor, target, {"email": email})
        assert response.status_code == status.HTTP_200_OK, response.data
        assert stored(target)["email"] == email

    def test_resending_your_own_email_is_not_a_conflict(self):
        actor, target = make_employee("Boss", "bff.*", "*"), make_employee("Target", BFF)
        response = bff_put(actor, target, {"email": target.email})
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_f8_target_authority_still_judges_the_hr_fields_sent_with_it(self):
        actor, admin = make_employee("Clerk", BFF), make_employee("Admin", "*")
        before = stored(admin)
        response = bff_put(actor, admin, {"first_name": "X", "email": f"x{next(_numbers)}@zchpc.test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"
        assert stored(admin) == before
