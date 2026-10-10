"""
PY-12: ZiG tax brackets were never found.

Currency.ZIG is "ZIG", but a TaxBracket stores the model's choice "ZiG"
(what synergy's Tax Tables screen saves), and every lookup filtered on the
exact string. So payroll fell back to the USD table for ZiG pay, the tax
table list filtered by ZIG came back empty, and the repository's own save
wrote "ZIG", which is not a valid choice.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.payroll.domain.entities.tax_table import TaxBracket as DomainBracket
from modules.payroll.domain.entities.tax_table import TaxTable
from modules.payroll.domain.value_objects import Currency
from modules.payroll.infrastructure.persistence.django_tax_repository import DjangoTaxTableRepository
from modules.payroll.infrastructure.persistence.models import TaxBracket

pytestmark = pytest.mark.django_db

User = get_user_model()

ACTIVE_FROM = date(2026, 1, 1)


def zig_bracket(**extra):
    values = dict(
        currency="ZiG", min_income=Decimal("0"), max_income=None,
        rate=Decimal("0.25"), deduction=Decimal("0"), active_from=ACTIVE_FROM,
    )
    values.update(extra)
    return TaxBracket.objects.create(**values)


def test_the_active_zig_table_is_found():
    zig_bracket()
    TaxBracket.objects.create(
        currency="USD", min_income=Decimal("0"), max_income=None,
        rate=Decimal("0.20"), deduction=Decimal("0"), active_from=ACTIVE_FROM,
    )

    table = DjangoTaxTableRepository().get_active_for_currency(Currency.ZIG, date(2026, 9, 1))

    assert table is not None
    assert table.currency == Currency.ZIG
    assert [b.rate for b in table.brackets] == [Decimal("0.25")]


def test_zig_brackets_as_tuples_are_found():
    zig_bracket()

    rows = DjangoTaxTableRepository().get_brackets_for_currency(Currency.ZIG, date(2026, 9, 1))

    assert len(rows) == 1


def test_saving_a_zig_table_stores_the_models_spelling_and_replaces_the_old_one():
    zig_bracket()
    table = TaxTable(
        id=None,
        currency=Currency.ZIG,
        effective_from=ACTIVE_FROM,
        brackets=[DomainBracket(
            min_income=Decimal("0"), max_income=None, rate=Decimal("0.30"),
            deduction=Decimal("0"), currency=Currency.ZIG,
        )],
        provider="",
        is_active=True,
    )

    DjangoTaxTableRepository().save(table)

    assert list(TaxBracket.objects.values_list("currency", "rate")) == [("ZiG", Decimal("0.3000"))]


@pytest.mark.parametrize("query", ["ZIG", "zig", "ZiG"])
def test_the_tax_bracket_list_filters_zig_whatever_the_case(query):
    zig_bracket()
    role = Role.objects.create(name="PY12_VIEWER", display_name="Viewer", permissions=["payroll.config.view"])
    user = User.objects.create_user(email="py12@zchpc.test", password="Pass12345!")
    Employees.objects.create(
        user=user, first_name="Vee", surname="Viewer", email="py12@zchpc.test",
        employee_id="EMP77001", role=role,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    response = client.get("/api/v2/payroll/tax-brackets/", {"currency": query})

    assert response.status_code == status.HTTP_200_OK, response.data
    rows = response.data["results"] if isinstance(response.data, dict) else response.data
    assert [r["currency"] for r in rows] == ["ZiG"]
