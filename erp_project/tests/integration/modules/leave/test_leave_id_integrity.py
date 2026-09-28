"""
REM-06: leave primary keys are database-assigned.

The leave repositories used to mint IDs as max(id) + 1 in the service and
write with update_or_create(id=...). A row inserted by anyone else between
those two steps received that same ID, and the new record then *updated* it:
another employee's leave request or balance was silently replaced while the
caller was told it succeeded. Now new records carry id=None and are INSERTed
(shared.infrastructure.persistence.insert_or_update); an explicit id only
ever updates its own existing row.

Interleaving is made deterministic by wrapping the repository's save so the
victim row is written after the service has prepared its record but before
it persists it - exactly where max(id) + 1 used to be stale.
"""

import itertools
from datetime import date
from decimal import Decimal
from importlib import import_module

import pytest
from django.contrib.auth import get_user_model

from modules.hr.infrastructure.persistence.models import Employees
from modules.identity.domain.value_objects import PermissionSet
from modules.leave.api.views import get_leave_balance_service, get_leave_request_service
from modules.leave.application.authorization import LeaveActor, LeavePermissions as L
from modules.leave.application.interfaces import (
    ILeaveBalanceRepository,
    ILeaveRequestRepository,
    ILeaveTypeRepository,
)
from modules.leave.application.services.leave_balance_service import CreateLeaveBalanceCommand
from modules.leave.application.services.leave_request_service import SubmitLeaveRequestCommand
from modules.leave.domain.entities import (
    LeaveBalance as LeaveBalanceEntity,
    LeaveRequest as LeaveRequestEntity,
    LeaveType as LeaveTypeEntity,
)
from modules.leave.domain.value_objects import LeaveEntitlement, LeavePeriod
from modules.leave.infrastructure.persistence.django_leave_balance_repository import (
    DjangoLeaveBalanceRepository,
)
from modules.leave.infrastructure.persistence.django_leave_request_repository import (
    DjangoLeaveRequestRepository,
)
from modules.leave.infrastructure.persistence.django_leave_type_repository import (
    DjangoLeaveTypeRepository,
)
from modules.leave.infrastructure.persistence.models import LeaveBalance, LeaveRequest, LeaveType
from shared.domain.exceptions import NotFoundError

pytestmark = pytest.mark.django_db

User = get_user_model()
YEAR = 2030
_numbers = itertools.count(62001)


def make_employee(first):
    n = next(_numbers)
    user = User.objects.create_user(email=f"{first.lower()}{n}@zchpc.test", password="Pass12345!")
    return Employees.objects.create(
        user=user, first_name=first, surname="Tester", email=user.email, employee_id=f"EMP{n}",
    )


@pytest.fixture
def annual():
    return LeaveType.objects.create(name="Annual", default_days_allowed=20)


def write_victim_first(monkeypatch, repository_class, write_victim):
    """Make the repository write ``write_victim()`` just before its first save."""
    real_save = repository_class.save
    victims = []

    def save(self, entity):
        if not victims:
            victims.append(write_victim())
        return real_save(self, entity)

    monkeypatch.setattr(repository_class, "save", save)
    return victims


# ---------------------------------------------------------------- structural


class TestNoRepositoryMintsIds:
    def test_repositories_and_interfaces_expose_no_get_next_id(self):
        for cls in (ILeaveTypeRepository, ILeaveBalanceRepository, ILeaveRequestRepository,
                    DjangoLeaveTypeRepository, DjangoLeaveBalanceRepository,
                    DjangoLeaveRequestRepository):
            assert not hasattr(cls, "get_next_id"), cls

    def test_no_leave_source_computes_the_next_primary_key(self):
        import inspect

        from modules.leave.application.services import (
            leave_balance_service,
            leave_request_service,
            leave_type_service,
        )
        from modules.leave.infrastructure.persistence import (
            django_leave_balance_repository,
            django_leave_request_repository,
            django_leave_type_repository,
        )

        for module in (leave_balance_service, leave_request_service, leave_type_service,
                       django_leave_balance_repository, django_leave_request_repository,
                       django_leave_type_repository):
            source = inspect.getsource(module)
            assert "get_next_id" not in source, module
            assert 'order_by("-id")' not in source, module
            assert "update_or_create(" not in source, module


# ---------------------------------------------------------------- leave requests


class TestLeaveRequestIds:
    def _submit(self, employee, leave_type, reason="Alice's leave"):
        return get_leave_request_service().submit_leave_request(
            SubmitLeaveRequestCommand(
                employee_id=employee.pk, leave_type_id=leave_type.id,
                start_date=date(YEAR, 3, 4), end_date=date(YEAR, 3, 6), reason=reason,
            ),
            LeaveActor(employee_id=employee.pk, permissions=PermissionSet.empty()),
        )

    def test_submission_gets_a_database_assigned_id(self, annual):
        alice = make_employee("Alice")
        LeaveBalance.objects.create(employee=alice, leave_type=annual, year=YEAR, days_remaining=Decimal("20"))
        dto = self._submit(alice, annual)
        row = LeaveRequest.objects.get(pk=dto.id)
        assert (row.employee_id, row.reason) == (alice.pk, "Alice's leave")

    def test_interleaved_insert_is_not_overwritten(self, annual, monkeypatch):
        alice, bob = make_employee("Alice"), make_employee("Bob")
        LeaveBalance.objects.create(employee=alice, leave_type=annual, year=YEAR, days_remaining=Decimal("20"))
        victims = write_victim_first(
            monkeypatch, DjangoLeaveRequestRepository,
            lambda: LeaveRequest.objects.create(
                employee=bob, leave_type=annual, start_date=date(YEAR, 5, 1),
                end_date=date(YEAR, 5, 2), reason="Bob's leave",
            ),
        )

        dto = self._submit(alice, annual)

        bob_row = LeaveRequest.objects.get(pk=victims[0].pk)
        assert (bob_row.employee_id, bob_row.reason, bob_row.start_date) == (
            bob.pk, "Bob's leave", date(YEAR, 5, 1)
        )
        assert dto.id != bob_row.pk
        assert LeaveRequest.objects.get(pk=dto.id).employee_id == alice.pk
        assert LeaveRequest.objects.count() == 2

    def test_saving_an_unknown_id_is_refused_not_inserted(self, annual):
        alice = make_employee("Alice")
        ghost = LeaveRequestEntity(
            id=987654, employee_id=alice.pk, leave_type_id=annual.id,
            period=LeavePeriod(start_date=date(YEAR, 1, 6), end_date=date(YEAR, 1, 7)),
        )
        with pytest.raises(NotFoundError):
            DjangoLeaveRequestRepository().save(ghost)
        assert not LeaveRequest.objects.filter(pk=987654).exists()
        assert LeaveRequest.objects.count() == 0

    def test_saving_a_known_id_still_updates_that_row(self, annual):
        alice = make_employee("Alice")
        row = LeaveRequest.objects.create(
            employee=alice, leave_type=annual, start_date=date(YEAR, 1, 6),
            end_date=date(YEAR, 1, 7), reason="before",
        )
        repo = DjangoLeaveRequestRepository()
        entity = repo.get_by_id(row.pk)
        entity.reason = "after"
        repo.save(entity)
        row.refresh_from_db()
        assert row.reason == "after"
        assert LeaveRequest.objects.count() == 1


# ---------------------------------------------------------------- leave balances


class TestLeaveBalanceIds:
    def _manager(self):
        return LeaveActor(employee_id=None, permissions=PermissionSet.from_list([L.BALANCE_MANAGE]))

    def test_created_balance_gets_a_database_assigned_id(self, annual):
        alice = make_employee("Alice")
        dto = get_leave_balance_service().create_or_update_balance(
            CreateLeaveBalanceCommand(employee_id=alice.pk, leave_type_id=annual.id,
                                      year=YEAR, entitled_days=Decimal("18")),
            self._manager(),
        )
        assert LeaveBalance.objects.get(pk=dto.id).employee_id == alice.pk

    def test_interleaved_insert_is_not_overwritten(self, annual, monkeypatch):
        alice, bob = make_employee("Alice"), make_employee("Bob")
        victims = write_victim_first(
            monkeypatch, DjangoLeaveBalanceRepository,
            lambda: LeaveBalance.objects.create(
                employee=bob, leave_type=annual, year=YEAR, days_remaining=Decimal("7.5"),
            ),
        )

        dto = get_leave_balance_service().create_or_update_balance(
            CreateLeaveBalanceCommand(employee_id=alice.pk, leave_type_id=annual.id,
                                      year=YEAR, entitled_days=Decimal("18")),
            self._manager(),
        )

        bob_row = LeaveBalance.objects.get(pk=victims[0].pk)
        assert (bob_row.employee_id, bob_row.days_remaining) == (bob.pk, Decimal("7.5"))
        assert dto.id != bob_row.pk
        assert LeaveBalance.objects.get(pk=dto.id).employee_id == alice.pk

    def test_initialisation_interleaved_insert_is_not_overwritten(self, annual, monkeypatch):
        alice, bob = make_employee("Alice"), make_employee("Bob")
        victims = write_victim_first(
            monkeypatch, DjangoLeaveBalanceRepository,
            lambda: LeaveBalance.objects.create(
                employee=bob, leave_type=annual, year=YEAR, days_remaining=Decimal("3"),
            ),
        )

        results = get_leave_balance_service().initialize_balances_for_employee(
            alice.pk, YEAR, self._manager()
        )

        assert results and all(r.employee_id == alice.pk for r in results)
        bob_row = LeaveBalance.objects.get(pk=victims[0].pk)
        assert (bob_row.employee_id, bob_row.days_remaining) == (bob.pk, Decimal("3"))
        assert LeaveBalance.objects.filter(employee=alice).count() == LeaveType.objects.count()

    def test_saving_an_unknown_id_is_refused_not_inserted(self, annual):
        alice = make_employee("Alice")
        ghost = LeaveBalanceEntity(
            id=987654, employee_id=alice.pk, leave_type_id=annual.id, year=YEAR,
            entitlement=LeaveEntitlement(entitled_days=Decimal("20"), used_days=Decimal("0")),
        )
        with pytest.raises(NotFoundError):
            DjangoLeaveBalanceRepository().save(ghost)
        assert LeaveBalance.objects.count() == 0


# ---------------------------------------------------------------- leave types


class TestLeaveTypeIds:
    """
    LeaveTypeService.create_leave_type cannot currently succeed (it builds
    LeaveTypeCreated with a keyword the event does not define - pre-existing,
    pinned by a strict xfail in test_leave_authorization.py), so creation is
    exercised at the repository: the service now only ever hands it id=None.
    """

    def test_new_type_gets_a_database_assigned_id_next_to_an_interleaved_insert(self):
        pending = LeaveTypeEntity(id=None, name="Study", default_days_allowed=5)
        victim = LeaveType.objects.create(name="Compassionate", default_days_allowed=3)

        saved = DjangoLeaveTypeRepository().save(pending)

        assert saved.id is not None and saved.id != victim.pk
        victim.refresh_from_db()
        assert (victim.name, victim.default_days_allowed) == ("Compassionate", 3)
        assert LeaveType.objects.get(pk=saved.id).name == "Study"

    def test_service_hands_the_repository_no_id(self, monkeypatch):
        from modules.leave.api.views import get_leave_type_service
        from modules.leave.application.services.leave_type_service import CreateLeaveTypeCommand

        seen = []
        real_save = DjangoLeaveTypeRepository.save
        monkeypatch.setattr(DjangoLeaveTypeRepository, "save",
                            lambda self, t: seen.append(t.id) or real_save(self, t))
        actor = LeaveActor(employee_id=None, permissions=PermissionSet.from_list([L.TYPE_MANAGE]))
        with pytest.raises(TypeError):  # the pre-existing event bug, raised before save
            get_leave_type_service().create_leave_type(
                CreateLeaveTypeCommand(name="Sabbatical", default_days_allowed=30), actor
            )
        # Fails before persisting anything - REM-06 must not turn that into a partial write.
        assert seen == []
        assert not LeaveType.objects.filter(name="Sabbatical").exists()

    def test_saving_an_unknown_id_is_refused_not_inserted(self):
        with pytest.raises(NotFoundError):
            DjangoLeaveTypeRepository().save(
                LeaveTypeEntity(id=987654, name="Ghost", default_days_allowed=1)
            )
        assert not LeaveType.objects.filter(name="Ghost").exists()


# ---------------------------------------------------------------- sequence migration


class _Editor:
    pass


def test_sequence_migration_moves_lagging_sequences_past_existing_rows(annual):
    """
    Explicit-ID inserts (the old scheme) leave a PostgreSQL sequence behind;
    migration 0004 must move it forward so a database-assigned insert does
    not collide with an existing row.
    """
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Sequences only lag on PostgreSQL")
    migration = import_module("modules.leave.migrations.0004_advance_id_sequences")
    alice = make_employee("Alice")

    LeaveType.objects.create(id=5000, name="Legacy", default_days_allowed=1)
    LeaveBalance.objects.create(id=5000, employee=alice, leave_type=annual, year=YEAR,
                                days_remaining=Decimal("1"))
    LeaveRequest.objects.create(id=5000, employee=alice, leave_type=annual,
                                start_date=date(YEAR, 1, 6), end_date=date(YEAR, 1, 6),
                                reason="Legacy")

    editor = _Editor()
    editor.connection = connection
    migration.advance_sequences(None, editor)
    migration.advance_sequences(None, editor)  # idempotent

    new_type = LeaveType.objects.create(name="New", default_days_allowed=1)
    new_balance = LeaveBalance.objects.create(employee=alice, leave_type=new_type, year=YEAR,
                                              days_remaining=Decimal("1"))
    new_request = LeaveRequest.objects.create(employee=alice, leave_type=annual,
                                              start_date=date(YEAR, 2, 6), end_date=date(YEAR, 2, 6))
    assert min(new_type.id, new_balance.id, new_request.id) > 5000
    assert LeaveType.objects.get(pk=5000).name == "Legacy"
    assert LeaveRequest.objects.get(pk=5000).reason == "Legacy"
