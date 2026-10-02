"""
Deploy-time safety of identity migrations 0004 and 0005.

- 0005 no longer checks passwords at deploy time (the flag_surname_passwords
  command does); applying it must change nothing.
- 0004's ALTER TABLE runs under SET LOCAL lock_timeout = '2s', so a held
  lock fails the migration promptly - forwards and backwards - instead of
  queueing every query on the users table behind it. SQLite is untouched.
"""

import time
from importlib import import_module

import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.operations import AddField, RunPython

from modules.hr.infrastructure.persistence.models import Employees

m0004 = import_module("modules.identity.migrations.0004_customuser_must_change_password")
m0005 = import_module("modules.identity.migrations.0005_flag_surname_passwords")

AT_0003 = [("identity", "0003_seed_core_system_modules")]
AT_0004 = [("identity", "0004_customuser_must_change_password")]
AT_0005 = [("identity", "0005_flag_surname_passwords")]
USERS_TABLE = "authentication_customuser"

postgres_only = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="lock_timeout is PostgreSQL-only"
)


def _migrate(targets):
    MigrationExecutor(connection).migrate(targets)


def _restore_latest():
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def _applied(migration):
    return migration in MigrationExecutor(connection).recorder.applied_migrations()


def _has_flag_column():
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, USERS_TABLE)
    return "must_change_password" in {column.name for column in columns}


def _show_lock_timeout():
    with connection.cursor() as cursor:
        cursor.execute("SHOW lock_timeout")
        return cursor.fetchone()[0]


class _FakeEditor:
    def __init__(self, vendor, in_atomic_block):
        self.connection = type("Conn", (), {"vendor": vendor, "in_atomic_block": in_atomic_block})()
        self.executed = []

    def execute(self, sql):
        self.executed.append(sql)


# =============================================================================
# 0005 is a no-op
# =============================================================================


class TestMigration0005:
    def test_its_only_operation_is_a_noop_both_ways(self):
        assert [type(op) for op in m0005.Migration.operations] == [RunPython]
        (operation,) = m0005.Migration.operations
        assert operation.code is RunPython.noop
        assert operation.reverse_code is RunPython.noop

    def test_identity_and_dependencies_are_unchanged(self):
        assert m0005.Migration.dependencies == [
            ("identity", "0004_customuser_must_change_password"),
            ("hr", "0020_seed_employee_lifecycle_permissions"),
        ]

    @pytest.mark.django_db(transaction=True)
    def test_applying_it_flags_nothing(self):
        user = get_user_model().objects.create_user(email="legacy@zchpc.test", password="Person")
        Employees.objects.create(
            user=user, first_name="Legacy", surname="Person",
            email="legacy@zchpc.test", employee_id="EMP88001",
        )
        try:
            _migrate(AT_0004)
            assert not _applied(AT_0005[0])
            _migrate(AT_0005)
            assert _applied(AT_0005[0])
            user.refresh_from_db()
            assert user.must_change_password is False
        finally:
            _restore_latest()


# =============================================================================
# 0004 lock timeout
# =============================================================================


class TestMigration0004LockTimeout:
    def test_timeout_precedes_the_ddl_in_both_directions(self):
        first, ddl, last = m0004.Migration.operations
        assert isinstance(ddl, AddField) and ddl.name == "must_change_password"
        # Forwards: set before AddField. Backwards (reverse order): set before
        # the column is dropped.
        assert first.code is m0004.set_lock_timeout
        assert first.reverse_code is RunPython.noop
        assert last.code is RunPython.noop
        assert last.reverse_code is m0004.set_lock_timeout
        assert m0004.Migration.atomic is True
        assert m0004.LOCK_TIMEOUT == "2s"

    def test_postgres_gets_a_transaction_scoped_timeout(self):
        editor = _FakeEditor("postgresql", in_atomic_block=True)
        m0004.set_lock_timeout(None, editor)
        assert editor.executed == ["SET LOCAL lock_timeout = '2s'"]

    def test_sqlite_is_left_alone(self):
        editor = _FakeEditor("sqlite", in_atomic_block=True)
        m0004.set_lock_timeout(None, editor)
        assert editor.executed == []

    def test_refuses_to_run_outside_a_transaction_on_postgres(self):
        editor = _FakeEditor("postgresql", in_atomic_block=False)
        with pytest.raises(RuntimeError, match="transaction"):
            m0004.set_lock_timeout(None, editor)
        assert editor.executed == []

    @pytest.mark.django_db(transaction=True)
    def test_migrates_both_ways_on_the_configured_database(self):
        """Runs on PostgreSQL and on SQLite (USE_SQLITE=1)."""
        try:
            _migrate(AT_0003)
            assert not _has_flag_column()
            _migrate(AT_0004)
            assert _has_flag_column()
        finally:
            _restore_latest()

    @postgres_only
    @pytest.mark.django_db(transaction=True)
    def test_timeout_ends_with_the_migration_transaction(self):
        before = _show_lock_timeout()
        assert before != "2s"
        with connection.schema_editor(atomic=True) as editor:
            m0004.set_lock_timeout(None, editor)
            assert _show_lock_timeout() == "2s"
        assert _show_lock_timeout() == before

    @postgres_only
    @pytest.mark.django_db(transaction=True)
    def test_a_held_lock_fails_the_migration_promptly_in_both_directions(self):
        holder = connection.get_new_connection(connection.get_connection_params())

        def hold_lock():
            # Any lock conflicts with ALTER TABLE's ACCESS EXCLUSIVE.
            holder.execute(f"LOCK TABLE {USERS_TABLE} IN ACCESS SHARE MODE")

        def assert_times_out(targets):
            started = time.monotonic()
            with pytest.raises(OperationalError) as failure:
                _migrate(targets)
            elapsed = time.monotonic() - started
            assert failure.value.__cause__.sqlstate == "55P03"  # lock_not_available
            assert "lock timeout" in str(failure.value)
            assert 1.5 <= elapsed < 10, elapsed

        with connection.cursor() as cursor:
            # Without the fix the ALTER would wait forever; make that fail the
            # test (with a different error) instead of hanging it.
            cursor.execute("SET statement_timeout = '20s'")
        try:
            _migrate(AT_0003)

            hold_lock()
            assert_times_out(AT_0004)
            holder.rollback()
            assert not _applied(AT_0004[0])
            assert not _has_flag_column()  # rolled back, not half-applied

            _migrate(AT_0004)
            hold_lock()
            assert_times_out(AT_0003)  # the reverse DROP COLUMN is protected too
            holder.rollback()
            assert _applied(AT_0004[0])
            assert _has_flag_column()
        finally:
            holder.rollback()
            holder.close()
            with connection.cursor() as cursor:
                cursor.execute("RESET statement_timeout")
            _restore_latest()
