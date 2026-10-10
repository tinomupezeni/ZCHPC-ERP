"""
PY-1: the portal payslip endpoints returned 500 for everyone.

DjangoPayrollProvider read fields the payslip model (payroll.Payroll) does
not have: it select_related("payroll") and read payroll.period_year /
period_month, and allowances_usd / allowances_zig. The model has a single
`period` date and total_allowances_*.

Now list, detail and the yearly summary return 200 with the right figures,
and an employee still sees only their own Processed/Paid payslips.

PY-2: each response has the shape the portal reads
(employee-portal/src/types/payslip.types.ts): PayslipsResponse,
PayslipDetail and PayslipYearSummary, with amounts as numbers.
"""

from datetime import date
from decimal import Decimal
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import Employees, Role
from modules.payroll.infrastructure.persistence.models import Payroll

pytestmark = pytest.mark.django_db

User = get_user_model()

LIST_URL = "/api/v2/portal/payslips/"
SUMMARY_URL = "/api/v2/portal/payslips/summary/"

_numbers = count(75001)


def detail_url(payslip_id):
    return f"/api/v2/portal/payslips/{payslip_id}/"


def make_employee(label, **extra):
    n = next(_numbers)
    email = f"{label.lower()}{n}@zchpc.test"
    user = User.objects.create_user(email=email, password="testpass123")
    role = Role.objects.create(name=f"PAYSLIP_{n}", display_name=label, permissions=["portal.*"])
    return Employees.objects.create(
        user=user, first_name=label, surname="Person", email=email, employee_id=f"EMP{n}", role=role,
        **extra,
    )


def make_payslip(employee, period, status_="Processed", **amounts):
    values = dict(
        base_salary_usd=Decimal("1000.00"),
        base_salary_zig=Decimal("26000.00"),
        total_allowances_usd=Decimal("200.00"),
        total_allowances_zig=Decimal("5200.00"),
        paye_usd=Decimal("120.00"),
        total_deductions_usd=Decimal("150.00"),
        net_salary_usd=Decimal("1050.00"),
        net_salary_zig=Decimal("27300.00"),
        exchange_rate=Decimal("26.0000"),
    )
    values.update(amounts)
    return Payroll.objects.create(employee=employee, period=period, status=status_, **values)


def client_for(employee):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(employee.user)}")
    return client


LIST_ITEM_KEYS = {
    "id", "period", "period_display", "month", "year", "status",
    "base_salary_usd", "net_salary_usd", "base_salary_zig", "net_salary_zig", "exchange_rate",
}
AMOUNT_KEYS = {"usd", "zig"}


def test_list_has_the_portal_shape_and_only_own_visible_payslips():
    me, other = make_employee("Mary"), make_employee("Other")
    september = make_payslip(me, date(2026, 9, 1))
    make_payslip(me, date(2025, 12, 1))
    make_payslip(me, date(2026, 8, 1), status_="Draft")
    make_payslip(other, date(2026, 9, 1))

    response = client_for(me).get(LIST_URL, {"year": 2026})

    assert response.status_code == status.HTTP_200_OK, response.data
    assert set(response.data) == {"payslips", "available_years", "current_year"}
    assert response.data["available_years"] == [2026, 2025]
    assert response.data["current_year"] == 2026
    [item] = response.data["payslips"]
    assert set(item) == LIST_ITEM_KEYS
    assert item["id"] == september.id
    assert (item["period"], item["period_display"], item["month"], item["year"]) == (
        "2026-09", "September 2026", 9, 2026,
    )
    assert item["net_salary_usd"] == 1050.0
    assert item["exchange_rate"] == 26.0


def test_list_without_a_year_returns_every_visible_payslip_newest_first():
    me = make_employee("Yara")
    make_payslip(me, date(2025, 12, 1))
    make_payslip(me, date(2026, 1, 1))

    response = client_for(me).get(LIST_URL)

    assert response.status_code == status.HTTP_200_OK, response.data
    assert [(p["year"], p["month"]) for p in response.data["payslips"]] == [(2026, 1), (2025, 12)]


def test_detail_has_the_portal_shape():
    from modules.hr.infrastructure.persistence.models import Department, Position

    department = Department.objects.create(name="Finance PY2")
    position = Position.objects.create(title="Analyst PY2", department=department)
    me = make_employee("Dina", department=department, position=position)
    payslip = make_payslip(
        me, date(2026, 9, 1), aids_levy_usd=Decimal("3.60"), nssa_employee_usd=Decimal("20.00"),
        notes="September run",
    )

    response = client_for(me).get(detail_url(payslip.id))

    assert response.status_code == status.HTTP_200_OK, response.data
    data = response.data
    assert (data["id"], data["period"], data["period_display"], data["month"], data["year"]) == (
        payslip.id, "2026-09", "September 2026", 9, 2026,
    )
    assert (data["employee_name"], data["employee_id"], data["department"], data["position"]) == (
        "Dina Person", me.employee_id, "Finance PY2", "Analyst PY2",
    )
    assert set(data["earnings"]) == {"base_salary", "allowances", "gross"}
    assert set(data["deductions"]) == {"paye", "aids_levy", "nssa_employee", "other_deductions", "total"}
    assert set(data["summary"]) == {"gross_salary", "total_deductions", "net_salary"}
    for group in ("earnings", "deductions", "summary"):
        for amount in data[group].values():
            assert set(amount) == AMOUNT_KEYS
    assert data["earnings"]["allowances"]["usd"] == 200.0
    # 150 total - 120 PAYE - 3.60 AIDS levy - 20 NSSA
    assert data["deductions"]["other_deductions"]["usd"] == 6.4
    assert data["summary"]["net_salary"]["usd"] == 1050.0
    assert data["exchange_rate"] == 26.0
    assert data["notes"] == "September run"
    assert data["created_at"]


def test_detail_of_someone_elses_or_a_draft_payslip_is_not_found():
    me, other = make_employee("Nia"), make_employee("Owen")
    others = make_payslip(other, date(2026, 9, 1))
    draft = make_payslip(me, date(2026, 8, 1), status_="Draft")

    assert client_for(me).get(detail_url(others.id)).status_code == status.HTTP_404_NOT_FOUND
    assert client_for(me).get(detail_url(draft.id)).status_code == status.HTTP_404_NOT_FOUND


def test_year_summary_has_the_portal_shape():
    me = make_employee("Sam")
    make_payslip(me, date(2026, 8, 1))
    make_payslip(me, date(2026, 9, 1))
    make_payslip(me, date(2025, 9, 1))

    response = client_for(me).get(SUMMARY_URL, {"year": 2026})

    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data == {
        "year": 2026,
        "total_gross_usd": 2400.0,
        "total_gross_zig": 62400.0,
        "total_deductions_usd": 300.0,
        "total_deductions_zig": 0.0,
        "total_net_usd": 2100.0,
        "total_net_zig": 54600.0,
        "payslip_count": 2,
    }


def test_year_summary_with_no_payslips_is_zero():
    response = client_for(make_employee("Zed")).get(SUMMARY_URL, {"year": 2026})

    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["payslip_count"] == 0
    assert response.data["total_net_usd"] == 0.0
