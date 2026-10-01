"""
AUD-02 Slice 5: historical integrity of the employee EC number.

Invariant: an EC number (Employees.employee_id) belongs to at most one
employee identity for all time.

It rests on three things, each enforced here:

1. The holder's row is permanent. Slice 4 removed every application path
   that deletes an employee, and deactivation (or, later, archival) keeps
   the row - so a consumed number stays recorded against its holder.
2. The number on a row never changes. No API accepts it on update, the
   repository's update does not write it, and a database trigger refuses
   any UPDATE that changes a non-blank number.
3. No two rows hold the same number. The database UNIQUE constraint, with
   allocation serialized (PostgreSQL advisory lock) so two concurrent
   creations cannot both pick the same number, and an explicit request
   compared in its normalized form.

Together these mean a number, once consumed, can never be held by anyone
else - without a separate historical-identifier table.
"""

import threading
import time
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.application.services import CreateEmployeeCommand, EmployeeLifecycleService
from modules.hr.domain.services import SequentialEmployeeIdGenerator
from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
from modules.hr.infrastructure.persistence.models import Employees
from modules.identity.domain.value_objects import PermissionSet
from shared.domain.value_objects import EmployeeId

User = get_user_model()

PASSWORD = "EmployeePass123!"
EMPLOYEES_URL = "/api/v2/hr/employees/"

_numbers = count(1)


# =============================================================================
# Helpers
# =============================================================================


def unique_email(label="hire"):
    return f"{label.lower()}{next(_numbers)}@zchpc.test"


def root_client():
    """A bare superuser (no employee record of its own)."""
    root = User.objects.create_superuser(email=unique_email("root"), password=PASSWORD)
    client = APIClient(raise_request_exception=False)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(root)}")
    return client


def hire(client, label="Hire", **extra):
    return client.post(
        EMPLOYEES_URL,
        {"first_name": label, "surname": "Person", "email": unique_email(label), **extra},
        format="json",
    )


def hired_number(client, label="Hire", **extra):
    response = hire(client, label, **extra)
    assert response.status_code == 201, response.data
    return response.data["employee_id"]


def existing(number, **extra):
    """An employee row holding ``number``, created directly."""
    return Employees.objects.create(
        employee_id=number,
        first_name="Existing",
        surname=number,
        email=unique_email("existing"),
        **extra,
    )


def store_state(employee, status):
    Employees.objects.filter(pk=employee.pk).update(
        lifecycle_status=status, is_active=status == "ACTIVE"
    )


def employee_service():
    from modules.hr.application.services import EmployeeService
    from modules.hr.infrastructure.persistence.department_repository import (
        DjangoDepartmentRepository,
    )
    from modules.hr.infrastructure.persistence.position_repository import (
        DjangoPositionRepository,
    )

    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


# =============================================================================
# Generation
# =============================================================================


@pytest.mark.django_db
class TestGeneration:
    @pytest.fixture(autouse=True)
    def empty_table(self):
        Employees.objects.all().delete()

    def test_first_number(self):
        assert hired_number(root_client()) == "EMP0001"

    def test_numbers_increase(self):
        client = root_client()
        assert [hired_number(client) for _ in range(3)] == ["EMP0001", "EMP0002", "EMP0003"]

    def test_a_gap_left_by_an_explicit_number_is_jumped_not_filled(self):
        client = root_client()
        hired_number(client)  # EMP0001
        hired_number(client, employee_id="EMP0010")
        assert hired_number(client) == "EMP0011"

    def test_highest_is_found_numerically_not_alphabetically(self):
        """'EMP9999' sorts after 'EMP10000' as text; the next number is EMP10001."""
        existing("EMP9999")
        existing("EMP10000")
        assert hired_number(root_client()) == "EMP10001"

    @pytest.mark.parametrize("status", ["DEACTIVATED", "ARCHIVED"])
    def test_a_non_active_holder_still_consumes_their_number(self, status):
        """
        ARCHIVED is written straight to the row (the Slice 2 model state); no
        archive transition exists yet. Allocation never looks at the state.
        """
        client = root_client()
        first = hired_number(client)
        store_state(Employees.objects.get(employee_id=first), status)
        assert hired_number(client) == "EMP0002"

    def test_a_fresh_repository_sees_every_consumed_number(self):
        client = root_client()
        hired_number(client)
        hired_number(client)
        generator = SequentialEmployeeIdGenerator(DjangoEmployeeRepository().get_max_employee_id)
        assert str(generator.next_id()) == "EMP0003"


# =============================================================================
# Explicit assignment
# =============================================================================


@pytest.mark.django_db
class TestExplicitAssignment:
    @pytest.mark.parametrize("requested", ["EMP0700", "emp0700", " EMP0700 ", "Emp0700"])
    def test_a_held_number_is_refused_in_any_spelling(self, requested):
        holder = existing("EMP0700")
        employees_before, logins_before = Employees.objects.count(), User.objects.count()
        response = hire(root_client(), "Claimant", employee_id=requested)
        assert response.status_code == 400, response.data
        assert response.data["code"] == "DUPLICATE_EMPLOYEE_ID"
        assert Employees.objects.count() == employees_before
        assert User.objects.count() == logins_before + 1  # only the actor's own login
        assert Employees.objects.get(pk=holder.pk).employee_id == "EMP0700"

    @pytest.mark.parametrize("status", ["DEACTIVATED", "ARCHIVED"])
    def test_a_non_active_holders_number_is_refused(self, status):
        holder = existing("EMP0701")
        store_state(holder, status)
        response = hire(root_client(), "Claimant", employee_id="EMP0701")
        assert response.status_code == 400
        assert response.data["code"] == "DUPLICATE_EMPLOYEE_ID"
        assert Employees.objects.filter(employee_id="EMP0701").count() == 1

    def test_a_deactivated_holder_through_the_lifecycle(self):
        client = root_client()
        number = hired_number(client, "Holder")
        holder = Employees.objects.get(employee_id=number)
        EmployeeLifecycleService(DjangoEmployeeRepository()).deactivate(holder.pk)
        response = hire(client, "Claimant", employee_id=number)
        assert response.status_code == 400
        assert Employees.objects.get(pk=holder.pk).lifecycle_status == "DEACTIVATED"

    def test_a_never_issued_number_can_be_assigned(self):
        """Only consumed numbers are protected; an unused one may be chosen."""
        assert hired_number(root_client(), "Chosen", employee_id="emp0800") == "EMP0800"

    def test_a_malformed_number_is_refused(self):
        response = hire(root_client(), "Odd", employee_id="X-1")
        assert response.status_code == 400


# =============================================================================
# The number on a row never changes
# =============================================================================


@pytest.mark.django_db
class TestNumberNeverChanges:
    def test_employee_update_ignores_it(self):
        holder = existing("EMP0900")
        response = root_client().patch(
            f"{EMPLOYEES_URL}{holder.pk}/", {"employee_id": "EMP0901"}, format="json"
        )
        assert response.status_code == 200
        assert Employees.objects.get(pk=holder.pk).employee_id == "EMP0900"

    def test_bff_profile_update_ignores_it(self):
        holder = existing("EMP0902")
        response = root_client().put(
            f"/api/v2/bff/employees/{holder.uuid}/", {"employee_id": "EMP0903"}, format="json"
        )
        assert response.status_code == 200
        assert Employees.objects.get(pk=holder.pk).employee_id == "EMP0902"

    def test_repository_update_does_not_write_it(self):
        holder = existing("EMP0904")
        repository = DjangoEmployeeRepository()
        entity = repository.get_by_id(holder.pk)
        entity.employee_id = EmployeeId("EMP0905")
        entity.first_name = "Renamed"
        repository.update(entity)
        row = Employees.objects.get(pk=holder.pk)
        assert (row.employee_id, row.first_name) == ("EMP0904", "Renamed")

    def test_database_refuses_a_change(self):
        holder = existing("EMP0906")
        with pytest.raises(IntegrityError), transaction.atomic():
            Employees.objects.filter(pk=holder.pk).update(employee_id="EMP0907")
        assert Employees.objects.get(pk=holder.pk).employee_id == "EMP0906"

    def test_database_refuses_a_change_through_save(self):
        holder = existing("EMP0908")
        holder.employee_id = "EMP0909"
        with pytest.raises(IntegrityError), transaction.atomic():
            holder.save()
        assert Employees.objects.get(pk=holder.pk).employee_id == "EMP0908"

    def test_database_allows_rewriting_the_same_number(self):
        """Ordinary saves write every column; an unchanged number passes."""
        holder = existing("EMP0910")
        holder.first_name = "Changed"
        holder.save()
        Employees.objects.filter(pk=holder.pk).update(employee_id="EMP0910")
        assert Employees.objects.get(pk=holder.pk).first_name == "Changed"

    def test_database_allows_numbering_a_row_that_has_none(self):
        """A blank number was never consumed; giving it one is allowed."""
        Employees.objects.bulk_create(
            [Employees(employee_id="", first_name="Blank", surname="Row", email=unique_email())]
        )
        row = Employees.objects.get(employee_id="")
        Employees.objects.filter(pk=row.pk).update(employee_id="EMP0911")
        assert Employees.objects.get(pk=row.pk).employee_id == "EMP0911"

    def test_lifecycle_transitions_keep_it(self):
        client = root_client()
        number = hired_number(client)
        holder = Employees.objects.get(employee_id=number)
        lifecycle = EmployeeLifecycleService(DjangoEmployeeRepository())
        lifecycle.deactivate(holder.pk)
        lifecycle.reactivate(holder.pk)
        assert Employees.objects.get(pk=holder.pk).employee_id == number


# =============================================================================
# Concurrent allocation (PostgreSQL: the production database)
# =============================================================================


def _run_concurrently(*calls):
    """Run each call in its own thread and database connection; collect outcomes."""
    outcomes = [None] * len(calls)

    def worker(index, call):
        try:
            outcomes[index] = ("ok", call())
        except Exception as exc:  # noqa: BLE001 - the outcome is what is asserted
            outcomes[index] = ("error", exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i, c)) for i, c in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return outcomes


@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="concurrency is a PostgreSQL property"
)
@pytest.mark.django_db(transaction=True)
class TestConcurrentAllocation:
    @pytest.fixture(autouse=True)
    def slow_generation(self, monkeypatch):
        """Widen the window between reading the highest number and inserting."""
        original = SequentialEmployeeIdGenerator.next_id

        def slow_next_id(self):
            number = original(self)
            time.sleep(0.5)
            return number

        monkeypatch.setattr(SequentialEmployeeIdGenerator, "next_id", slow_next_id)

    @staticmethod
    def _create(label, employee_id=None):
        def call():
            return str(
                employee_service()
                .create_employee(
                    CreateEmployeeCommand(
                        first_name=label,
                        surname="Concurrent",
                        email=unique_email(label),
                        employee_id=employee_id,
                    ),
                    actor_permissions=PermissionSet.full_access(),
                )
                .employee_id
            )

        return call

    def test_two_generated_numbers_never_collide(self):
        existing("EMP0100")
        outcomes = _run_concurrently(self._create("Alpha"), self._create("Bravo"))
        assert [kind for kind, _ in outcomes] == ["ok", "ok"], outcomes
        assert sorted(number for _, number in outcomes) == ["EMP0101", "EMP0102"]

    def test_two_explicit_requests_for_one_number_give_one_holder(self):
        from shared.domain.exceptions import ValidationError

        outcomes = _run_concurrently(
            self._create("Alpha", "EMP0200"), self._create("Bravo", "EMP0200")
        )
        kinds = sorted(kind for kind, _ in outcomes)
        assert kinds == ["error", "ok"], outcomes
        error = next(value for kind, value in outcomes if kind == "error")
        assert isinstance(error, ValidationError)
        assert error.code == "DUPLICATE_EMPLOYEE_ID"
        assert Employees.objects.filter(employee_id="EMP0200").count() == 1
