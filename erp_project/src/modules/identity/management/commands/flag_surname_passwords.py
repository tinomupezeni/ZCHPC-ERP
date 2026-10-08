"""
Flag logins still holding the surname password (REM-07).

Until REM-07, every login provisioned for a new employee received the
employee's surname as its password. This command finds those accounts and
marks them must_change_password, so RBACMiddleware confines them to the
password change. It replaces the work identity migration 0005 used to do at
deploy time.

The rule is unchanged from that migration: an account is flagged when its
employee has a non-empty surname, the account is not already flagged, holds a
password, and check_password(<the surname exactly as stored>, <hash>) is
true. No hash is read into plaintext, rewritten or replaced.

How it runs:
- Employees are read in pages ordered by primary key (keyset pagination:
  each page starts after the last pk seen), so memory stays flat and a
  page's flags never shift what the next page sees.
- The expensive hash checks run with no transaction open and no lock held.
- Each page's flags are written in one short transaction. Every write is
  conditional on the account still matching what was checked - same
  password hash, still not flagged, still linked to the same employee with
  the same surname - so a concurrent password change, relink or surname edit
  is never flagged on stale data; it is counted as "changed" and a rerun
  re-checks it.
- Flagged accounts are skipped, so reruns are safe and only flag what is
  left. --start-after resumes after a given employee pk.

Output is aggregate counts and employee primary keys only - never passwords,
hashes, names, emails or EC numbers.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.hr.infrastructure.persistence.models import Employees

User = get_user_model()

DEFAULT_BATCH_SIZE = 100


class Command(BaseCommand):
    help = (
        "Flag logins whose password is still the employee's surname "
        "(must_change_password). Safe to rerun; see docs/DEPLOYMENT.md."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help=f"Employees checked per page (default: {DEFAULT_BATCH_SIZE}).",
        )
        parser.add_argument(
            "--start-after",
            type=int,
            default=0,
            metavar="PK",
            help="Resume after this employee primary key (from an earlier run's output).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many accounts would be flagged without saving anything.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]
        last_pk = options["start_after"]
        if batch_size < 1:
            raise CommandError("--batch-size must be at least 1.")
        if last_pk < 0:
            raise CommandError("--start-after must not be negative.")
        totals = {"checked": 0, "matched": 0, "flagged": 0, "changed": 0}
        prefix = "[dry run - nothing saved] " if dry_run else ""

        try:
            while True:
                page = self._next_page(last_pk, batch_size)
                if not page:
                    break
                matches = [row for row in page if row[3] and check_password(row[2], row[3])]
                flagged = changed = 0
                if matches and not dry_run:
                    flagged = self._flag(matches)
                    changed = len(matches) - flagged
                last_pk = page[-1][0]

                totals["checked"] += len(page)
                totals["matched"] += len(matches)
                totals["flagged"] += flagged
                totals["changed"] += changed
                self.stdout.write(
                    f"{prefix}page: checked={len(page)} matched={len(matches)} "
                    f"flagged={flagged} changed={changed} last_employee_pk={last_pk}"
                )
        except Exception as exc:
            # The exception's message may quote row data, so only its type is
            # reported. Pages before last_pk are complete and committed.
            raise CommandError(
                f"{prefix}failed after employee pk {last_pk} ({type(exc).__name__}); "
                f"so far: checked={totals['checked']} matched={totals['matched']} "
                f"flagged={totals['flagged']} changed={totals['changed']}. "
                f"Resume with --start-after {last_pk}."
            ) from exc

        if dry_run:
            summary = (
                f"{prefix}complete: checked={totals['checked']} "
                f"would_flag={totals['matched']} last_employee_pk={last_pk}"
            )
        else:
            summary = (
                f"complete: checked={totals['checked']} matched={totals['matched']} "
                f"flagged={totals['flagged']} changed={totals['changed']} "
                f"last_employee_pk={last_pk}"
            )
        self.stdout.write(self.style.SUCCESS(summary))

    @staticmethod
    def _next_page(after_pk, batch_size):
        """(employee pk, user pk, surname, password hash) rows after after_pk."""
        return list(
            Employees.objects.filter(
                pk__gt=after_pk, user__isnull=False, user__must_change_password=False
            )
            .exclude(surname="")
            .order_by("pk")
            .values_list("pk", "user_id", "surname", "user__password")[:batch_size]
        )

    @staticmethod
    def _flag(matches):
        """Flag each match still exactly as checked; return how many were flagged."""
        flagged = 0
        with transaction.atomic():
            for employee_pk, user_pk, surname, password in matches:
                flagged += User.objects.filter(
                    pk=user_pk,
                    password=password,
                    must_change_password=False,
                    employee_profile__pk=employee_pk,
                    employee_profile__surname=surname,
                ).update(must_change_password=True)
        return flagged
