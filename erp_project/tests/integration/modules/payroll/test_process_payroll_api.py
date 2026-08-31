"""
Regression test: processing payroll (POST /payroll/payslips/) must
actually work end to end.

Before this fix, running payroll was impossible for any of several
independent reasons, none of which had ever been exercised by a test:
- The view had no POST handler at all (405 for the "Run Payroll" button).
- PayrollService was never wired up - no Django repository existed for
  the domain Payroll aggregate, and IEmployeePayrollInfoProvider had no
  implementation.
- Payroll/Payslip/ExchangeRate/TaxTable/AllowanceType/DeductionType/
  EmployeeAllowance/EmployeeDeduction were all @dataclass subclasses of
  AggregateRoot/Entity, whose __init__(self, id) never runs because a
  dataclass generates its own __init__ - and `id` can't even be added as
  a dataclass field since it collides with the inherited read-only
  property. Every one of `Entity.create()`-style factories calling
  `cls(id=..., ...)` raised TypeError.
- EmployeeAllowance/EmployeeDeduction (HR module) were empty stub models
  with zero fields, so any allowance/deduction lookup raised FieldError.
- PayrollBatch.processed_by/closed_by were IntegerFields, but CustomUser's
  primary key is a UUID - saving one overflowed SQLite's INTEGER column
  (and would silently misbehave on Postgres too).
- Payroll.complete_processing() never transitioned status back to OPEN,
  so a period could only ever be processed once - re-running it (the
  expected way to pick up newly added employees) always 400'd.
- PayslipListSerializer expected gross_usd/gross_zig directly on the raw
  payslip row, which only ever had base_salary_usd/total_allowances_usd -
  listing any period with real payslips crashed with AttributeError.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status

from modules.payroll.infrastructure.persistence.models import DailyZiGRateToUSD, TaxBracket


@pytest.fixture
def usd_tax_bracket(db):
    return TaxBracket.objects.create(
        currency="USD", min_income=Decimal("0"), max_income=None,
        rate=Decimal("0.20"), deduction=Decimal("0"), active_from=date(2020, 1, 1),
    )


@pytest.fixture
def exchange_rate(db):
    return DailyZiGRateToUSD.objects.create(date=date.today(), average=Decimal("13.5"))


@pytest.mark.django_db
class TestProcessPayroll:
    def test_month_is_required(self, admin_client):
        response = admin_client.post("/api/v2/payroll/payslips/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_exchange_rate_does_not_strand_the_batch_in_processing(
        self, admin_client, sample_employee, usd_tax_bracket
    ):
        """
        Regression: a failed run used to leave the batch in PROCESSING
        forever (can_process only allows OPEN), permanently blocking every
        future attempt to process this period - discovered by triggering
        exactly this on the live deployment.
        """
        failed = admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert failed.status_code == status.HTTP_400_BAD_REQUEST
        assert "exchange rate" in failed.data["error"].lower()

        DailyZiGRateToUSD.objects.create(date=date.today(), average=Decimal("13.5"))
        retry = admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert retry.status_code == status.HTTP_201_CREATED, retry.data
        assert retry.data["total_processed"] == 1

    def test_process_payroll_generates_a_payslip_for_the_active_employee(
        self, admin_client, sample_employee, usd_tax_bracket, exchange_rate
    ):
        response = admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["total_processed"] == 1
        assert response.data["total_skipped"] == 0
        assert response.data["total_errors"] == 0

    def test_reprocessing_the_same_period_skips_already_processed_employees(
        self, admin_client, sample_employee, usd_tax_bracket, exchange_rate
    ):
        first = admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert first.data["total_processed"] == 1

        second = admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert second.status_code == status.HTTP_201_CREATED, second.data
        assert second.data["total_processed"] == 0
        assert second.data["total_skipped"] == 1

    def test_processed_payslips_are_listable_with_computed_gross_pay(
        self, admin_client, sample_employee, usd_tax_bracket, exchange_rate
    ):
        admin_client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")

        response = admin_client.get("/api/v2/payroll/payslips/", {"period": "2026-08"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        row = response.data[0]
        assert row["employee_name"] == "Farai Chuma"
        assert Decimal(row["gross_usd"]) == Decimal("2500.00")
        assert row["status"] == "Draft"
