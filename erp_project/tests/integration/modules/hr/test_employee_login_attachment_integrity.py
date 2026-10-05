"""
AUD-02 F9 (slice 1): which login a new employee record is attached to.

Creating an employee whose email matches an existing login attaches the new
record to that login (F7), and the creator must have authority over it. The
rule that picks the login must be the same wherever it is applied - the
authorization in EmployeeService and the link made by the post_save signal -
and must match identities the way identity does, case-insensitively:

- a login whose email differs only by letter case is the same identity, so
  attaching to it is judged by F7 like any other (F9-1);
- a login that already belongs to another employee is not attachable: the
  email is taken (DUPLICATE_EMAIL), nothing is created (F9-2);
- an employee email already held by another employee is DUPLICATE_EMAIL on
  create and on update, also when two requests race for it (F9-8).

Every HTTP request carries a real JWT, so RBACMiddleware is on the path.
"""

import threading
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import (
    CreateEmployeeCommand,
    EmployeeService,
    UpdateEmployeeCommand,
)
from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.exceptions import ValidationError

User = get_user_model()

PASSWORD = "AttachPass12345!"
EMPLOYEES_URL = "/api/v2/hr/employees/"
LOGIN_URL = "/api/v2/auth/token/"
CREATOR = ("hr.employee.view", "hr.employee.create")
EXCEEDS = "EMPLOYEE_TARGET_EXCEEDS_ACTOR_AUTHORITY"

# EmployeeId accepts only EMP + digits.
_numbers = count(93501)

# Fixed by the next commit ("harden employee login attachment").
F9_FIX = pytest.mark.xfail(strict=True, reason="AUD-02 F9 slice 1: not yet fixed")


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
        user=user, first_name=label, surname="Person", email=email, role=role,
        employee_id=f"EMP{next(_numbers)}",
    )


def mixed_case_email(label):
    """A login email whose local part keeps capitals (as createsuperuser stores it)."""
    return f"{label}.Case{next(_numbers)}@zchpc.test"


def client_for(user):
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def create(actor, email, **extra):
    return client_for(actor.user).post(
        EMPLOYEES_URL, {"first_name": "New", "surname": "Hire", "email": email, **extra}, format="json"
    )


def logins_for(email):
    return User.objects.filter(email__iexact=email).count()


def employee_service():
    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


def diverge(employee):
    """Move the employee's email away from their login's, leaving the login attached."""
    employee_service().update_employee(
        UpdateEmployeeCommand(employee_id=employee.pk, email=f"moved{next(_numbers)}@zchpc.test"),
        actor_permissions=PermissionSet.full_access(),
    )


# =============================================================================
# F9-1: logins are matched case-insensitively, and F7 judges the match
# =============================================================================


@pytest.mark.django_db
class TestMixedCaseLogins:
    @F9_FIX
    def test_a_mixed_case_privileged_login_is_protected_by_f7(self):
        root_email = mixed_case_email("Root")
        root = User.objects.create_superuser(email=root_email, password=PASSWORD)
        actor = make_employee("Creator", *CREATOR)
        employees_before = Employees.objects.count()

        response = create(actor, root_email.lower())

        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert response.data["code"] == EXCEEDS
        assert Employees.objects.count() == employees_before
        assert logins_for(root_email) == 1
        assert User.objects.get(pk=root.pk).email == root_email

    @F9_FIX
    def test_the_privileged_login_can_still_sign_in(self):
        root_email = mixed_case_email("Root")
        User.objects.create_superuser(email=root_email, password=PASSWORD)
        create(make_employee("Creator", *CREATOR), root_email.lower())

        response = APIClient(raise_request_exception=False).post(
            LOGIN_URL, {"email": root_email, "password": PASSWORD}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, getattr(response, "data", None)

    @F9_FIX
    def test_a_mixed_case_login_the_actor_covers_is_attached_not_duplicated(self):
        bare_email = mixed_case_email("Bare")
        bare = User.objects.create_user(email=bare_email, password=PASSWORD)

        response = create(make_employee("Creator", *CREATOR), bare_email.lower())

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Employees.objects.get(pk=response.data["id"]).user_id == bare.pk
        assert logins_for(bare_email) == 1

    def test_same_case_privileged_login_keeps_its_f7_refusal(self):
        root = User.objects.create_superuser(email=f"root{next(_numbers)}@zchpc.test", password=PASSWORD)
        response = create(make_employee("Creator", *CREATOR), root.email)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == EXCEEDS
        assert not Employees.objects.filter(user_id=root.pk).exists()

    @F9_FIX
    def test_logins_differing_only_by_case_are_never_attached(self):
        """Pre-existing ambiguity: refuse rather than pick one."""
        email = mixed_case_email("Twin")
        User.objects.create_user(email=email, password=PASSWORD)
        User.objects.create_user(email=email.lower(), password=PASSWORD)
        employees_before = Employees.objects.count()

        response = create(make_employee("Boss", "*"), email.lower())

        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert Employees.objects.count() == employees_before
        assert logins_for(email) == 2


# =============================================================================
# F9-2: a login that already belongs to an employee is not attachable
# =============================================================================


@pytest.mark.django_db(transaction=True)
class TestAlreadyAttachedLogin:
    @F9_FIX
    @pytest.mark.parametrize("case", ["same", "upper"], ids=["same-case", "different-case"])
    def test_its_email_is_taken(self, case):
        holder = make_employee("Holder", "hr.employee.view")
        login_email = holder.user.email
        diverge(holder)
        employees_before = Employees.objects.count()

        requested = login_email if case == "same" else login_email.upper()
        response = create(make_employee("Boss", "*"), requested)

        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert response.data["code"] == "DUPLICATE_EMAIL"
        assert Employees.objects.count() == employees_before + 1  # only Boss
        assert Employees.objects.get(pk=holder.pk).user_id == holder.user_id
        assert logins_for(login_email) == 1

    @F9_FIX
    def test_the_signal_does_not_attach_it_either(self):
        """Records created outside EmployeeService follow the same rule."""
        holder = make_employee("Holder", "hr.employee.view")
        login_email = holder.user.email
        diverge(holder)
        with pytest.raises(ValidationError):
            Employees.objects.create(
                first_name="Direct", surname="Orm", email=login_email,
                employee_id=f"EMP{next(_numbers)}",
            )
        assert not Employees.objects.filter(email=login_email).exists()
        assert Employees.objects.get(pk=holder.pk).user_id == holder.user_id


# =============================================================================
# F9-8: an employee email held by another employee is DUPLICATE_EMAIL
# =============================================================================


@pytest.mark.django_db(transaction=True)
class TestDuplicateEmployeeEmail:
    def test_on_create(self):
        existing = make_employee("Existing", "hr.employee.view")
        response = create(make_employee("Boss", "*"), existing.email.upper())
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "DUPLICATE_EMAIL"

    @F9_FIX
    @pytest.mark.parametrize("case", ["same", "upper"], ids=["same-case", "different-case"])
    def test_on_update(self, case):
        boss = make_employee("Boss", "*")
        target, other = make_employee("Target", "hr.employee.view"), make_employee("Other", "hr.employee.view")
        before = Employees.objects.get(pk=target.pk).email
        email = other.email if case == "same" else other.email.upper()
        response = client_for(boss.user).patch(f"{EMPLOYEES_URL}{target.pk}/", {"email": email}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, getattr(response, "data", None)
        assert response.data["code"] == "DUPLICATE_EMAIL"
        assert Employees.objects.get(pk=target.pk).email == before

    def test_keeping_your_own_email_is_not_a_conflict(self):
        boss = make_employee("Boss", "*")
        target = make_employee("Target", "hr.employee.view")
        response = client_for(boss.user).patch(
            f"{EMPLOYEES_URL}{target.pk}/", {"email": target.email.upper(), "phone": "0771234567"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data

    @F9_FIX
    def test_a_lost_race_on_create_is_duplicate_email_not_a_database_error(self, monkeypatch):
        """Both requests pass the duplicate check; the unique index decides."""
        email = f"race{next(_numbers)}@zchpc.test"
        barrier = threading.Barrier(2, timeout=15)
        original = DjangoEmployeeRepository.exists_by_email
        gated = {"calls": 0}
        lock = threading.Lock()

        def exists_by_email(self, value, *args, **kwargs):
            result = original(self, value, *args, **kwargs)
            with lock:
                gated["calls"] += 1
                first_two = gated["calls"] <= 2
            if first_two:
                barrier.wait()
            return result

        monkeypatch.setattr(DjangoEmployeeRepository, "exists_by_email", exists_by_email)
        outcomes = []

        def run(i):
            try:
                employee_service().create_employee(
                    CreateEmployeeCommand(first_name=f"Racer{i}", surname="R", email=email),
                    actor_permissions=PermissionSet.full_access(),
                )
                outcomes.append("created")
            except ValidationError as exc:
                outcomes.append(exc.code)
            except Exception as exc:  # noqa: BLE001 - the defect being characterized
                outcomes.append(type(exc).__name__)
            finally:
                connection.close()

        threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sorted(outcomes) == ["DUPLICATE_EMAIL", "created"], outcomes
        assert Employees.objects.filter(email=email).count() == 1
        assert logins_for(email) == 1
