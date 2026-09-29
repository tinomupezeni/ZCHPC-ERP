"""
Management command to import an official Chart of Accounts into AccountChart.

The default source is the ZCHPC chart exported from Sage 200 Evolution
(src/modules/accounts/data/zchpc_chart_of_accounts.csv). See
src/modules/accounts/data/README.md for the file format and provenance.

The import is keyed by account code and is safe to re-run:

    - accounts missing from the database are created
    - accounts already matching the source are left unchanged
    - only fields the source represents are updated: name,
      external_account_type and an explicitly stated parent
    - nothing is ever deleted
    - parents are resolved by account code, never by database id

Source values are stored exactly as supplied. Malformed source data - including
values with surrounding whitespace, which would otherwise need normalising - is
rejected before anything is written.

account_type: the source carries no value for AccountChart.account_type, which
records posting structure (view/regular/consolidation) rather than the Sage
financial type. New accounts are created as 'regular', the value the existing
account repository assigns to every account that is not explicitly a view or
consolidation account. That is a technical default, not an accounting
classification, and existing accounts keep whatever account_type they have.
"""

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[2] / "data" / "zchpc_chart_of_accounts.csv"
)
EXPECTED_HEADER = ["code", "name", "external_account_type", "parent_code"]
DEFAULT_ACCOUNT_TYPE = "regular"


@dataclass(frozen=True)
class SourceAccount:
    """One validated row of the source file."""

    line: int
    code: str
    name: str
    external_account_type: str
    parent_code: str


def read_source(path: Path) -> list[SourceAccount]:
    """
    Parse and validate a chart of accounts CSV.

    Raises CommandError describing every problem found; returns rows only when
    the whole file is valid.
    """
    from modules.accounts.infrastructure.persistence.models import AccountChart

    max_lengths = {
        field: AccountChart._meta.get_field(field).max_length
        for field in ("code", "name", "external_account_type")
    }

    if not path.is_file():
        raise CommandError(f"Source file not found: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CommandError(f"Source file is not valid UTF-8: {exc}") from exc

    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        raise CommandError("Source file is empty") from None
    if header != EXPECTED_HEADER:
        raise CommandError(
            f"Unexpected header {header!r}; expected {EXPECTED_HEADER!r}"
        )

    errors: list[str] = []
    rows: list[SourceAccount] = []
    first_line_for_code: dict[str, int] = {}

    for line, values in enumerate(reader, start=2):
        if not values:
            errors.append(f"line {line}: blank line")
            continue
        if len(values) != len(EXPECTED_HEADER):
            errors.append(
                f"line {line}: expected {len(EXPECTED_HEADER)} columns, got {len(values)}"
            )
            continue

        record = dict(zip(EXPECTED_HEADER, values))
        row_errors = []
        for field, value in record.items():
            if value != value.strip():
                row_errors.append(f"{field} has leading or trailing whitespace")
            if field != "parent_code" and not value:
                row_errors.append(f"{field} is empty")
        for field, limit in max_lengths.items():
            if len(record[field]) > limit:
                row_errors.append(f"{field} is longer than {limit} characters")
        if record["parent_code"] and record["parent_code"] == record["code"]:
            row_errors.append("account is its own parent")

        if row_errors:
            errors.extend(f"line {line}: {message}" for message in row_errors)
            continue

        if record["code"] in first_line_for_code:
            errors.append(
                f"line {line}: duplicate code {record['code']!r} "
                f"(first seen on line {first_line_for_code[record['code']]})"
            )
            continue
        first_line_for_code[record["code"]] = line
        rows.append(SourceAccount(line=line, **record))

    if not rows and not errors:
        errors.append("source file contains no accounts")

    by_code = {row.code: row for row in rows}
    for row in rows:
        if row.parent_code and row.parent_code not in by_code:
            errors.append(
                f"line {row.line}: parent_code {row.parent_code!r} is not an account in the source"
            )

    if not errors:
        for row in rows:
            seen = {row.code}
            parent = row.parent_code
            while parent:
                if parent in seen:
                    errors.append(f"line {row.line}: parent chain of {row.code!r} is circular")
                    break
                seen.add(parent)
                parent = by_code[parent].parent_code

    if errors:
        raise CommandError("Invalid chart of accounts source:\n  " + "\n  ".join(errors))

    return rows


class Command(BaseCommand):
    help = (
        "Import an official Chart of Accounts CSV into AccountChart, keyed by "
        "account code. Idempotent; never deletes accounts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=DEFAULT_SOURCE,
            help=f"CSV file to import (default: {DEFAULT_SOURCE})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change, then roll back without saving.",
        )

    def handle(self, *args, **options):
        from modules.accounts.infrastructure.persistence.models import AccountChart

        source: Path = options["source"]
        dry_run: bool = options["dry_run"]
        rows = read_source(source)

        created: list[str] = []
        updated: dict[str, list[str]] = {}

        with transaction.atomic():
            accounts: dict[str, AccountChart] = {}

            for row in rows:
                account = AccountChart.objects.filter(code=row.code).first()
                if account is None:
                    accounts[row.code] = AccountChart.objects.create(
                        code=row.code,
                        name=row.name,
                        external_account_type=row.external_account_type,
                        account_type=DEFAULT_ACCOUNT_TYPE,
                    )
                    created.append(row.code)
                    continue

                changed = [
                    field
                    for field in ("name", "external_account_type")
                    if getattr(account, field) != getattr(row, field)
                ]
                if changed:
                    for field in changed:
                        setattr(account, field, getattr(row, field))
                    account.save(update_fields=[*changed, "updated_at"])
                    updated[row.code] = changed
                accounts[row.code] = account

            # A blank parent_code states nothing, so an existing parent is kept.
            for row in rows:
                if not row.parent_code:
                    continue
                account = accounts[row.code]
                parent = accounts[row.parent_code]
                if account.parent_id != parent.id:
                    account.parent = parent
                    account.save(update_fields=["parent", "updated_at"])
                    if row.code not in created:
                        updated.setdefault(row.code, []).append("parent")

            if dry_run:
                transaction.set_rollback(True)

        unchanged = len(rows) - len(created) - len(updated)
        prefix = "[dry run - nothing saved] " if dry_run else ""

        self.stdout.write(f"{prefix}Source: {source} ({len(rows)} accounts)")
        for code in created:
            self.stdout.write(f"  created   {code}")
        for code, fields in updated.items():
            self.stdout.write(f"  updated   {code} ({', '.join(fields)})")
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}created: {len(created)}, updated: {len(updated)}, "
                f"unchanged: {unchanged}"
            )
        )
