"""
REM-02: payroll object-level authorization.

Before this remediation any actor who passed RBACMiddleware's coarse "holds
anything in the payroll module" gate could read any employee's payslip, salary
profile, statutory numbers and bank accounts, write them, approve any payslip,
and change tax/exchange/allowance/deduction configuration. The same data was
also reachable, with even less protection, through the BFF employee profile,
the HR employee salary endpoints, HR employee update/create, and the HR
allowance/deduction endpoints.

Authentication styles follow REM-01/REM-05:

- Direct application-service calls (no HTTP): the boundary lives in the
  services, not only in the views, so a caller that bypasses middleware and
  views is still stopped.
- APIClient + real JWT through URL routing + RBACMiddleware + view + service.

Capability names come from PayrollPermissions. Role names in these tests are
arbitrary on purpose: what is proven is that only capabilities matter.
"""

import itertools
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from modules.hr.infrastructure.persistence.models import (
    AllowanceType,
    DeductionType,
    Employees,
    Role,
)
from modules.identity.domain.value_objects import PermissionSet
from modules.payroll.application.authorization import PayrollActor, PayrollPermissions as P
from modules.payroll.application.services import PayrollService, ProcessPayrollCommand
from modules.payroll.application.services.employee_payroll_data_service import (
    EmployeePayrollDataService,
)
from modules.payroll.application.services.payroll_configuration_service import (
    PayrollConfigurationService,
)
from modules.payroll.application.services.payslip_access_service import PayslipAccessService
from modules.payroll.domain.value_objects import PayrollPeriod
from modules.payroll.infrastructure.persistence.models import (
    DailyZiGRateToUSD,
    EmployeeBankAccount,
    Payroll,
    PayrollBatch,
    PayrollProfile,
    StatutoryProfile,
    TaxBracket,
)
from shared.domain.exceptions import AuthorizationError, NotFoundError

pytestmark = pytest.mark.django_db

User = get_user_model()

PERIOD = date(2026, 8, 1)


# ---------------------------------------------------------------- helpers


_employee_numbers = itertools.count(1)  # the domain requires EMP0001-style ids


def make_role(name, permissions):
    return Role.objects.create(name=name, display_name=name, permissions=permissions)


def make_employee(first, suffix, role=None):
    user = User.objects.create_user(email=f"{first.lower()}{suffix}@zchpc.test", password="Pass12345!")
    return Employees.objects.create(
        user=user,
        first_name=first,
        surname="Tester",
        email=f"{first.lower()}{suffix}@zchpc.test",
        employee_id=f"EMP{next(_employee_numbers):04d}",
        role=role,
    )


def jwt_client_for(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def client_with(*permissions, name="ARBITRARY_ROLE", suffix="A1"):
    """An authenticated employee whose role grants exactly these permissions."""
    role = make_role(f"{name}_{suffix}", list(permissions))
    employee = make_employee("Actor", suffix, role=role)
    return jwt_client_for(employee.user), employee


def make_payslip(employee, status_="Draft"):
    return Payroll.objects.create(
        employee=employee,
        period=PERIOD,
        base_salary_usd=Decimal("1000.00"),
        net_salary_usd=Decimal("800.00"),
        status=status_,
    )


@pytest.fixture
def victim():
    employee = make_employee("Victim", "V1")
    PayrollProfile.objects.create(employee=employee, usd_salary=Decimal("4321.00"), zig_salary=Decimal("99"))
    StatutoryProfile.objects.create(employee=employee, nssa_number="NSSA-SECRET", paye_number="PAYE-SECRET")
    EmployeeBankAccount.objects.create(employee=employee, bank_name="SecretBank", account_number="ACC-SECRET")
    return employee


@pytest.fixture
def victim_payslip(victim):
    return make_payslip(victim)


def payslip_url(payslip):
    return f"/api/v2/payroll/payslips/{payslip.id}/"


def approve_url(payslip):
    return f"/api/v2/payroll/payslips/{payslip.id}/approve/"


def profile_url(employee):
    return f"/api/v2/payroll/profiles/{employee.uuid}/"


def statutory_url(employee):
    return f"/api/v2/payroll/statutory/{employee.uuid}/"


def bank_url(employee):
    return f"/api/v2/payroll/bank-accounts/{employee.uuid}/"


def assert_denied(response):
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


def assert_no_disclosure(response, *secrets):
    body = response.content.decode()
    for secret in secrets:
        assert secret not in body


# ---------------------------------------------------------------- unauthenticated


class TestUnauthenticated:
    @pytest.mark.parametrize(
        "method, url",
        [
            ("get", "/api/v2/payroll/payslips/?period=2026-08"),
            ("get", "/api/v2/payroll/summary/?period=2026-08"),
            ("post", "/api/v2/payroll/tax-brackets/"),
            ("get", "/api/v2/hr/deductions/"),
            ("get", "/api/v2/bff/employees/00000000-0000-0000-0000-000000000000/"),
        ],
    )
    def test_no_credentials_is_401(self, method, url):
        response = getattr(APIClient(), method)(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_service_layer_rejects_anonymous_actor(self, victim, victim_payslip):
        anonymous = PayrollActor.anonymous()
        with pytest.raises(AuthorizationError) as exc:
            PayslipAccessService().get_payslip(anonymous, victim_payslip.id)
        assert exc.value.code == "UNAUTHENTICATED"
        with pytest.raises(AuthorizationError):
            EmployeePayrollDataService().get_payroll_profile(anonymous, victim.uuid)
        with pytest.raises(AuthorizationError):
            PayrollConfigurationService().list_tax_brackets(anonymous)


# ---------------------------------------------------------------- payslips


class TestPayslipDetailAndList:
    def test_actor_without_capability_cannot_read_another_employees_payslip(self, victim_payslip):
        client, _ = client_with(P.CONFIG_VIEW)
        response = client.get(payslip_url(victim_payslip))
        assert_denied(response)
        assert_no_disclosure(response, "1000", "800", "Victim")

    def test_capability_holder_can_read_payslip(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_VIEW)
        response = client.get(payslip_url(victim_payslip))
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["id"] == victim_payslip.id

    def test_unauthorized_actor_gets_same_answer_for_missing_and_existing_payslip(self, victim_payslip):
        client, _ = client_with(P.CONFIG_VIEW)
        existing = client.get(payslip_url(victim_payslip))
        missing = client.get("/api/v2/payroll/payslips/999999/")
        assert existing.status_code == missing.status_code == status.HTTP_403_FORBIDDEN

    def test_authorized_actor_gets_404_for_missing_payslip(self):
        client, _ = client_with(P.PAYSLIP_VIEW)
        assert client.get("/api/v2/payroll/payslips/999999/").status_code == status.HTTP_404_NOT_FOUND

    def test_payslip_list_is_denied_without_capability_and_returns_nothing(self, victim_payslip):
        client, _ = client_with(P.CONFIG_VIEW)
        response = client.get("/api/v2/payroll/payslips/?period=2026-08")
        assert_denied(response)
        assert_no_disclosure(response, "Victim")

    def test_payslip_list_returned_to_capability_holder(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_VIEW)
        response = client.get("/api/v2/payroll/payslips/?period=2026-08")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert len(response.data) == 1

    def test_service_filters_the_list_through_the_policy(self, victim, victim_payslip):
        """A narrowing policy loses records from the result, proving filtering is per record."""
        from modules.payroll.application.authorization import PayrollAuthorizationPolicy

        other = make_employee("Other", "O1")
        make_payslip(other)

        class NoVictim(PayrollAuthorizationPolicy):
            def _permits_target(self, actor, capability, target_employee_id):
                return target_employee_id != victim.id

        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.PAYSLIP_VIEW]))
        rows = PayslipAccessService(policy=NoVictim()).list_payslips(actor, 2026, 8)
        assert [r.employee_id for r in rows] == [other.id]


class TestPayslipApproval:
    def test_actor_without_approval_capability_cannot_approve_and_status_is_unchanged(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_VIEW, P.PAYSLIP_PROCESS, P.CONFIG_MANAGE)
        response = client.post(approve_url(victim_payslip))
        assert_denied(response)
        victim_payslip.refresh_from_db()
        assert victim_payslip.status == "Draft"

    def test_approval_capability_holder_can_approve(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_APPROVE)
        response = client.post(approve_url(victim_payslip))
        assert response.status_code == status.HTTP_200_OK, response.data
        victim_payslip.refresh_from_db()
        assert victim_payslip.status == "Processed"

    def test_approval_still_refuses_a_non_draft_payslip(self, victim):
        payslip = make_payslip(victim, status_="Paid")
        client, _ = client_with(P.PAYSLIP_APPROVE)
        response = client.post(approve_url(payslip))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_service_layer_denial_leaves_status_unchanged(self, victim_payslip):
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.PAYSLIP_VIEW]))
        with pytest.raises(AuthorizationError):
            PayslipAccessService().approve_payslip(actor, victim_payslip.id)
        victim_payslip.refresh_from_db()
        assert victim_payslip.status == "Draft"


class TestProcessPayrollBoundary:
    def test_actor_without_capability_cannot_run_payroll_via_api(self):
        client, _ = client_with(P.PAYSLIP_VIEW)
        response = client.post("/api/v2/payroll/payslips/", {"month": "2026-08"}, format="json")
        assert_denied(response)
        assert PayrollBatch.objects.count() == 0

    def test_service_denies_before_touching_any_repository(self):
        repos = {n: MagicMock() for n in (
            "payroll_repository", "payslip_repository", "tax_repository",
            "exchange_rate_repository", "allowance_repository", "deduction_repository",
            "employee_provider",
        )}
        service = PayrollService(**repos)
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.PAYSLIP_VIEW]))

        with pytest.raises(AuthorizationError):
            service.process_payroll(
                ProcessPayrollCommand(period=PayrollPeriod.from_string("2026-08"), processed_by=1), actor
            )
        with pytest.raises(AuthorizationError):
            service.approve_payslip(1, actor)
        with pytest.raises(AuthorizationError):
            service.close_payroll(1, 1, actor)
        with pytest.raises(AuthorizationError):
            service.reopen_payroll(1, actor)
        with pytest.raises(AuthorizationError):
            service.mark_payslip_paid(1, actor)
        for repo in repos.values():
            assert repo.method_calls == []

    def test_a_capability_holder_passes_the_gate(self):
        repos = {n: MagicMock() for n in (
            "payroll_repository", "payslip_repository", "tax_repository",
            "exchange_rate_repository", "allowance_repository", "deduction_repository",
            "employee_provider",
        )}
        repos["payroll_repository"].get_by_period.return_value = None
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.PAYSLIP_PROCESS]))
        # Gets past authorization; any later failure is a business one, not authorization.
        try:
            PayrollService(**repos).process_payroll(
                ProcessPayrollCommand(period=PayrollPeriod.from_string("2026-08"), processed_by=1), actor
            )
        except AuthorizationError:
            pytest.fail("authorized actor was denied")
        except Exception:
            pass


# ---------------------------------------------------------------- profile / statutory / bank


class TestPayrollProfile:
    def test_read_is_denied_and_discloses_nothing(self, victim):
        client, _ = client_with(P.STATUTORY_VIEW, P.BANK_VIEW)
        response = client.get(profile_url(victim))
        assert_denied(response)
        assert_no_disclosure(response, "4321")

    def test_write_is_denied_and_does_not_persist(self, victim):
        client, _ = client_with(P.PROFILE_VIEW)
        response = client.put(profile_url(victim), {"usd_salary": "1.00"}, format="json")
        assert_denied(response)
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("4321.00")

    def test_view_capability_reads(self, victim):
        client, _ = client_with(P.PROFILE_VIEW)
        response = client.get(profile_url(victim))
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Decimal(response.data["usd_salary"]) == Decimal("4321.00")

    def test_manage_capability_writes(self, victim):
        client, _ = client_with(P.PROFILE_MANAGE)
        response = client.put(profile_url(victim), {"usd_salary": "5000.00"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("5000.00")

    def test_authorized_read_of_employee_with_no_profile_row_no_longer_errors_and_creates_nothing(self):
        bare = make_employee("Bare", "B1")
        client, _ = client_with(P.PROFILE_VIEW)
        response = client.get(profile_url(bare))
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Decimal(response.data["usd_salary"]) == Decimal("0")
        assert not PayrollProfile.objects.filter(employee=bare).exists()

    def test_unknown_employee_is_403_for_unauthorized_and_404_for_authorized(self):
        unknown = "/api/v2/payroll/profiles/11111111-1111-1111-1111-111111111111/"
        denied, _ = client_with(P.CONFIG_VIEW, suffix="A2")
        allowed, _ = client_with(P.PROFILE_VIEW, suffix="A3")
        assert denied.get(unknown).status_code == status.HTTP_403_FORBIDDEN
        assert allowed.get(unknown).status_code == status.HTTP_404_NOT_FOUND


class TestStatutoryProfile:
    def test_read_denied_discloses_nothing(self, victim):
        client, _ = client_with(P.PROFILE_VIEW, P.BANK_VIEW)
        response = client.get(statutory_url(victim))
        assert_denied(response)
        assert_no_disclosure(response, "NSSA-SECRET", "PAYE-SECRET")

    def test_write_denied_does_not_persist(self, victim):
        client, _ = client_with(P.STATUTORY_VIEW)
        response = client.put(statutory_url(victim), {"nssa_number": "HACKED"}, format="json")
        assert_denied(response)
        assert StatutoryProfile.objects.get(employee=victim).nssa_number == "NSSA-SECRET"

    def test_capabilities_allow_read_and_write(self, victim):
        reader, _ = client_with(P.STATUTORY_VIEW, suffix="R1")
        writer, _ = client_with(P.STATUTORY_MANAGE, suffix="W1")
        assert reader.get(statutory_url(victim)).data["nssa_number"] == "NSSA-SECRET"
        response = writer.put(statutory_url(victim), {"nssa_number": "NEW"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert StatutoryProfile.objects.get(employee=victim).nssa_number == "NEW"


class TestBankAccounts:
    def test_read_denied_discloses_nothing(self, victim):
        client, _ = client_with(P.PROFILE_VIEW, P.STATUTORY_VIEW)
        response = client.get(bank_url(victim))
        assert_denied(response)
        assert_no_disclosure(response, "ACC-SECRET", "SecretBank")

    def test_create_denied_does_not_persist(self, victim):
        client, _ = client_with(P.BANK_VIEW)
        response = client.post(
            bank_url(victim), {"bank_name": "Evil", "account_number": "666"}, format="json"
        )
        assert_denied(response)
        assert EmployeeBankAccount.objects.filter(employee=victim).count() == 1

    def test_capabilities_allow_read_and_create(self, victim):
        reader, _ = client_with(P.BANK_VIEW, suffix="R2")
        writer, _ = client_with(P.BANK_MANAGE, suffix="W2")
        assert len(reader.get(bank_url(victim)).data) == 1
        response = writer.post(
            bank_url(victim), {"bank_name": "Good", "account_number": "1"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert EmployeeBankAccount.objects.filter(employee=victim).count() == 2

    def test_service_layer_denies_and_persists_nothing(self, victim):
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.BANK_VIEW]))
        with pytest.raises(AuthorizationError):
            EmployeePayrollDataService().add_bank_account(
                actor, victim.uuid, {"bank_name": "x", "account_number": "1"}
            )
        assert EmployeeBankAccount.objects.filter(employee=victim).count() == 1

    def test_service_layer_reports_missing_employee_only_after_authorization(self):
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.BANK_VIEW]))
        with pytest.raises(NotFoundError):
            EmployeePayrollDataService().list_bank_accounts(actor, "11111111-1111-1111-1111-111111111111")


# ---------------------------------------------------------------- summary / configuration


class TestSummaryAndConfiguration:
    def test_summary_denied(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_VIEW)
        response = client.get("/api/v2/payroll/summary/?period=2026-08")
        assert_denied(response)

    def test_summary_allowed(self, victim_payslip):
        client, _ = client_with(P.SUMMARY_VIEW)
        response = client.get("/api/v2/payroll/summary/?period=2026-08")
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_tax_bracket_mutations_denied_and_do_not_persist(self):
        bracket = TaxBracket.objects.create(
            currency="USD", min_income=0, max_income=None, rate=Decimal("0.2"), deduction=0,
            active_from=date(2020, 1, 1),
        )
        client, _ = client_with(P.CONFIG_VIEW)
        body = {
            "currency": "USD", "min_income": "0", "rate": "0.9", "deduction": "0",
            "active_from": "2026-01-01",
        }
        assert_denied(client.post("/api/v2/payroll/tax-brackets/", body, format="json"))
        assert_denied(client.put(f"/api/v2/payroll/tax-brackets/{bracket.id}/", {"rate": "0.9"}, format="json"))
        assert_denied(client.delete(f"/api/v2/payroll/tax-brackets/{bracket.id}/"))
        assert TaxBracket.objects.count() == 1
        bracket.refresh_from_db()
        assert bracket.rate == Decimal("0.200")

    def test_tax_bracket_read_needs_view_capability(self):
        denied, _ = client_with(P.CONFIG_MANAGE, suffix="A4")
        # manage does not silently imply view in the policy; view is its own capability
        assert denied.get("/api/v2/payroll/tax-brackets/").status_code == status.HTTP_403_FORBIDDEN
        allowed, _ = client_with(P.CONFIG_VIEW, suffix="A5")
        assert allowed.get("/api/v2/payroll/tax-brackets/").status_code == status.HTTP_200_OK

    def test_config_manage_allows_tax_bracket_mutation(self):
        client, _ = client_with(P.CONFIG_MANAGE)
        body = {
            "currency": "USD", "min_income": "0", "rate": "0.2", "deduction": "0",
            "active_from": "2026-01-01",
        }
        response = client.post("/api/v2/payroll/tax-brackets/", body, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_exchange_rate_mutations_denied(self):
        rate = DailyZiGRateToUSD.objects.create(date=date(2026, 1, 1), average=Decimal("13"))
        client, _ = client_with(P.CONFIG_VIEW)
        assert_denied(client.post("/api/v2/payroll/rates/", {"date": "2026-02-02", "zigRate": "20"}, format="json"))
        assert_denied(client.delete(f"/api/v2/payroll/rates/{rate.id}/"))
        assert DailyZiGRateToUSD.objects.count() == 1

    def test_exchange_rate_reads_denied_without_view(self):
        client, _ = client_with(P.PAYSLIP_VIEW)
        assert_denied(client.get("/api/v2/payroll/rates/"))
        assert_denied(client.get("/api/v2/payroll/rates/latest/"))

    def test_payroll_allowance_and_deduction_types_denied(self):
        client, _ = client_with(P.PAYSLIP_VIEW)
        assert_denied(client.get("/api/v2/payroll/allowance-types/"))
        assert_denied(client.post("/api/v2/payroll/allowance-types/", {"name": "X"}, format="json"))
        assert_denied(client.get("/api/v2/payroll/deduction-types/"))
        assert_denied(client.post("/api/v2/payroll/deduction-types/", {"name": "X"}, format="json"))
        assert not AllowanceType.objects.filter(name="X").exists()
        assert not DeductionType.objects.filter(name="X").exists()

    def test_service_layer_configuration_denied(self):
        actor = PayrollActor.from_permissions(PermissionSet.from_list([P.CONFIG_VIEW]))
        with pytest.raises(AuthorizationError):
            PayrollConfigurationService().create_tax_bracket(
                actor,
                dict(currency="USD", min_income=Decimal("0"), rate=Decimal("0.1"),
                     deduction=Decimal("0"), active_from=date(2026, 1, 1)),
            )
        assert TaxBracket.objects.count() == 0


# ---------------------------------------------------------------- Slice E: alternate paths


class TestHrAllowanceAndDeductionEndpoints:
    def test_mutations_denied_and_do_not_persist(self):
        allowance = AllowanceType.objects.create(name="Housing")
        deduction = DeductionType.objects.create(name="Union")
        client, _ = client_with("hr.employee.view", P.CONFIG_VIEW)

        assert_denied(client.post("/api/v2/hr/deductions/", {"name": "New"}, format="json"))
        assert_denied(client.patch(f"/api/v2/hr/deductions/{deduction.id}/", {"name": "Changed"}, format="json"))
        assert_denied(client.delete(f"/api/v2/hr/deductions/{deduction.id}/"))
        assert_denied(client.post("/api/v2/hr/allowances/", {"name": "New"}, format="json"))
        assert_denied(client.delete(f"/api/v2/hr/allowances/{allowance.id}/"))

        assert not DeductionType.objects.filter(name="New").exists()
        assert not AllowanceType.objects.filter(name="New").exists()
        deduction.refresh_from_db()
        allowance.refresh_from_db()
        assert deduction.name == "Union" and deduction.is_active
        assert allowance.is_active

    def test_reads_denied_without_view_capability(self):
        client, _ = client_with("hr.employee.view")
        assert_denied(client.get("/api/v2/hr/deductions/"))
        assert_denied(client.get("/api/v2/hr/allowances/"))

    def test_capability_holder_can_use_them(self):
        client, _ = client_with("hr.employee.view", P.CONFIG_VIEW, P.CONFIG_MANAGE)
        created = client.post("/api/v2/hr/deductions/", {"name": "Pension"}, format="json")
        assert created.status_code == status.HTTP_201_CREATED, created.data
        assert client.get("/api/v2/hr/deductions/").status_code == status.HTTP_200_OK
        deleted = client.delete(f"/api/v2/hr/deductions/{created.data['id']}/")
        assert deleted.status_code == status.HTTP_204_NO_CONTENT


class TestHrSalaryEndpoint:
    def test_salary_read_denied_discloses_nothing(self, victim):
        client, _ = client_with("hr.employee.view", P.STATUTORY_VIEW)
        response = client.get(f"/api/v2/hr/employees/{victim.id}/salary/")
        assert_denied(response)
        assert_no_disclosure(response, "4321")

    def test_salary_read_allowed_with_profile_view(self, victim):
        client, _ = client_with("hr.employee.view", P.PROFILE_VIEW)
        response = client.get(f"/api/v2/hr/employees/{victim.id}/salary/")
        assert response.status_code == status.HTTP_200_OK, response.data


class TestHrEmployeeWritesToPayrollData:
    def test_update_with_salary_denied_and_not_persisted(self, victim):
        client, _ = client_with("hr.employee.view")
        response = client.patch(f"/api/v2/hr/employees/{victim.id}/", {"usd_salary": "1.00"}, format="json")
        assert_denied(response)
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("4321.00")

    def test_service_update_with_bank_and_statutory_denied_and_not_persisted(self, victim):
        """The HTTP serializer does not accept these fields, but the service does, so it is guarded itself."""
        from modules.hr.api.views.employee_views import get_employee_service
        from modules.hr.application.services import UpdateEmployeeCommand

        service = get_employee_service()
        only_profile = PermissionSet.from_list([P.PROFILE_MANAGE])
        for command in (
            UpdateEmployeeCommand(employee_id=victim.id, bank_name="Evil", bank_account="666"),
            UpdateEmployeeCommand(employee_id=victim.id, nssa_number="HACK"),
            UpdateEmployeeCommand(employee_id=victim.id, pension_fund="HACK"),
        ):
            with pytest.raises(AuthorizationError):
                service.update_employee(command, actor_permissions=only_profile)
        assert EmployeeBankAccount.objects.get(employee=victim).bank_name == "SecretBank"
        assert StatutoryProfile.objects.get(employee=victim).nssa_number == "NSSA-SECRET"

    def test_service_create_and_update_with_no_actor_permissions_fail_closed(self, victim):
        from modules.hr.api.views.employee_views import get_employee_service
        from modules.hr.application.services import CreateEmployeeCommand, UpdateEmployeeCommand

        service = get_employee_service()
        with pytest.raises(AuthorizationError):
            service.create_employee(CreateEmployeeCommand(first_name="A", surname="B", usd_salary=Decimal("1")))
        with pytest.raises(AuthorizationError):
            service.update_employee(
                UpdateEmployeeCommand(employee_id=victim.id, usd_salary=Decimal("1")),
                actor_permissions=PermissionSet.empty(),
            )
        with pytest.raises(AuthorizationError):
            service.get_employee_salary(victim.id, None)
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("4321.00")

    def test_update_without_payroll_fields_is_unaffected(self, victim):
        client, _ = client_with("hr.employee.view", suffix="U1")
        response = client.patch(f"/api/v2/hr/employees/{victim.id}/", {"first_name": "Renamed"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data

    def test_update_with_capabilities_persists(self, victim):
        client, _ = client_with("hr.employee.view", P.PROFILE_MANAGE, P.BANK_MANAGE, P.STATUTORY_MANAGE, suffix="U2")
        response = client.patch(
            f"/api/v2/hr/employees/{victim.id}/",
            {"usd_salary": "7000.00", "bank_name": "Good", "nssa_number": "N2"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("7000.00")

    def test_create_with_salary_denied_creates_nothing(self):
        # hr.employee.create (REM-01) so that the payroll check is what denies.
        client, _ = client_with("hr.employee.view", "hr.employee.create")
        before = Employees.objects.count()
        response = client.post(
            "/api/v2/hr/employees/",
            {"first_name": "New", "surname": "Hire", "email": "new.hire@zchpc.test", "usd_salary": "9999.00"},
            format="json",
        )
        assert_denied(response)
        assert Employees.objects.count() == before


class TestBffEmployeeProfile:
    def url(self, employee):
        return f"/api/v2/bff/employees/{employee.uuid}/"

    def test_read_redacts_payroll_sections_without_capability(self, victim):
        client, _ = client_with("bff.employee.view")
        response = client.get(self.url(victim))
        assert response.status_code == status.HTTP_200_OK, response.data
        assert_no_disclosure(response, "4321", "SecretBank", "ACC-SECRET", "NSSA-SECRET", "PAYE-SECRET")
        assert response.data["usd_salary"] is None
        assert response.data["bank_account"] is None
        assert response.data["nssa_number"] is None
        assert response.data["first_name"] == "Victim"

    def test_read_shows_only_the_sections_the_actor_may_view(self, victim):
        client, _ = client_with("bff.employee.view", P.PROFILE_VIEW)
        response = client.get(self.url(victim))
        assert Decimal(response.data["usd_salary"]) == Decimal("4321.00")
        assert response.data["bank_account"] is None
        assert response.data["nssa_number"] is None

    def test_write_denied_persists_nothing_including_hr_fields(self, victim):
        client, _ = client_with("bff.employee.view", P.PROFILE_VIEW)
        response = client.put(
            self.url(victim),
            {"first_name": "Hijacked", "usd_salary": "1.00", "bank_account": "666"},
            format="json",
        )
        assert_denied(response)
        victim.refresh_from_db()
        assert victim.first_name == "Victim"
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("4321.00")
        assert EmployeeBankAccount.objects.get(employee=victim).account_number == "ACC-SECRET"

    def test_write_with_capabilities_persists(self, victim):
        client, _ = client_with("bff.employee.view", P.PROFILE_MANAGE, P.BANK_MANAGE, P.PROFILE_VIEW, P.BANK_VIEW,
                                P.STATUTORY_VIEW)
        response = client.put(
            self.url(victim), {"usd_salary": "8000.00", "bank_account": "NEWACC"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert PayrollProfile.objects.get(employee=victim).usd_salary == Decimal("8000.00")
        assert EmployeeBankAccount.objects.get(employee=victim, is_primary=True).account_number == "NEWACC"

    def test_non_payroll_edit_needs_no_payroll_capability_and_creates_no_payroll_rows(self):
        bare = make_employee("Bare", "B2")
        client, _ = client_with("bff.employee.view", suffix="A9")
        response = client.put(self.url(bare), {"phone": "0777"}, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert not PayrollProfile.objects.filter(employee=bare).exists()
        assert not EmployeeBankAccount.objects.filter(employee=bare).exists()
        assert not StatutoryProfile.objects.filter(employee=bare).exists()


# ---------------------------------------------------------------- roles are not policy; superuser; wildcard


class TestRoleNamesAndSuperuser:
    def test_role_named_accountant_without_capabilities_is_denied(self, victim_payslip, victim):
        client, _ = client_with(P.CONFIG_VIEW, name="ACCOUNTANT")
        assert_denied(client.get(payslip_url(victim_payslip)))
        assert_denied(client.get(profile_url(victim)))
        assert_denied(client.get("/api/v2/payroll/summary/?period=2026-08"))

    def test_arbitrarily_named_role_with_capability_is_allowed(self, victim_payslip):
        client, _ = client_with(P.PAYSLIP_VIEW, name="ZZZ_NOT_A_KNOWN_ROLE")
        assert client.get(payslip_url(victim_payslip)).status_code == status.HTTP_200_OK

    def test_role_named_admin_without_capabilities_gets_no_bypass(self, victim_payslip):
        client, _ = client_with(P.CONFIG_VIEW, name="ADMIN")
        assert_denied(client.get(payslip_url(victim_payslip)))

    def test_existing_payroll_wildcard_still_grants_everything(self, victim, victim_payslip):
        client, _ = client_with("payroll.*")
        assert client.get(payslip_url(victim_payslip)).status_code == status.HTTP_200_OK
        assert client.get(profile_url(victim)).status_code == status.HTTP_200_OK
        assert client.post(approve_url(victim_payslip)).status_code == status.HTTP_200_OK

    def test_full_access_role_still_works(self, victim_payslip):
        client, _ = client_with("*")
        assert client.get(payslip_url(victim_payslip)).status_code == status.HTTP_200_OK

    def test_superuser_without_employee_profile_retains_access(self, victim, victim_payslip):
        superuser = User.objects.create_superuser(email="rem02.super@zchpc.test", password="x")
        client = jwt_client_for(superuser)
        assert client.get(payslip_url(victim_payslip)).status_code == status.HTTP_200_OK
        assert client.get(profile_url(victim)).status_code == status.HTTP_200_OK
        assert client.get(bank_url(victim)).status_code == status.HTTP_200_OK
        assert client.get(f"/api/v2/hr/employees/{victim.id}/salary/").status_code == status.HTTP_200_OK
        assert client.post(approve_url(victim_payslip)).status_code == status.HTTP_200_OK
        assert client.get("/api/v2/payroll/tax-brackets/").status_code == status.HTTP_200_OK
        assert client.get("/api/v2/hr/deductions/").status_code == status.HTTP_200_OK
        assert client.get(f"/api/v2/bff/employees/{victim.uuid}/").data["usd_salary"] is not None

    def test_actor_from_request_uses_shared_resolution(self, victim):
        from rest_framework.test import APIRequestFactory

        from modules.payroll.api.actors import payroll_actor_from_request

        superuser = User.objects.create_superuser(email="rem02.super2@zchpc.test", password="x")
        request = APIRequestFactory().get("/")
        request.user = superuser
        actor = payroll_actor_from_request(request)
        assert actor.is_superuser and actor.employee_id is None and actor.has_permission(P.PAYSLIP_APPROVE)

        request.user = victim.user
        actor = payroll_actor_from_request(request)
        assert actor.employee_id == victim.pk  # Employees.pk, the id payroll rows carry
        assert not actor.has_permission(P.PAYSLIP_VIEW)


# ---------------------------------------------------------------- other disclosure paths found in review


class TestHrEmployeeDetailRedactsPayrollFields:
    """GET /hr/employees/<id>/ embedded salary for any employee via EmployeeDTO."""

    def test_salary_is_redacted_without_profile_view(self, victim):
        client, _ = client_with("hr.employee.view")
        response = client.get(f"/api/v2/hr/employees/{victim.id}/")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["usd_salary"] is None
        assert response.data["zig_salary"] is None
        assert_no_disclosure(response, "4321")

    def test_salary_is_shown_with_profile_view(self, victim):
        client, _ = client_with("hr.employee.view", P.PROFILE_VIEW, suffix="A7")
        response = client.get(f"/api/v2/hr/employees/{victim.id}/")
        assert Decimal(response.data["usd_salary"]) == Decimal("4321.00")

    def test_service_dto_getters_redact_by_default(self, victim):
        from modules.hr.api.views.employee_views import get_employee_service

        service = get_employee_service()
        dto = service.get_employee(victim.id)
        assert (dto.usd_salary, dto.bank_account, dto.bank_name) == (None, None, None)
        allowed = service.get_employee(
            victim.id, PermissionSet.from_list([P.PROFILE_VIEW, P.BANK_VIEW])
        )
        assert allowed.usd_salary == Decimal("4321.00") and allowed.bank_account == "ACC-SECRET"
        bank_only = service.get_employee(victim.id, PermissionSet.from_list([P.BANK_VIEW]))
        assert bank_only.usd_salary is None and bank_only.bank_account == "ACC-SECRET"


class TestAdminDashboardPayrollAggregates:
    """The dashboard view is reached without the payroll route gate, so it enforces the policy itself."""

    def _dashboard(self, user):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from modules.identity.api.views.admin_views import AdminDashboardView

        request = APIRequestFactory().get("/api/v2/admin/dashboard/")
        force_authenticate(request, user=user)
        return AdminDashboardView.as_view()(request)

    def test_payroll_distribution_is_empty_without_summary_capability(self, victim_payslip):
        _, actor = client_with(P.PAYSLIP_VIEW, suffix="D1")
        response = self._dashboard(actor.user)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["charts"]["payroll_distribution"] == []

    def test_payroll_distribution_shown_with_summary_capability_and_to_superuser(self, victim_payslip):
        _, actor = client_with(P.SUMMARY_VIEW, suffix="D2")
        assert self._dashboard(actor.user).data["charts"]["payroll_distribution"] != []
        superuser = User.objects.create_superuser(email="rem02.dash@zchpc.test", password="x")
        assert self._dashboard(superuser).data["charts"]["payroll_distribution"] != []
