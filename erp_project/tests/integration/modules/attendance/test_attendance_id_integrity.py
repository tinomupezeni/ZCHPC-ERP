"""
REM-06: attendance and QR-token primary keys are database-assigned.

AttendanceService.clock_in and QRTokenService used to stamp new records with
max(id) + 1, and the repositories then ran "UPDATE ... WHERE id = that; if
nothing updated, INSERT". A row inserted by anyone else in between took that
same id, so the UPDATE rewrote it: another employee's clock-in became this
employee's, and both callers were told they succeeded. New records now carry
id=None and are INSERTed; an explicit id only ever updates its own row.
"""

import itertools
from datetime import date, datetime, timedelta, time
from importlib import import_module

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.attendance.api.views import get_attendance_service, get_qr_token_service
from modules.attendance.application.interfaces import IAttendanceRepository, IQRTokenRepository
from modules.attendance.application.services import ClockInCommand
from modules.attendance.domain.entities import AttendanceRecord as AttendanceEntity, QRToken
from modules.attendance.domain.value_objects import ClockTime
from modules.attendance.infrastructure.persistence.attendance_repository import (
    DjangoAttendanceRepository,
)
from modules.attendance.infrastructure.persistence.models import AttendanceRecord
from modules.attendance.infrastructure.persistence.qr_token_repository import DjangoQRTokenRepository
from modules.hr.infrastructure.persistence.models import Employees
from modules.portal.infrastructure.persistence.models import AttendanceQRToken
from shared.domain.exceptions import NotFoundError

User = get_user_model()
_numbers = itertools.count(63001)


def make_employee(first):
    n = next(_numbers)
    user = User.objects.create_user(email=f"{first.lower()}{n}@zchpc.test", password="Pass12345!")
    return Employees.objects.create(
        user=user, first_name=first, surname="Tester", email=user.email, employee_id=f"EMP{n}",
    )


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


def row(record):
    record.refresh_from_db()
    return record.employee_id, record.date, record.time_in, record.time_out


# ---------------------------------------------------------------- structural


class TestNoRepositoryMintsIds:
    def test_repositories_and_interfaces_expose_no_get_next_id(self):
        for cls in (IAttendanceRepository, IQRTokenRepository,
                    DjangoAttendanceRepository, DjangoQRTokenRepository):
            assert not hasattr(cls, "get_next_id"), cls

    def test_no_attendance_source_computes_the_next_primary_key(self):
        import inspect

        from modules.attendance.application.services import attendance_app_service, qr_token_service
        from modules.attendance.infrastructure.persistence import attendance_repository, qr_token_repository

        for module in (attendance_app_service, qr_token_service,
                       attendance_repository, qr_token_repository):
            source = inspect.getsource(module)
            assert "get_next_id" not in source, module
            assert 'order_by("-id")' not in source, module


# ---------------------------------------------------------------- attendance records


@pytest.mark.django_db
class TestAttendanceRecordIds:
    def test_clock_in_gets_a_database_assigned_id(self):
        alice = make_employee("Alice")
        record = get_attendance_service().clock_in(ClockInCommand(employee_id=alice.pk))
        assert AttendanceRecord.objects.get(pk=record.id).employee_id == alice.pk

    def test_interleaved_clock_in_is_not_overwritten(self, monkeypatch):
        alice, bob = make_employee("Alice"), make_employee("Bob")
        victims = write_victim_first(
            monkeypatch, DjangoAttendanceRepository,
            lambda: AttendanceRecord.objects.create(employee=bob, date=date.today(), time_in=time(7, 45)),
        )

        record = get_attendance_service().clock_in(ClockInCommand(employee_id=alice.pk))

        bob_row = victims[0]
        assert row(bob_row) == (bob.pk, date.today(), time(7, 45), None)
        assert record.id != bob_row.pk
        assert AttendanceRecord.objects.get(pk=record.id).employee_id == alice.pk
        assert AttendanceRecord.objects.filter(date=date.today()).count() == 2

    def test_saving_an_unknown_id_is_refused_not_inserted(self):
        alice = make_employee("Alice")
        ghost = AttendanceEntity.create_for_clock_in(
            id=987654, employee_id=alice.pk, record_date=date.today(),
            clock_in_time=ClockTime.from_time(time(8, 0)),
        )
        with pytest.raises(NotFoundError):
            DjangoAttendanceRepository().save(ghost)
        assert AttendanceRecord.objects.count() == 0

    def test_clock_out_still_updates_the_existing_row(self):
        alice = make_employee("Alice")
        service = get_attendance_service()
        now = datetime.now()
        record = service.clock_in(ClockInCommand(employee_id=alice.pk, clock_time=now.replace(hour=8, minute=0)))
        from modules.attendance.application.services import ClockOutCommand

        service.clock_out(ClockOutCommand(employee_id=alice.pk, clock_time=now.replace(hour=17, minute=0)))
        assert AttendanceRecord.objects.count() == 1
        updated = AttendanceRecord.objects.get(pk=record.id)
        assert updated.time_out is not None and updated.time_out.hour == 17


# ---------------------------------------------------------------- QR tokens


@pytest.mark.django_db
class TestQRTokenIds:
    """
    Exercisable because this repository's model import was corrected as the
    minimal enabling change for REM-06 (it named a non-existent package).
    """

    def test_new_token_gets_a_database_assigned_id(self):
        dto = get_qr_token_service().get_or_create_current_token()
        assert AttendanceQRToken.objects.filter(token=dto.token).exists()

    def test_interleaved_token_is_not_overwritten(self, monkeypatch):
        victims = write_victim_first(
            monkeypatch, DjangoQRTokenRepository,
            lambda: AttendanceQRToken.objects.create(
                token="VICTIM-TOKEN-VALUE", expires_at=timezone.now() + timedelta(minutes=5),
            ),
        )

        dto = get_qr_token_service().get_or_create_current_token()

        victim = AttendanceQRToken.objects.get(pk=victims[0].pk)
        assert victim.token == "VICTIM-TOKEN-VALUE"
        assert dto.token != "VICTIM-TOKEN-VALUE"
        assert AttendanceQRToken.objects.filter(token=dto.token).exclude(pk=victim.pk).exists()

    def test_saving_an_unknown_id_is_refused_not_inserted(self):
        with pytest.raises(NotFoundError):
            DjangoQRTokenRepository().save(QRToken.create(id=987654, validity_seconds=30))
        assert AttendanceQRToken.objects.count() == 0


# ---------------------------------------------------------------- sequence migrations


class _Editor:
    pass


@pytest.mark.django_db
@pytest.mark.parametrize("migration_path", [
    "modules.attendance.migrations.0003_advance_id_sequences",
    "modules.portal.migrations.0004_advance_attendance_qr_token_sequence",
])
def test_sequence_migrations_move_lagging_sequences_past_existing_rows(migration_path):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("Sequences only lag on PostgreSQL")
    migration = import_module(migration_path)
    alice = make_employee("Alice")
    AttendanceRecord.objects.create(id=5000, employee=alice, date=date(2020, 1, 1))
    AttendanceQRToken.objects.create(id=5000, token="LEGACY", expires_at=timezone.now())

    editor = _Editor()
    editor.connection = connection
    migration.advance_sequences(None, editor)
    migration.advance_sequences(None, editor)  # idempotent

    if "attendance" in migration.TABLES[0]:
        fresh = AttendanceRecord.objects.create(employee=alice, date=date(2020, 1, 2))
        assert AttendanceRecord.objects.get(pk=5000).date == date(2020, 1, 1)
    else:
        fresh = AttendanceQRToken.objects.create(token="NEW", expires_at=timezone.now())
        assert AttendanceQRToken.objects.get(pk=5000).token == "LEGACY"
    assert fresh.id > 5000


# ---------------------------------------------------------------- real concurrency


@pytest.mark.django_db(transaction=True)
def test_concurrent_clock_ins_get_distinct_rows_and_leave_the_victim_intact():
    import threading

    from django.db import connection

    if connection.vendor == "sqlite":
        pytest.skip(
            "SQLite's shared-cache in-memory test DB raises 'database table is "
            "locked' on concurrent writers instead of waiting; run on PostgreSQL"
        )

    victim_employee = make_employee("Victim")
    victim = AttendanceRecord.objects.create(employee=victim_employee, date=date.today(), time_in=time(7, 30))
    before = row(victim)
    employees = [make_employee(f"Worker{i}") for i in range(8)]
    barrier = threading.Barrier(len(employees))
    errors = []

    def clock_in(employee_id):
        try:
            barrier.wait()
            get_attendance_service().clock_in(ClockInCommand(employee_id=employee_id))
        except Exception as exc:  # noqa: BLE001 - reported below
            errors.append(repr(exc))
        finally:
            connection.close()

    threads = [threading.Thread(target=clock_in, args=(e.pk,)) for e in employees]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    created = AttendanceRecord.objects.filter(employee__in=employees, date=date.today())
    assert created.count() == len(employees)
    assert len({r.pk for r in created}) == len(employees)
    assert {r.employee_id for r in created} == {e.pk for e in employees}
    assert row(victim) == before
