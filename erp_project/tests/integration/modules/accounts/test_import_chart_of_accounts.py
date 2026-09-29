"""
Tests for the import_chart_of_accounts management command and the committed
official ZCHPC Chart of Accounts.

The committed CSV is read here with csv.DictReader rather than the command's
own parser, so the import is checked against the file independently. A handful
of accounts are also pinned to the values in the Sage export, so an accidental
edit to the data file fails loudly.
"""

import csv
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from modules.accounts.infrastructure.persistence.models import AccountChart
from modules.accounts.management.commands.import_chart_of_accounts import (
    DEFAULT_SOURCE,
)

pytestmark = pytest.mark.django_db

OFFICIAL_ACCOUNT_COUNT = 103
HEADER = "code,name,external_account_type,parent_code\n"

# (code, name, external_account_type) exactly as in the Sage 200 Evolution export.
PINNED_OFFICIAL_ACCOUNTS = [
    ("10000/03/050", "Transfers - Without Binding Agreements", "Revenue"),
    ("10000/04/056", "Hosting Services", "Revenue"),
    ("10000/04/056/0002", "RAM (Gb)", "Revenue"),
    ("12000", "Loss on Exchange", "Other Income"),
    ("20000/01/101/010/300", "Stationery and Printing", "Other Expense"),
    ("20000/01/101/022/300", "Software Subscriptions", "Other Expense"),
    (
        "20000/01/101/050/301",
        "Monitoring, Evaluation and Due Dilligenc/Internal Resources",
        "Other Expense",
    ),
    ("20000/02/101/011/300", "Communication (Telephone and Internet)", "Other Expense"),
    ("4000", "Depreciation, Amortisation and ImpairmentExpense", "Other Expense"),
    ("40500", "Non Distributable Reserves", "Non Distributable Reserves"),
    ("58000", "Deferred Income Liability", "Other Non Current Liability"),
    ("65000", "Machinery and Equipoment @ Costs", "Property, Plant and Equipm"),
    ("80200", "ZW$, A/C 24299820025", "Cash and Cash Equivalents"),
    ("92000", "Vat Control", "Taxation Liability"),
    ("96000", "VAT Control", "Taxation Liability"),
    ("9993", "Stock Takeon Balance", "Other Current Liability"),
]

HOSTING_SERVICES_CHILDREN = {
    "10000/04/056/0001",
    "10000/04/056/0002",
    "10000/04/056/0003",
    "10000/04/056/0004",
}


def run_import(*args):
    out = StringIO()
    call_command("import_chart_of_accounts", *args, stdout=out)
    return out.getvalue()


def official_rows():
    with DEFAULT_SOURCE.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_source(tmp_path: Path, body: str, name="chart.csv") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8", newline="")
    return path


# =============================================================================
# The committed official chart
# =============================================================================


class TestOfficialChartImport:
    def test_committed_source_contains_all_official_accounts(self):
        rows = official_rows()

        assert len(rows) == OFFICIAL_ACCOUNT_COUNT
        assert len({row["code"] for row in rows}) == OFFICIAL_ACCOUNT_COUNT

    def test_complete_import_creates_every_official_account(self):
        output = run_import()

        assert AccountChart.objects.count() == OFFICIAL_ACCOUNT_COUNT
        assert "created: 103, updated: 0, unchanged: 0" in output

    def test_codes_names_and_types_match_the_source_exactly(self):
        run_import()

        stored = {
            a.code: (a.name, a.external_account_type)
            for a in AccountChart.objects.all()
        }
        expected = {
            row["code"]: (row["name"], row["external_account_type"])
            for row in official_rows()
        }
        assert stored == expected

    @pytest.mark.parametrize("code,name,external_type", PINNED_OFFICIAL_ACCOUNTS)
    def test_official_values_are_preserved_verbatim(self, code, name, external_type):
        run_import()

        account = AccountChart.objects.get(code=code)
        assert account.name == name
        assert account.external_account_type == external_type

    def test_account_type_is_the_technical_default_not_a_mapping(self):
        run_import()

        assert set(AccountChart.objects.values_list("account_type", flat=True)) == {
            "regular"
        }

    def test_only_explicit_parent_relationships_are_created(self):
        run_import()

        with_parent = AccountChart.objects.filter(parent__isnull=False)
        assert set(with_parent.values_list("code", flat=True)) == HOSTING_SERVICES_CHILDREN
        assert set(with_parent.values_list("parent__code", flat=True)) == {"10000/04/056"}
        assert AccountChart.objects.get(code="10000/04/056").parent is None

    def test_no_parent_accounts_are_invented(self):
        run_import()

        official_codes = {row["code"] for row in official_rows()}
        assert set(AccountChart.objects.values_list("code", flat=True)) == official_codes
        for implied in ("20000", "20000/01", "20000/01/101", "20000/01/101/022", "10000", "10000/04"):
            assert not AccountChart.objects.filter(code=implied).exists()
        assert AccountChart.objects.get(code="20000/01/101/022/300").parent is None


# =============================================================================
# Idempotency and update semantics
# =============================================================================


class TestIdempotency:
    def test_second_import_changes_nothing(self):
        run_import()
        before = {
            a.code: (a.pk, a.name, a.external_account_type, a.parent_id, a.updated_at)
            for a in AccountChart.objects.all()
        }

        output = run_import()

        after = {
            a.code: (a.pk, a.name, a.external_account_type, a.parent_id, a.updated_at)
            for a in AccountChart.objects.all()
        }
        assert after == before
        assert "created: 0, updated: 0, unchanged: 103" in output

    def test_existing_account_is_updated_only_in_source_fields(self):
        legacy_parent = AccountChart.objects.create(
            code="LEGACY-PARENT", name="Legacy parent", account_type="view"
        )
        AccountChart.objects.create(
            code="20000/01/101/022/300",
            name="Old name",
            external_account_type="",
            account_type="view",
            reconcile=True,
            parent=legacy_parent,
        )

        output = run_import()

        account = AccountChart.objects.get(code="20000/01/101/022/300")
        assert account.name == "Software Subscriptions"
        assert account.external_account_type == "Other Expense"
        # Not represented by the source, so untouched.
        assert account.account_type == "view"
        assert account.reconcile is True
        assert account.parent_id == legacy_parent.id
        assert "updated   20000/01/101/022/300 (name, external_account_type)" in output
        assert "created: 102, updated: 1, unchanged: 0" in output

    def test_explicit_parent_is_corrected_by_code(self):
        wrong_parent = AccountChart.objects.create(
            code="LEGACY-PARENT", name="Legacy parent", account_type="view"
        )
        AccountChart.objects.create(
            code="10000/04/056/0001",
            name="vCPU",
            external_account_type="Revenue",
            account_type="regular",
            parent=wrong_parent,
        )

        output = run_import()

        child = AccountChart.objects.get(code="10000/04/056/0001")
        assert child.parent.code == "10000/04/056"
        assert "updated   10000/04/056/0001 (parent)" in output

    def test_accounts_absent_from_the_source_are_never_deleted(self):
        AccountChart.objects.create(code="LEGACY-1", name="Legacy", account_type="regular")

        run_import()
        run_import()

        assert AccountChart.objects.filter(code="LEGACY-1").exists()
        assert AccountChart.objects.count() == OFFICIAL_ACCOUNT_COUNT + 1

    def test_dry_run_saves_nothing(self):
        output = run_import("--dry-run")

        assert AccountChart.objects.count() == 0
        assert "[dry run - nothing saved] created: 103, updated: 0, unchanged: 0" in output


# =============================================================================
# Source validation
# =============================================================================


class TestSourceValidation:
    def test_duplicate_code_is_rejected_and_nothing_is_written(self, tmp_path):
        source = write_source(
            tmp_path,
            HEADER
            + "1000,First,Revenue,\n"
            + "2000,Second,Revenue,\n"
            + "1000,Duplicate,Revenue,\n",
        )

        with pytest.raises(CommandError, match=r"line 4: duplicate code '1000' \(first seen on line 2\)"):
            run_import("--source", str(source))

        assert AccountChart.objects.count() == 0

    @pytest.mark.parametrize(
        "body,message",
        [
            ("", "Source file is empty"),
            (HEADER, "contains no accounts"),
            ("code,name,type,parent_code\n1000,Cash,Revenue,\n", "Unexpected header"),
            (HEADER + "1000,Cash,Revenue\n", "expected 4 columns, got 3"),
            (HEADER + "1000,Cash,Revenue,,extra\n", "expected 4 columns, got 5"),
            (HEADER + ",Cash,Revenue,\n", "code is empty"),
            (HEADER + "1000,,Revenue,\n", "name is empty"),
            (HEADER + "1000,Cash,,\n", "external_account_type is empty"),
            (HEADER + " 1000,Cash,Revenue,\n", "code has leading or trailing whitespace"),
            (HEADER + "1000,Cash ,Revenue,\n", "name has leading or trailing whitespace"),
            (HEADER + "1000,Cash,Revenue,\n\n", "blank line"),
            (HEADER + "1000,Cash,Revenue,9999\n", "parent_code '9999' is not an account in the source"),
            (HEADER + "1000,Cash,Revenue,1000\n", "account is its own parent"),
            (HEADER + "1000,A,Revenue,2000\n2000,B,Revenue,1000\n", "circular"),
            (HEADER + f"{'9' * 65},Cash,Revenue,\n", "code is longer than 64 characters"),
        ],
    )
    def test_malformed_source_is_rejected(self, tmp_path, body, message):
        source = write_source(tmp_path, body)

        with pytest.raises(CommandError, match=message):
            run_import("--source", str(source))

        assert AccountChart.objects.count() == 0

    def test_invalid_row_late_in_the_file_prevents_any_write(self, tmp_path):
        source = write_source(
            tmp_path, HEADER + "1000,Cash,Revenue,\n2000,Bank,Revenue,\n3000,,Revenue,\n"
        )

        with pytest.raises(CommandError, match="line 4: name is empty"):
            run_import("--source", str(source))

        assert AccountChart.objects.count() == 0

    def test_missing_source_file_is_rejected(self, tmp_path):
        with pytest.raises(CommandError, match="Source file not found"):
            run_import("--source", str(tmp_path / "missing.csv"))

    def test_non_utf8_source_is_rejected(self, tmp_path):
        path = tmp_path / "latin1.csv"
        path.write_bytes((HEADER + "1000,Caf\xe9,Revenue,\n").encode("latin-1"))

        with pytest.raises(CommandError, match="not valid UTF-8"):
            run_import("--source", str(path))
