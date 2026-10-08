"""
flag_surname_passwords: the REM-07 surname-password sweep.

The command took over the work of identity migration 0005 so the expensive
hash checks run outside the deployment window. The rule must be exactly the
migration's: flag an account when its employee has a non-empty surname, it
is not already flagged, it holds a password, and check_password(<surname as
stored>, <hash>) is true. These tests pin that rule and the command's
paging, rerun, concurrency, privacy and failure behaviour.
"""

from io import StringIO
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.core.management import ManagementUtility, call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from modules.hr.infrastructure.persistence.models import Employees
from modules.identity.management.commands import flag_surname_passwords as command_module

pytestmark = pytest.mark.django_db

User = get_user_model()
STRONG = "Str0ng-Unrelated-Passw0rd"
_numbers = count(81001)


def employee(surname="Person", password=None, *, flagged=False, unusable=False, stored_hash=None):
    """An employee with a login whose password defaults to the surname (legacy)."""
    n = next(_numbers)
    email = f"sweep{n}@zchpc.test"
    user = User.objects.create_user(email=email, password=surname if password is None else password)
    if unusable:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    if stored_hash is not None:
        User.objects.filter(pk=user.pk).update(password=stored_hash)
    if flagged:
        User.objects.filter(pk=user.pk).update(must_change_password=True)
    return Employees.objects.create(
        user=user, first_name="Tendai", surname=surname, email=email, employee_id=f"EMP{n}"
    )


def is_flagged(emp):
    return User.objects.get(pk=emp.user_id).must_change_password


def run(*args):
    out = StringIO()
    call_command("flag_surname_passwords", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def summary(output):
    return output.strip().splitlines()[-1]


def race(monkeypatch, mutate):
    """Run mutate() right after each hash check - between check and update."""
    real = command_module.check_password

    def check(raw, encoded):
        result = real(raw, encoded)
        mutate()
        return result

    monkeypatch.setattr(command_module, "check_password", check)


class TestSelection:
    def test_flags_exactly_the_accounts_whose_password_is_the_stored_surname(self):
        legacy = employee("Person")
        strong = employee("Person", STRONG)
        other_case = employee("Person", "person")
        trailing_space_surname = employee("Person ", "Person")
        exact_spaces = employee(" Moyo ", " Moyo ")

        run()

        assert is_flagged(legacy) is True
        assert is_flagged(exact_spaces) is True  # the surname exactly as stored
        assert is_flagged(strong) is False
        assert is_flagged(other_case) is False  # no case folding
        assert is_flagged(trailing_space_surname) is False  # no trimming

    def test_blank_surnames_empty_unusable_or_malformed_hashes_are_not_flagged(self):
        blank_surname = employee("", "")
        empty_hash = employee("Person", stored_hash="")
        unusable = employee("Person", unusable=True)
        malformed = employee("Person", stored_hash="not-a-django-hash")

        output = run()

        for emp in (blank_surname, empty_hash, unusable, malformed):
            assert is_flagged(emp) is False
        # The blank surname is never selected; the other three are checked.
        assert "checked=3 matched=0 flagged=0" in summary(output)

    def test_employees_without_a_login_are_ignored(self):
        no_login = Employees.objects.create(
            first_name="No", surname="Login", email="", employee_id=f"EMP{next(_numbers)}"
        )
        no_login.refresh_from_db()
        assert no_login.user_id is None

        assert "checked=0" in summary(run())

    def test_already_flagged_accounts_are_left_alone_and_not_rechecked(self):
        flagged = employee("Person", flagged=True)
        flagged_strong = employee("Person", STRONG, flagged=True)

        output = run()

        assert is_flagged(flagged) is True
        assert is_flagged(flagged_strong) is True
        assert "checked=0" in summary(output)

    def test_password_hashes_are_never_modified(self):
        employee("Person")
        employee("Person", STRONG)
        employee("Person", unusable=True)
        hashes = dict(User.objects.values_list("pk", "password"))

        run()
        run()

        assert dict(User.objects.values_list("pk", "password")) == hashes


class TestReruns:
    def test_a_rerun_flags_nothing_new_and_changes_nothing(self):
        legacy = employee("Person")
        strong = employee("Person", STRONG)

        first = run()
        state = dict(User.objects.values_list("pk", "must_change_password"))
        second = run()

        assert "matched=1 flagged=1 changed=0" in summary(first)
        assert "checked=1 matched=0 flagged=0 changed=0" in summary(second)  # only `strong`
        assert dict(User.objects.values_list("pk", "must_change_password")) == state
        assert is_flagged(legacy) is True and is_flagged(strong) is False


class TestPagination:
    def test_pages_are_bounded_and_keyed_on_the_employee_primary_key(self):
        legacy = [employee("Person") for _ in range(5)]
        table = Employees._meta.db_table

        with CaptureQueriesContext(connection) as queries:
            output = run("--batch-size", "2")

        pages = [line for line in output.splitlines() if line.startswith("page:")]
        assert len(pages) == 3
        assert pages[-1].endswith(f"last_employee_pk={legacy[-1].pk}")
        assert all(is_flagged(emp) for emp in legacy)
        reads = [q["sql"] for q in queries.captured_queries if q["sql"].startswith("SELECT") and table in q["sql"]]
        assert len(reads) == 4  # three pages and the empty read that ends the run
        assert all("LIMIT 2" in sql and "ORDER BY" in sql for sql in reads)

    def test_start_after_resumes_after_the_given_employee_pk(self):
        first, second, third = employee("Person"), employee("Person"), employee("Person")

        output = run("--start-after", str(second.pk))

        assert is_flagged(first) is False
        assert is_flagged(second) is False
        assert is_flagged(third) is True
        assert "checked=1" in summary(output)
        assert summary(output).endswith(f"last_employee_pk={third.pk}")

    @pytest.mark.parametrize(
        "args, message",
        [
            (("--batch-size", "0"), "--batch-size must be at least 1."),
            (("--start-after", "-1"), "--start-after must not be negative."),
        ],
    )
    def test_invalid_options_are_rejected(self, args, message):
        with pytest.raises(CommandError, match=message):
            run(*args)


class TestDryRun:
    def test_dry_run_reports_matches_and_saves_nothing(self):
        legacy = employee("Person")
        employee("Person", STRONG)

        output = run("--dry-run")

        assert is_flagged(legacy) is False
        assert summary(output).startswith("[dry run - nothing saved] complete:")
        assert "checked=2 would_flag=1" in summary(output)


class TestConcurrentChanges:
    """
    Each write is conditional on the account still being exactly what was
    checked. A change between the hash check and the write is not flagged on
    stale data: it is counted as "changed", and a rerun re-checks it.
    """

    def _race_on(self, monkeypatch, target, mutate):
        done = []

        def once():
            if not done:
                done.append(True)
                mutate(target)

        race(monkeypatch, once)

    def test_password_changed_after_the_check_is_not_flagged(self, monkeypatch):
        target, bystander = employee("Person"), employee("Person")

        def change_password(emp):
            user = User.objects.get(pk=emp.user_id)
            user.set_password(STRONG)
            user.save(update_fields=["password"])

        self._race_on(monkeypatch, target, change_password)
        output = run()

        assert is_flagged(target) is False
        assert is_flagged(bystander) is True
        assert "matched=2 flagged=1 changed=1" in summary(output)
        monkeypatch.undo()
        assert "matched=0" in summary(run())  # a rerun sees the new password

    def test_already_flagged_meanwhile_is_counted_as_changed(self, monkeypatch):
        target = employee("Person")

        def flag(emp):
            User.objects.filter(pk=emp.user_id).update(must_change_password=True)

        self._race_on(monkeypatch, target, flag)
        output = run()

        assert is_flagged(target) is True
        assert "matched=1 flagged=0 changed=1" in summary(output)

    def test_surname_changed_after_the_check_is_not_flagged_on_the_old_surname(self, monkeypatch):
        target = employee("Person")

        def rename(emp):
            Employees.objects.filter(pk=emp.pk).update(surname="Renamed")

        self._race_on(monkeypatch, target, rename)
        output = run()

        assert is_flagged(target) is False
        assert "flagged=0 changed=1" in summary(output)
        monkeypatch.undo()
        # The rule uses the current surname, which the password no longer equals.
        assert "matched=0" in summary(run())

    def test_login_unlinked_after_the_check_is_not_flagged(self, monkeypatch):
        target = employee("Person")
        user_pk = target.user_id

        def unlink(emp):
            Employees.objects.filter(pk=emp.pk).update(user=None)

        self._race_on(monkeypatch, target, unlink)
        output = run()

        assert User.objects.get(pk=user_pk).must_change_password is False
        assert "flagged=0 changed=1" in summary(output)

    def test_login_moved_to_another_employee_after_the_check_is_not_flagged(self, monkeypatch):
        target = employee("Person")
        user_pk = target.user_id

        def relink(emp):
            Employees.objects.filter(pk=emp.pk).update(user=None)
            Employees.objects.create(
                user_id=user_pk, first_name="Other", surname="Other",
                email=f"other{next(_numbers)}@zchpc.test", employee_id=f"EMP{next(_numbers)}",
            )

        self._race_on(monkeypatch, target, relink)
        output = run()

        # The stale match is not written; the login's new employee is then
        # checked on its own surname, which the password does not equal.
        assert User.objects.get(pk=user_pk).must_change_password is False
        assert "checked=2 matched=1 flagged=0 changed=1" in summary(output)


class TestFailure:
    def _fail_on_call(self, monkeypatch, n, secret):
        real = command_module.check_password
        calls = []

        def check(raw, encoded):
            calls.append(True)
            if len(calls) == n:
                raise RuntimeError(f"boom for {secret}")
            return real(raw, encoded)

        monkeypatch.setattr(command_module, "check_password", check)

    def test_failure_raises_keeps_completed_pages_and_can_be_resumed(self, monkeypatch):
        first, second, third = employee("Person"), employee("Person"), employee("Person")
        self._fail_on_call(monkeypatch, 3, "x")
        out = StringIO()

        with pytest.raises(CommandError) as failure:
            call_command("flag_surname_passwords", "--batch-size", "2", stdout=out)

        message = str(failure.value)
        assert f"failed after employee pk {second.pk} (RuntimeError)" in message
        assert f"Resume with --start-after {second.pk}." in message
        assert "flagged=2" in message
        assert "complete" not in out.getvalue()
        assert is_flagged(first) and is_flagged(second)
        assert is_flagged(third) is False

        monkeypatch.undo()
        resumed = run("--start-after", str(second.pk))
        assert "checked=1 matched=1 flagged=1" in summary(resumed)
        assert is_flagged(third) is True

    def test_failure_exits_non_zero_from_the_command_line(self, monkeypatch, capsys):
        employee("Person")
        self._fail_on_call(monkeypatch, 1, "x")

        with pytest.raises(SystemExit) as exit_info:
            ManagementUtility(["manage.py", "flag_surname_passwords"]).execute()

        assert exit_info.value.code != 0
        captured = capsys.readouterr()
        assert "failed after employee pk" in captured.err
        assert "complete" not in captured.out


class TestNoPersonalDataInOutput:
    def test_output_holds_counts_and_primary_keys_only(self, monkeypatch, capsys):
        emp = employee("Zvobgo")
        employee("Zvobgo", STRONG)
        Employees.objects.filter(pk=emp.pk).update(first_name="Rutendo")
        private = [
            "Zvobgo", "Rutendo", "Tendai", "@zchpc.test", "EMP", "pbkdf2",
            *User.objects.values_list("password", flat=True),
            *Employees.objects.values_list("employee_id", flat=True),
        ]

        outputs = [run("--dry-run"), run()]
        employee("Zvobgo")
        self._leaky_failure(monkeypatch)
        with pytest.raises(SystemExit):
            ManagementUtility(["manage.py", "flag_surname_passwords"]).execute()
        captured = capsys.readouterr()
        outputs += [captured.out, captured.err]

        text = "\n".join(outputs)
        assert "failed after employee pk" in text  # the failure path was exercised
        for value in private:
            assert value not in text

    @staticmethod
    def _leaky_failure(monkeypatch):
        """An exception whose message quotes personal data must not reach the output."""

        def check(raw, encoded):
            raise ValueError(f"cannot check {raw!r} against {encoded!r}")

        monkeypatch.setattr(command_module, "check_password", check)
