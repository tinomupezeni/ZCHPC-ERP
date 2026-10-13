"""
seed_evaluation: the evaluation dataset for staging (PLAN Day 4).

What the evaluator gets, checked through the real HTTP stack: every role's
login works (synergy by email, portal by EC number), and each role reaches
what its grants allow and is refused what they don't, through a real JWT so
RBACMiddleware is on the path. Then the dataset itself (every PR state, each
step taken by the right role), idempotency, and the guards.

Passwords: the command gives its logins no usable password (seed-eval.sh sets
generated ones afterwards, A-8), so these tests set one, exactly as that
script does, before logging in.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.test import APIClient

from modules.hr.infrastructure.persistence.models import (
    Department,
    EmployeeAllowance,
    Employees,
    Position,
    Role,
)
from modules.hr.management.commands import seed_evaluation as seed
from modules.identity.infrastructure.persistence.models import SystemModule
from modules.leave.infrastructure.persistence.models import (
    LeaveBalance,
    LeaveRequest,
    LeaveType,
)
from modules.payroll.infrastructure.persistence.models import (
    DailyZiGRateToUSD,
    PayrollProfile,
    TaxBracket,
)
from modules.procurement.infrastructure.persistence.models import (
    PurchaseRequest,
    PurchaseRequestDecision,
    PurchaseRequestItem,
)
from modules.recruitment.infrastructure.persistence.models import Job

pytestmark = pytest.mark.django_db

User = get_user_model()

PASSWORD = "Eval-Passw0rd-For-Tests"
LOGIN_URL = "/api/v2/auth/token/"
PORTAL_LOGIN_URL = "/api/v2/portal/auth/login/"
ME_ACCESS_URL = "/api/v2/auth/users/me/access/"
PR_URL = "/api/v2/procurement/requests/"
PAYSLIPS_URL = "/api/v2/payroll/payslips/?period=2026-10"
RECRUITMENT_JOBS_URL = "/api/v2/recruitment/jobs/"
ATTENDANCE_ALL_URL = "/api/v2/attendance/all/"
EMPLOYEES_URL = "/api/v2/hr/employees/"
LEAVE_PENDING_URL = "/api/v2/leave/requests/pending/"
PORTAL_DASHBOARD_URL = "/api/v2/portal/dashboard/"

ALL_STATES = {
    "DRAFT",
    "PENDING_DEPARTMENT_HEAD",
    "PENDING_ACCOUNTS",
    "PENDING_GM",
    "PENDING_DIRECTOR",
    "PENDING_PROCUREMENT",
    "PROCESSED",
    "REJECTED",
}

# The role that must have taken each PR decision.
STAGE_ROLE = {
    "DEPARTMENT_HEAD": "DEPARTMENT_MANAGER",
    "ACCOUNTS": "ACCOUNTANT",
    "GM": "GENERAL_MANAGER",
    "DIRECTOR": "DIRECTOR",
}


@pytest.fixture(autouse=True)
def fast_hashing_and_allowed(settings):
    """Cheap hashing for these tests only; the guard's test setting on."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.SEED_EVALUATION_ALLOWED = True


@pytest.fixture(autouse=True)
def no_marker():
    """The marker can outlive a test's transaction (SQLite pragma); start clean."""
    seed.clear_marker()
    yield
    seed.clear_marker()


@pytest.fixture
def seeded():
    call_command("seed_evaluation", stdout=_Sink())


class _Sink:
    def write(self, *_args, **_kwargs):
        pass

    def flush(self):
        pass


def login_employee(role_key):
    return Employees.objects.select_related("user", "role").get(email=seed.LOGINS[role_key])


def set_password(employee):
    employee.user.set_password(PASSWORD)
    employee.user.save(update_fields=["password"])


def client_for(role_key):
    """A client holding a JWT obtained through the real synergy login."""
    employee = login_employee(role_key)
    set_password(employee)
    response = APIClient().post(
        LOGIN_URL, {"email": employee.email, "password": PASSWORD}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def pr_in_state(state, department_name=None):
    queryset = PurchaseRequest.objects.filter(status=state)
    if department_name:
        queryset = queryset.filter(department__name=department_name)
    return queryset.order_by("id").first()


def queue(client, scope):
    return client.get(PR_URL, {"scope": scope})


# ---------------------------------------------------------------------------
# Logins
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("seeded")
class TestEveryRoleLogsIn:
    def test_one_login_per_role(self):
        assert set(seed.LOGINS) == {
            "admin", "hr", "hod", "accountant", "gm", "director", "procurement", "staff",
        }

    @pytest.mark.parametrize("role_key", sorted(seed.LOGINS))
    def test_synergy_login_by_email(self, role_key):
        client_for(role_key)  # asserts 200

    @pytest.mark.parametrize("role_key", sorted(seed.LOGINS))
    def test_portal_login_by_ec_number(self, role_key):
        employee = login_employee(role_key)
        set_password(employee)

        response = APIClient().post(
            PORTAL_LOGIN_URL,
            {"ec_number": employee.employee_id, "password": PASSWORD},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK, response.data

    @pytest.mark.parametrize("role_key", sorted(seed.LOGINS))
    def test_no_forced_password_change_and_portal_dashboard_loads(self, role_key):
        client = client_for(role_key)

        assert client.get(ME_ACCESS_URL).status_code == status.HTTP_200_OK
        assert client.get(PORTAL_DASHBOARD_URL).status_code == status.HTTP_200_OK

    def test_seeded_logins_have_no_usable_password_until_one_is_set(self):
        for email in seed.LOGINS.values():
            assert not User.objects.get(email=email).has_usable_password(), email


# ---------------------------------------------------------------------------
# Grants: what each role reaches, and what it is refused
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("seeded")
class TestRoleGrants:
    @pytest.mark.parametrize("role_key", sorted(seed.LOGINS))
    def test_me_access_reports_exactly_the_configured_grants(self, role_key):
        employee = login_employee(role_key)

        data = client_for(role_key).get(ME_ACCESS_URL).data

        assert data["role"] == employee.role.name
        assert sorted(data["permissions"]) == sorted(seed.ROLE_GRANTS[employee.role.name])

    def test_admin_reaches_everything(self):
        client = client_for("admin")

        for url in (PAYSLIPS_URL, EMPLOYEES_URL, LEAVE_PENDING_URL):
            assert client.get(url).status_code == status.HTTP_200_OK, url

    def test_hr_runs_payroll_hr_and_leave(self):
        client = client_for("hr")

        assert client.get(PAYSLIPS_URL).status_code == status.HTTP_200_OK
        assert client.get(EMPLOYEES_URL).status_code == status.HTTP_200_OK
        assert client.get(LEAVE_PENDING_URL).status_code == status.HTTP_200_OK
        assert "payroll.*" in client.get(ME_ACCESS_URL).data["permissions"]

    def test_hr_runs_recruitment(self):
        # Hand checks 2026-10-12: HR got 403 "Failed to load jobs" in synergy.
        assert client_for("hr").get(RECRUITMENT_JOBS_URL).status_code == status.HTTP_200_OK

    @pytest.mark.parametrize("role_key", ["staff", "hod", "accountant", "gm", "director", "procurement"])
    def test_only_hr_and_admin_reach_recruitment(self, role_key):
        response = client_for(role_key).get(RECRUITMENT_JOBS_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_hr_sees_all_attendance(self):
        # Hand checks 2026-10-12: synergy Attendance showed "0 records" for HR (403).
        assert client_for("hr").get(ATTENDANCE_ALL_URL).status_code == status.HTTP_200_OK

    @pytest.mark.parametrize("role_key", ["staff", "hod", "accountant", "gm", "director", "procurement"])
    def test_only_hr_and_admin_see_all_attendance(self, role_key):
        response = client_for(role_key).get(ATTENDANCE_ALL_URL)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_hod_sees_no_payroll(self):
        client = client_for("hod")

        assert client.get(PAYSLIPS_URL).status_code == status.HTTP_403_FORBIDDEN
        profile_url = f"/api/v2/payroll/profiles/{login_employee('staff').uuid}/"
        assert client.get(profile_url).status_code == status.HTTP_403_FORBIDDEN
        permissions = client.get(ME_ACCESS_URL).data["permissions"]
        assert not [p for p in permissions if p.startswith("payroll")]

    def test_hod_queue_holds_only_their_own_department(self):
        hod = login_employee("hod")
        own = pr_in_state("PENDING_DEPARTMENT_HEAD", hod.department.name)
        other = PurchaseRequest.objects.filter(status="PENDING_DEPARTMENT_HEAD").exclude(
            department=hod.department
        ).first()
        assert own is not None and other is not None, "seed needs both cases"

        response = queue(client_for("hod"), "pending-department-head")

        assert response.status_code == status.HTTP_200_OK
        ids = {row["id"] for row in response.data}
        assert own.id in ids
        assert other.id not in ids

    def test_hod_cannot_approve_another_departments_request(self):
        hod = login_employee("hod")
        other = PurchaseRequest.objects.filter(status="PENDING_DEPARTMENT_HEAD").exclude(
            department=hod.department
        ).first()

        response = client_for("hod").post(f"{PR_URL}{other.id}/department-head/approve/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        other.refresh_from_db()
        assert other.status == "PENDING_DEPARTMENT_HEAD"

    def test_hod_has_no_hr_or_leave_review(self):
        client = client_for("hod")

        assert client.get(EMPLOYEES_URL).status_code == status.HTTP_403_FORBIDDEN
        assert "leave.request.review" not in client.get(ME_ACCESS_URL).data["permissions"]

    @pytest.mark.parametrize(
        "role_key, own_scope, refused_scopes",
        [
            ("accountant", "pending-accounts",
             ["pending-department-head", "pending-gm", "pending-director", "pending-procurement"]),
            ("gm", "pending-gm",
             ["pending-department-head", "pending-accounts", "pending-director", "pending-procurement"]),
            ("director", "pending-director",
             ["pending-department-head", "pending-accounts", "pending-gm", "pending-procurement"]),
            ("procurement", "pending-procurement",
             ["pending-department-head", "pending-accounts", "pending-gm", "pending-director"]),
        ],
    )
    def test_each_office_sees_its_own_queue_only(self, role_key, own_scope, refused_scopes):
        client = client_for(role_key)

        response = queue(client, own_scope)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        for scope in refused_scopes:
            assert queue(client, scope).status_code == status.HTTP_403_FORBIDDEN, scope

    @pytest.mark.parametrize(
        "state, action",
        [
            ("PENDING_DEPARTMENT_HEAD", "department-head/approve/"),
            ("PENDING_ACCOUNTS", "accounts/verify/"),
            ("PENDING_GM", "gm/recommend/"),
            ("PENDING_DIRECTOR", "director/approve/"),
        ],
    )
    def test_procurement_cannot_approve_at_any_stage(self, state, action):
        request = pr_in_state(state)

        response = client_for("procurement").post(f"{PR_URL}{request.id}/{action}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        request.refresh_from_db()
        assert request.status == state

    def test_procurement_cannot_reject(self):
        request = pr_in_state("PENDING_PROCUREMENT")

        response = client_for("procurement").post(
            f"{PR_URL}{request.id}/reject/", {"reason": "No"}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("role_key", ["accountant", "gm", "director", "procurement"])
    def test_offices_hold_no_payroll_or_hr(self, role_key):
        client = client_for(role_key)

        assert client.get(PAYSLIPS_URL).status_code == status.HTTP_403_FORBIDDEN
        assert client.get(EMPLOYEES_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_staff_is_self_service_only(self):
        client = client_for("staff")

        mine = queue(client, "mine")
        assert mine.status_code == status.HTTP_200_OK
        assert len(mine.data) >= 1
        for scope in ("pending-department-head", "pending-accounts", "pending-gm",
                      "pending-director", "pending-procurement"):
            assert queue(client, scope).status_code == status.HTTP_403_FORBIDDEN, scope
        assert client.get(PAYSLIPS_URL).status_code == status.HTTP_403_FORBIDDEN
        assert client.get(EMPLOYEES_URL).status_code == status.HTTP_403_FORBIDDEN
        assert client.get(LEAVE_PENDING_URL).status_code == status.HTTP_403_FORBIDDEN

    def test_hr_cannot_approve_own_leave(self):
        hr = login_employee("hr")
        own = LeaveRequest.objects.filter(employee=hr, status="Pending").first()
        assert own is not None, "seed needs HR's own pending request"
        balance_before = LeaveBalance.objects.get(
            employee=hr, leave_type=own.leave_type, year=own.start_date.year
        ).days_remaining

        response = client_for("hr").post(
            f"/api/v2/leave/requests/{own.id}/review/", {"approved": True}, format="json"
        )

        assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)
        own.refresh_from_db()
        assert own.status == "Pending"
        assert LeaveBalance.objects.get(
            employee=hr, leave_type=own.leave_type, year=own.start_date.year
        ).days_remaining == balance_before

    def test_hr_can_approve_staff_leave_and_the_balance_drops(self):
        staff = login_employee("staff")
        pending = LeaveRequest.objects.filter(employee=staff, status="Pending").first()
        assert pending is not None, "seed needs a staff pending request"
        balance = LeaveBalance.objects.get(
            employee=staff, leave_type=pending.leave_type, year=pending.start_date.year
        )
        before = balance.days_remaining

        response = client_for("hr").post(
            f"/api/v2/leave/requests/{pending.id}/review/", {"approved": True}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        balance.refresh_from_db()
        assert balance.days_remaining == before - pending.number_of_days


# ---------------------------------------------------------------------------
# The dataset
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("seeded")
class TestDataset:
    def test_every_pr_state_exists(self):
        states = set(PurchaseRequest.objects.values_list("status", flat=True))

        assert ALL_STATES <= states

    def test_each_pr_decision_was_taken_by_the_right_role(self):
        decisions = PurchaseRequestDecision.objects.select_related(
            "actor__role", "purchase_request"
        )
        assert decisions.exists()

        for decision in decisions:
            assert decision.actor.role.name == STAGE_ROLE[decision.stage], decision
            assert decision.actor_id != decision.purchase_request.requester_id
            if decision.stage == "DEPARTMENT_HEAD":
                assert decision.purchase_request.department.head_id == decision.actor_id

    def test_processed_by_procurement_with_a_po_number(self):
        processed = PurchaseRequest.objects.filter(status="PROCESSED")

        assert processed.exists()
        for request in processed:
            assert request.processed_by.role.name == "PROCUREMENT_OFFICER"
            assert request.purchase_order_number

    def test_rejected_request_carries_a_reason(self):
        rejected = PurchaseRequestDecision.objects.filter(decision="REJECTED")

        assert rejected.exists()
        assert all(d.reason for d in rejected)

    def test_items_past_accounts_have_budget_codes(self):
        past_accounts = ["PENDING_GM", "PENDING_DIRECTOR", "PENDING_PROCUREMENT", "PROCESSED"]

        items = PurchaseRequestItem.objects.filter(purchase_request__status__in=past_accounts)

        assert items.exists()
        assert not items.filter(budget_code__isnull=True).exists()

    def test_requests_are_raised_by_staff_in_their_own_department(self):
        for request in PurchaseRequest.objects.select_related("requester"):
            assert request.department_id == request.requester.department_id

    def test_about_six_departments_each_with_a_head_in_it(self):
        departments = Department.objects.filter(name__in=seed.DEPARTMENT_NAMES)

        assert departments.count() == len(seed.DEPARTMENT_NAMES) >= 6
        for department in departments:
            assert department.head is not None, department.name
            assert department.head.department_id == department.id
            assert department.head.role.name == "DEPARTMENT_MANAGER"

    def test_hod_login_heads_the_staff_logins_department(self):
        hod, staff = login_employee("hod"), login_employee("staff")

        assert staff.department.head_id == hod.id

    def test_about_twenty_employees_every_one_with_a_salary_and_leave(self):
        employees = Employees.objects.filter(email__in=seed.EMPLOYEE_EMAILS)
        year_types = LeaveType.objects.filter(name__in=seed.LEAVE_TYPE_NAMES)

        assert employees.count() == len(seed.EMPLOYEE_EMAILS) >= 20
        for employee in employees:
            profile = PayrollProfile.objects.get(employee=employee)
            assert profile.usd_salary > 0, employee.email
            assert employee.employee_id.startswith("EMP")
            for leave_type in year_types:
                assert LeaveBalance.objects.filter(
                    employee=employee, leave_type=leave_type
                ).exists(), (employee.email, leave_type.name)

    def test_some_allowances(self):
        assert EmployeeAllowance.objects.filter(amount__gt=0).count() >= 3

    def test_usd_tax_brackets_and_one_exchange_rate(self):
        usd = TaxBracket.objects.filter(currency="USD")

        assert usd.count() >= 5
        assert usd.filter(max_income__isnull=True).count() == 1
        assert DailyZiGRateToUSD.objects.count() == 1
        assert DailyZiGRateToUSD.objects.get().average > Decimal("0")

    def test_in_scope_system_modules_are_active(self):
        for identifier in seed.IN_SCOPE_MODULES:
            assert SystemModule.objects.get(identifier=identifier).is_active, identifier

    def test_roles_hold_exactly_the_configured_grants(self):
        for name, grants in seed.ROLE_GRANTS.items():
            assert sorted(Role.objects.get(name=name).permissions) == sorted(grants), name

    def test_no_test_job_postings(self):
        assert not Job.objects.filter(title__startswith="[TEST]").exists()

    def test_the_database_is_marked(self):
        assert seed.read_marker() == seed.MARKER


# ---------------------------------------------------------------------------
# Idempotency and guards
# ---------------------------------------------------------------------------


SNAPSHOT_MODELS = [
    Department, Position, Role, Employees, User, EmployeeAllowance, PayrollProfile,
    TaxBracket, DailyZiGRateToUSD, LeaveType, LeaveBalance, LeaveRequest,
    PurchaseRequest, PurchaseRequestItem, PurchaseRequestDecision, SystemModule, Job,
]


def snapshot():
    return {
        model.__name__: [model_to_dict(row) | {"pk": row.pk} for row in model.objects.order_by("pk")]
        for model in SNAPSHOT_MODELS
    }


class TestIdempotencyAndGuards:
    def test_rerun_changes_nothing(self, seeded):
        before = snapshot()

        call_command("seed_evaluation", stdout=_Sink())

        assert snapshot() == before

    def test_rerun_brings_an_existing_roles_grants_up_to_date(self, seeded):
        # A grant change reaches an already seeded staging DB by rerunning
        # seed-eval.sh (which also rotates the eight passwords).
        hr_role = Role.objects.get(name="HUMAN_RESOURCES")
        hr_role.permissions = ["portal.*", "hr.*"]
        hr_role.save(update_fields=["permissions"])

        call_command("seed_evaluation", stdout=_Sink())

        hr_role.refresh_from_db()
        assert sorted(hr_role.permissions) == sorted(seed.ROLE_GRANTS["HUMAN_RESOURCES"])

    def test_refuses_a_non_empty_unmarked_database(self):
        Employees.objects.create(first_name="Real", surname="Person", email="real@zchpc.test")
        roles_before = list(Role.objects.order_by("pk").values())

        with pytest.raises(CommandError, match="marker"):
            call_command("seed_evaluation", stdout=_Sink())

        assert Employees.objects.count() == 1
        assert list(Role.objects.order_by("pk").values()) == roles_before
        assert seed.read_marker() != seed.MARKER

    def test_seeds_a_non_empty_database_that_carries_the_marker(self):
        Employees.objects.create(first_name="Earlier", surname="Seed", email="earlier@zchpc.test")
        seed.write_marker()

        call_command("seed_evaluation", stdout=_Sink())

        assert Employees.objects.filter(email__in=seed.EMPLOYEE_EMAILS).exists()

    def test_refuses_outside_staging(self, settings, monkeypatch):
        settings.SEED_EVALUATION_ALLOWED = False
        monkeypatch.setenv("ZCHPC_ENV", "production")

        with pytest.raises(CommandError, match="staging"):
            call_command("seed_evaluation", stdout=_Sink())

        assert not Employees.objects.exists()

    def test_runs_when_zchpc_env_is_staging(self, settings, monkeypatch):
        settings.SEED_EVALUATION_ALLOWED = False
        monkeypatch.setenv("ZCHPC_ENV", "staging")

        call_command("seed_evaluation", stdout=_Sink())

        assert Employees.objects.filter(email__in=seed.EMPLOYEE_EMAILS).exists()

    def test_removes_existing_test_job_postings(self):
        Job.objects.create(title="[TEST] QA Careers Page Verification Role")
        seed.write_marker()  # the interim seed's jobs are on a marked database

        call_command("seed_evaluation", stdout=_Sink())

        assert not Job.objects.filter(title__startswith="[TEST]").exists()
