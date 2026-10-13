"""
Management command: seed_evaluation.

The evaluation dataset for the isolated staging deployment (PLAN.md Day 4).
Staging uses only this data; it never restores production data.

Guards (checked before anything is written)
-------------------------------------------
- Runs only when ``ZCHPC_ENV=staging``, or when the Django setting
  ``SEED_EVALUATION_ALLOWED`` is true (tests).
- Runs only on a database that is empty (no employees) or already carries the
  evaluation marker. The marker is the one seed-eval.sh sets: on PostgreSQL
  the database comment ``zchpc-eval-seed``; on SQLite (laptops, tests) the
  file's ``application_id``. The command sets it itself after seeding.

Idempotent
----------
Everything is looked up by a natural key before it is created, and a row is
saved only when it differs from what the seed wants, so a rerun writes
nothing. Two kinds of data:
- Policy is reconciled on every run: the role grants below, the in-scope
  modules, departments and their heads, each seeded employee's department,
  position and role, the seeded logins' flags, the tax brackets and the
  exchange rate.
- Records an evaluator may change are created once and then left alone:
  salaries (a zero salary is still filled in), allowances, leave balances,
  leave requests and purchase requests.

Passwords
---------
New logins get no usable password, and existing passwords are never touched.
seed-eval.sh sets a generated password for each login afterwards and writes
them only to credentials.txt (A-8). Nothing here prints a password.

Purchase requests are driven through the application's own use cases, each
step by the actor whose role holds that stage (requester, the department's
recorded head, Accounts, GM, Director, Procurement), so their decisions and
notifications are what the real workflow would produce.
"""

import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from modules.procurement.application.authorization import PurchaseRequestPermissions as P

# =============================================================================
# ROLE GRANTS - the one place evaluation access is decided (PLAN §4a).
#
# Confirmed in writing (Fri 2026-10-09):
# - department heads see their own department's queues and no payroll; who
#   heads a department is Department.head, not the role name (INT-01 Q1, Q2)
# - HR runs payroll and holds payroll.* (A-10, A-11)
# - HR runs recruitment and holds recruitment.* (owner, 2026-10-12)
# - HR sees everyone's attendance and holds attendance.* (supervisor, 2026-10-13:
#   Attendance display fix only; the legacy role map already granted it)
# - procurement only processes (A-1)
# - GM and Director are real roles (A-1)
# - staff get self-service only: the portal and raising their own requests
# Every employee role can raise its own purchase request (self-service).
# A change here is an edit plus a reseed.
# =============================================================================
_SELF_SERVICE = ["portal.*", P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT]

ROLE_GRANTS: dict[str, list[str]] = {
    "ADMIN": ["*"],
    "HUMAN_RESOURCES": [
        *_SELF_SERVICE, "hr.*", "leave.*", "payroll.*", "recruitment.*", "attendance.*",
    ],
    "DEPARTMENT_MANAGER": [*_SELF_SERVICE, P.DEPARTMENT_HEAD_APPROVE, P.REJECT],
    "ACCOUNTANT": [*_SELF_SERVICE, P.ACCOUNTS_VERIFY, P.REJECT],
    "GENERAL_MANAGER": [*_SELF_SERVICE, P.GM_RECOMMEND, P.REJECT],
    "DIRECTOR": [*_SELF_SERVICE, P.DIRECTOR_APPROVE, P.REJECT],
    "PROCUREMENT_OFFICER": [*_SELF_SERVICE, P.PROCESS],
    "REGULAR_STAFF": list(_SELF_SERVICE),
}

ROLE_DISPLAY_NAMES = {
    "ADMIN": "System Administrator",
    "HUMAN_RESOURCES": "Human Resources",
    "DEPARTMENT_MANAGER": "Head of Department",
    "ACCOUNTANT": "Accountant",
    "GENERAL_MANAGER": "General Manager",
    "DIRECTOR": "Director",
    "PROCUREMENT_OFFICER": "Procurement Officer",
    "REGULAR_STAFF": "Staff",
}
# =============================================================================

MARKER = "zchpc-eval-seed"
# SQLite has no database comment; its header's application_id carries the
# marker instead ("ZEVS").
SQLITE_APPLICATION_ID = 0x5A455653

IN_SCOPE_MODULES = {
    "hr": "Human Resources",
    "payroll": "Payroll",
    "leave": "Leave Management",
    "procurement": "Procurement",
    "portal": "Employee Portal",
}

# name -> description. "IT" is the name seed_admin already uses.
DEPARTMENTS = {
    "IT": "Information Technology: ERP, networks and end-user support.",
    "HPC Operations": "Operates the national high performance computing platform.",
    "Finance": "Accounts, budgets and financial reporting.",
    "Human Resources": "People, payroll and leave administration.",
    "Procurement": "Purchasing, suppliers and stores.",
    "Administration": "Executive office, transport and facilities.",
}
DEPARTMENT_NAMES = list(DEPARTMENTS)

EMAIL_DOMAIN = "eval.zchpc.test"  # reserved TLD: nothing is ever delivered


@dataclass(frozen=True)
class Person:
    key: str
    first_name: str
    surname: str
    department: str
    position: str
    role: str
    usd_salary: Decimal
    heads_department: bool = False
    email: str = ""

    @property
    def login_email(self) -> str:
        return self.email or f"{self.first_name}.{self.surname}@{EMAIL_DOMAIN}".lower()


def _usd(amount: str) -> Decimal:
    return Decimal(amount)


PEOPLE = [
    # The eight evaluator logins, one per role.
    Person("admin", "System", "Administrator", "IT", "ERP System Administrator", "ADMIN",
           _usd("1500.00"), email="admin@zchpc.ac.zw"),
    Person("hr", "Rutendo", "Mlambo", "Human Resources", "Human Resources Officer",
           "HUMAN_RESOURCES", _usd("1100.00")),
    Person("hod", "Farai", "Chikwanha", "IT", "Head of IT", "DEPARTMENT_MANAGER",
           _usd("1800.00"), heads_department=True),
    Person("accountant", "Tatenda", "Mukarati", "Finance", "Accountant", "ACCOUNTANT",
           _usd("1200.00")),
    Person("gm", "Kudakwashe", "Nyathi", "Administration", "General Manager",
           "GENERAL_MANAGER", _usd("2600.00")),
    Person("director", "Tendai", "Moyo", "Administration", "Director", "DIRECTOR",
           _usd("3400.00")),
    Person("procurement", "Nyasha", "Chiweshe", "Procurement", "Procurement Officer",
           "PROCUREMENT_OFFICER", _usd("1000.00")),
    Person("staff", "Tinashe", "Dube", "IT", "Systems Engineer", "REGULAR_STAFF",
           _usd("950.00")),
    # The other department heads.
    Person("hpc_head", "Simbarashe", "Mutasa", "HPC Operations", "Head of HPC Operations",
           "DEPARTMENT_MANAGER", _usd("1900.00"), heads_department=True),
    Person("finance_head", "Chiedza", "Marufu", "Finance", "Finance Manager",
           "DEPARTMENT_MANAGER", _usd("1850.00"), heads_department=True),
    Person("hr_head", "Memory", "Sibanda", "Human Resources", "Human Resources Manager",
           "DEPARTMENT_MANAGER", _usd("1750.00"), heads_department=True),
    Person("procurement_head", "Blessing", "Zvobgo", "Procurement", "Procurement Manager",
           "DEPARTMENT_MANAGER", _usd("1700.00"), heads_department=True),
    Person("admin_head", "Tafadzwa", "Chirwa", "Administration", "Administration Manager",
           "DEPARTMENT_MANAGER", _usd("1650.00"), heads_department=True),
    # Staff.
    Person("rumbidzai", "Rumbidzai", "Gumbo", "HPC Operations", "HPC Systems Engineer",
           "REGULAR_STAFF", _usd("1050.00")),
    Person("munyaradzi", "Munyaradzi", "Hove", "HPC Operations", "HPC Systems Engineer",
           "REGULAR_STAFF", _usd("1000.00")),
    Person("tapiwa", "Tapiwa", "Ncube", "HPC Operations", "Data Centre Technician",
           "REGULAR_STAFF", _usd("780.00")),
    Person("takudzwa", "Takudzwa", "Shumba", "IT", "Network Technician", "REGULAR_STAFF",
           _usd("720.00")),
    Person("vimbai", "Vimbai", "Machingura", "Finance", "Accounts Clerk", "REGULAR_STAFF",
           _usd("680.00")),
    Person("ruvimbo", "Ruvimbo", "Katsande", "Human Resources", "HR Assistant",
           "REGULAR_STAFF", _usd("650.00")),
    Person("panashe", "Panashe", "Mapfumo", "Procurement", "Stores Clerk", "REGULAR_STAFF",
           _usd("620.00")),
]
PEOPLE_BY_KEY = {p.key: p for p in PEOPLE}

LOGIN_KEYS = ["admin", "hr", "hod", "accountant", "gm", "director", "procurement", "staff"]
LOGINS = {key: PEOPLE_BY_KEY[key].login_email for key in LOGIN_KEYS}
EMPLOYEE_EMAILS = [p.login_email for p in PEOPLE]

# (allowance type, taxable, person key, monthly USD)
ALLOWANCES = [
    ("Housing Allowance", True, "director", _usd("400.00")),
    ("Housing Allowance", True, "gm", _usd("300.00")),
    ("Transport Allowance", True, "hod", _usd("150.00")),
    ("Transport Allowance", True, "hpc_head", _usd("150.00")),
    ("Cellphone Allowance", True, "accountant", _usd("40.00")),
    ("Cellphone Allowance", True, "procurement", _usd("40.00")),
]

# ZIMRA USD monthly PAYE table: (min, max, rate, deduction). PAYE = income *
# rate - deduction. Figures are indicative until a payroll expert signs off (A-9).
TAX_TABLE_ACTIVE_FROM = date(2025, 1, 1)
USD_TAX_BRACKETS = [
    (_usd("0.00"), _usd("100.00"), Decimal("0.000"), _usd("0.00")),
    (_usd("100.01"), _usd("300.00"), Decimal("0.200"), _usd("20.00")),
    (_usd("300.01"), _usd("1000.00"), Decimal("0.250"), _usd("35.00")),
    (_usd("1000.01"), _usd("2000.00"), Decimal("0.300"), _usd("85.00")),
    (_usd("2000.01"), _usd("3000.00"), Decimal("0.350"), _usd("185.00")),
    (_usd("3000.01"), None, Decimal("0.400"), _usd("335.00")),
]

EXCHANGE_RATE_DATE = date(2026, 10, 1)
EXCHANGE_RATE_ZIG_PER_USD = Decimal("26.75000000")

# name -> (days per year, statutory)
LEAVE_TYPES = {
    "Annual Leave": (22, True),
    "Sick Leave": (90, True),
    "Compassionate Leave": (12, False),
    "Study Leave": (10, False),
}
LEAVE_TYPE_NAMES = list(LEAVE_TYPES)


@dataclass(frozen=True)
class Item:
    description: str
    quantity: int
    period: str
    cost: Decimal
    category: str


@dataclass(frozen=True)
class Scenario:
    """One purchase request, driven to ``state``. The first item names it."""

    requester: str
    state: str
    items: tuple[Item, ...]
    reason: str = ""
    po_number: str = ""


PR_SCENARIOS = [
    Scenario("staff", "DRAFT", (
        Item("Laptop docking stations for the ERP support desk", 3, "2 weeks",
             _usd("185.00"), "IT Hardware & Accessories"),
    )),
    Scenario("staff", "PENDING_DEPARTMENT_HEAD", (
        Item("Replacement UPS batteries for the server room", 8, "1 month",
             _usd("95.00"), "Equipment Maintenance & Repairs"),
    )),
    Scenario("rumbidzai", "PENDING_DEPARTMENT_HEAD", (
        Item("Air filters for the HPC cooling units", 12, "3 weeks",
             _usd("42.50"), "General Maintenance & Facilities"),
    )),
    Scenario("takudzwa", "PENDING_ACCOUNTS", (
        Item("Cat6 patch cables (3 m)", 50, "1 week", _usd("4.20"), "IT Hardware & Accessories"),
        Item("24-port managed network switch", 1, "1 month", _usd("640.00"),
             "IT Hardware & Accessories"),
    )),
    Scenario("staff", "PENDING_GM", (
        Item("Annual antivirus licence renewal (50 seats)", 1, "2 weeks",
             _usd("1250.00"), "IT Software & Subscriptions"),
    )),
    Scenario("vimbai", "PENDING_DIRECTOR", (
        Item("Printer toner cartridges for the Finance office", 6, "1 week",
             _usd("78.00"), "Office & Stationery Supplies"),
    )),
    Scenario("tapiwa", "PENDING_PROCUREMENT", (
        Item("Protective clothing for data centre technicians", 4, "2 weeks",
             _usd("65.00"), "Protective Clothing & Safety Equipment"),
    )),
    Scenario("staff", "PROCESSED", (
        Item("Mobile data bundles for field support", 5, "Immediate",
             _usd("30.00"), "Mobile Data & Airtime"),
    ), po_number="ZCHPC-PO-EVAL-0001"),
    Scenario("staff", "REJECTED", (
        Item("Ergonomic office chair", 1, "1 month", _usd("420.00"),
             "Office & Stationery Supplies"),
    ), reason="Over the office furniture budget this quarter; please request a standard chair."),
]


# ---------------------------------------------------------------------------
# The marker
# ---------------------------------------------------------------------------


def _quoted_database_name() -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        return connection.ops.quote_name(cursor.fetchone()[0])


def read_marker() -> str:
    """The evaluation marker this database carries, or ''."""
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(
                "SELECT coalesce(shobj_description(oid, 'pg_database'), '') "
                "FROM pg_database WHERE datname = current_database()"
            )
            return cursor.fetchone()[0]
        if connection.vendor == "sqlite":
            cursor.execute("PRAGMA application_id")
            return MARKER if cursor.fetchone()[0] == SQLITE_APPLICATION_ID else ""
    raise CommandError(f"seed_evaluation does not support the {connection.vendor} backend")


def write_marker() -> None:
    if read_marker() == MARKER:
        return
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(f"COMMENT ON DATABASE {_quoted_database_name()} IS '{MARKER}'")
        else:
            cursor.execute(f"PRAGMA application_id = {SQLITE_APPLICATION_ID}")


def clear_marker() -> None:
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            cursor.execute(f"COMMENT ON DATABASE {_quoted_database_name()} IS NULL")
        else:
            cursor.execute("PRAGMA application_id = 0")


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


def _first_monday_of_december(year: int) -> date:
    first = date(year, 12, 1)
    return first + timedelta(days=(7 - first.weekday()) % 7)


class Command(BaseCommand):
    help = (
        "Seed the evaluation dataset on staging. Refuses unless ZCHPC_ENV=staging "
        "and the database is empty or carries the evaluation marker. Idempotent."
    )

    def handle(self, *args, **options):
        self._guard()
        self.changes: list[str] = []

        with transaction.atomic():
            self._reference_data()
            roles = self._roles()
            self._modules()
            departments = self._departments()
            employees = {p.key: self._employee(p, departments, roles) for p in PEOPLE}
            self._department_heads(departments, employees)
            self._payroll(employees)
            leave_types = self._leave(employees)
            self._leave_requests(employees, leave_types)
            self._purchase_requests(employees)
            self._remove_test_job_postings()
            write_marker()

        self._report(employees)

    # -- guards ---------------------------------------------------------------

    def _guard(self) -> None:
        allowed = os.environ.get("ZCHPC_ENV") == "staging" or getattr(
            settings, "SEED_EVALUATION_ALLOWED", False
        )
        if not allowed:
            raise CommandError(
                "seed_evaluation runs only on staging (ZCHPC_ENV=staging); refusing."
            )

        from modules.hr.infrastructure.persistence.models import Employees

        if Employees.objects.exists() and read_marker() != MARKER:
            raise CommandError(
                f"The database has employees and no '{MARKER}' marker; refusing to seed "
                "a database the evaluation seed did not create."
            )

    # -- small helpers ------------------------------------------------------------

    def _note(self, message: str) -> None:
        self.changes.append(message)

    def _set_fields(self, obj, label: str, **wanted) -> None:
        """Save ``obj`` only when a field differs from what the seed wants."""
        changed = [name for name, value in wanted.items() if getattr(obj, name) != value]
        if changed:
            for name in changed:
                setattr(obj, name, wanted[name])
            obj.save(update_fields=changed)
            self._note(f"updated {label}: {', '.join(changed)}")

    # -- reference data -----------------------------------------------------------

    def _reference_data(self) -> None:
        """Assignable budget codes and PR categories; both commands are idempotent."""
        call_command("import_chart_of_accounts", stdout=StringIO())
        call_command("seed_purchase_request_categories", stdout=StringIO())

    def _roles(self) -> dict:
        from modules.hr.infrastructure.persistence.models import Role

        roles = {}
        for name, grants in ROLE_GRANTS.items():
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={
                    "display_name": ROLE_DISPLAY_NAMES[name],
                    "description": "Evaluation role; grants set by seed_evaluation.",
                    "permissions": list(grants),
                },
            )
            if created:
                self._note(f"created role {name}")
            else:
                self._set_fields(role, f"role {name}", permissions=list(grants))
            roles[name] = role
        return roles

    def _modules(self) -> None:
        from modules.identity.infrastructure.persistence.models import SystemModule

        for identifier, name in IN_SCOPE_MODULES.items():
            module, created = SystemModule.objects.get_or_create(
                identifier=identifier, defaults={"name": name, "is_active": True}
            )
            if created:
                self._note(f"created module {identifier}")
            else:
                self._set_fields(module, f"module {identifier}", is_active=True)

    def _departments(self) -> dict:
        from modules.hr.infrastructure.persistence.models import Department

        departments = {}
        for name, description in DEPARTMENTS.items():
            department, created = Department.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if created:
                self._note(f"created department {name}")
            departments[name] = department
        return departments

    def _position(self, title: str, department):
        from modules.hr.infrastructure.persistence.models import Position

        position, created = Position.objects.get_or_create(
            title=title, defaults={"department": department}
        )
        if created:
            self._note(f"created position {title}")
        else:
            self._set_fields(position, f"position {title}", department=department)
        return position

    # -- people -------------------------------------------------------------------

    def _employee(self, person: Person, departments: dict, roles: dict):
        from modules.hr.infrastructure.persistence.models import Employees

        department = departments[person.department]
        position = self._position(person.position, department)
        role = roles[person.role]

        employee = Employees.objects.select_related("user").filter(
            email=person.login_email
        ).first()
        created = employee is None
        if created:
            employee = self._create_employee(person, department, position, role)
        else:
            if (employee.first_name, employee.surname) != (person.first_name, person.surname):
                raise CommandError(
                    f"Refusing to touch {person.login_email}: expected {person.first_name} "
                    f"{person.surname}, found {employee.first_name} {employee.surname}."
                )
            fields = dict(department=department, position=position, role=role)
            if not employee.is_active:
                fields.update(lifecycle_status="ACTIVE", is_active=True)
            self._set_fields(employee, f"employee {person.login_email}", **fields)

        self._login(person, employee, created)
        return employee

    def _create_employee(self, person: Person, department, position, role):
        from modules.hr.application.services import CreateEmployeeCommand, EmployeeService
        from modules.hr.infrastructure.persistence.department_repository import (
            DjangoDepartmentRepository,
        )
        from modules.hr.infrastructure.persistence.employee_repository import (
            DjangoEmployeeRepository,
        )
        from modules.hr.infrastructure.persistence.models import Employees
        from modules.hr.infrastructure.persistence.position_repository import (
            DjangoPositionRepository,
        )
        from modules.identity.domain.value_objects import PermissionSet
        from shared.domain.exceptions import ValidationError

        service = EmployeeService(
            employee_repository=DjangoEmployeeRepository(),
            department_repository=DjangoDepartmentRepository(),
            position_repository=DjangoPositionRepository(),
        )
        index = PEOPLE.index(person)
        command = CreateEmployeeCommand(
            first_name=person.first_name,
            surname=person.surname,
            email=person.login_email,
            department_id=department.id,
            position_id=position.id,
            role_id=role.id,
            employee_type="Full-time",
            date_joined=date(2016 + index % 9, 1 + index % 12, 1),
            usd_salary=person.usd_salary,
            zig_salary=Decimal("0.00"),
            pay_frequency="Monthly",
            leave_days_entitled=LEAVE_TYPES["Annual Leave"][0],
        )
        try:
            # Operator-run seed, no request actor: full access, as
            # seed_pr_test_data and seed_test_employees do.
            entity = service.create_employee(command, actor_permissions=PermissionSet.full_access())
        except ValidationError as exc:
            raise CommandError(f"Could not create {person.login_email}: {exc.message}") from exc
        self._note(f"created employee {person.login_email}")
        return Employees.objects.select_related("user").get(pk=entity.id)

    def _login(self, person: Person, employee, created: bool) -> None:
        """A new login gets no usable password; flags are reconciled; an existing password is kept."""
        user = employee.user
        if user is None:
            raise CommandError(f"{person.login_email} has no login; the creation signal did not run.")

        privileged = person.role == "ADMIN"
        changed = []
        if created:
            # The creation signal issued a temporary password: drop it, so
            # only the password seed-eval.sh sets can open this login.
            user.set_unusable_password()
            changed.append("password")
        for name, value in (("is_active", True), ("must_change_password", False),
                            ("is_staff", privileged), ("is_superuser", privileged)):
            if getattr(user, name) != value:
                setattr(user, name, value)
                changed.append(name)
        if changed:
            user.save(update_fields=changed)
            self._note(f"updated login {person.login_email}: {', '.join(changed)}")

    def _department_heads(self, departments: dict, employees: dict) -> None:
        for person in PEOPLE:
            if person.heads_department:
                department = departments[person.department]
                self._set_fields(
                    department, f"department {department.name}", head=employees[person.key]
                )

    # -- payroll ------------------------------------------------------------------

    def _payroll(self, employees: dict) -> None:
        from modules.hr.infrastructure.persistence.models import AllowanceType, EmployeeAllowance
        from modules.payroll.infrastructure.persistence.models import (
            DailyZiGRateToUSD,
            PayrollProfile,
            TaxBracket,
        )

        for person in PEOPLE:
            profile, created = PayrollProfile.objects.get_or_create(
                employee=employees[person.key],
                defaults={"usd_salary": person.usd_salary, "pay_frequency": "Monthly"},
            )
            if created:
                self._note(f"created payroll profile {person.login_email}")
            elif not profile.usd_salary:
                self._set_fields(profile, f"salary {person.login_email}", usd_salary=person.usd_salary)

        for type_name, taxable, key, amount in ALLOWANCES:
            allowance_type, created = AllowanceType.objects.get_or_create(
                name=type_name, defaults={"is_taxable": taxable}
            )
            if created:
                self._note(f"created allowance type {type_name}")
            _, created = EmployeeAllowance.objects.get_or_create(
                employee=employees[key],
                allowance_type=allowance_type,
                defaults={"amount": amount, "currency": "USD"},
            )
            if created:
                self._note(f"created {type_name} for {PEOPLE_BY_KEY[key].login_email}")

        for low, high, rate, deduction in USD_TAX_BRACKETS:
            bracket, created = TaxBracket.objects.get_or_create(
                currency="USD",
                active_from=TAX_TABLE_ACTIVE_FROM,
                min_income=low,
                defaults={"max_income": high, "rate": rate, "deduction": deduction,
                          "provider": "ZIMRA"},
            )
            if created:
                self._note(f"created USD tax bracket from {low}")
            else:
                self._set_fields(bracket, f"USD tax bracket from {low}",
                                 max_income=high, rate=rate, deduction=deduction)

        rate, created = DailyZiGRateToUSD.objects.get_or_create(
            date=EXCHANGE_RATE_DATE, defaults={"average": EXCHANGE_RATE_ZIG_PER_USD}
        )
        if created:
            self._note(f"created exchange rate for {EXCHANGE_RATE_DATE}")
        else:
            self._set_fields(rate, "exchange rate", average=EXCHANGE_RATE_ZIG_PER_USD)

    # -- leave --------------------------------------------------------------------

    def _leave(self, employees: dict) -> dict:
        """Leave types through the ORM (avoids the LV-1 API bug) and this year's balances."""
        from modules.leave.infrastructure.persistence.models import LeaveBalance, LeaveType

        leave_types = {}
        for name, (days, statutory) in LEAVE_TYPES.items():
            leave_type, created = LeaveType.objects.get_or_create(
                name=name, defaults={"default_days_allowed": days, "is_statutory": statutory}
            )
            if created:
                self._note(f"created leave type {name}")
            leave_types[name] = leave_type

        year = date.today().year
        for person in PEOPLE:
            for leave_type in leave_types.values():
                _, created = LeaveBalance.objects.get_or_create(
                    employee=employees[person.key],
                    leave_type=leave_type,
                    year=year,
                    defaults={"days_remaining": Decimal(leave_type.default_days_allowed)},
                )
                if created:
                    self._note(f"created {leave_type.name} balance for {person.login_email}")
        return leave_types

    def _leave_requests(self, employees: dict, leave_types: dict) -> None:
        """Two pending requests: staff's (for HR to approve) and HR's own (HR cannot)."""
        from modules.leave.infrastructure.persistence.models import LeaveRequest

        monday = _first_monday_of_december(date.today().year)
        wanted = [
            ("staff", monday, monday + timedelta(days=4), "Family visit to Mutare"),
            ("hr", monday + timedelta(days=7), monday + timedelta(days=9),
             "Attending a graduation ceremony"),
        ]
        annual = leave_types["Annual Leave"]
        for key, start, end, reason in wanted:
            _, created = LeaveRequest.objects.get_or_create(
                employee=employees[key],
                leave_type=annual,
                start_date=start,
                defaults={"end_date": end, "reason": reason, "status": "Pending"},
            )
            if created:
                self._note(f"created leave request for {PEOPLE_BY_KEY[key].login_email}")

    # -- purchase requests ----------------------------------------------------------

    def _purchase_requests(self, employees: dict) -> None:
        from modules.procurement.infrastructure.persistence.models import PurchaseRequestItem

        for scenario in PR_SCENARIOS:
            requester = employees[scenario.requester]
            exists = PurchaseRequestItem.objects.filter(
                purchase_request__requester=requester,
                description=scenario.items[0].description,
            ).exists()
            if not exists:
                self._drive(scenario, requester, employees)
                self._note(f"created purchase request ({scenario.state}) for "
                           f"{PEOPLE_BY_KEY[scenario.requester].login_email}")

    def _drive(self, scenario: Scenario, requester, employees: dict) -> None:
        """Create the request and take it to its state, each step by the right actor."""
        from modules.procurement.application.authorization import (
            PurchaseRequestAuthorizationPolicy,
        )
        from modules.procurement.application.use_cases import (
            ApprovePurchaseRequestByDepartmentHead,
            ApprovePurchaseRequestByDirector,
            AssignItemBudgetCode,
            CreatePurchaseRequest,
            ProcessPurchaseRequestByProcurement,
            RecommendPurchaseRequestByGM,
            RejectPurchaseRequest,
            SubmitPurchaseRequest,
            VerifyPurchaseRequestByAccounts,
        )
        from modules.procurement.application.use_cases.purchase_request_use_cases import (
            CreatePurchaseRequestDTO,
            PurchaseRequestItemDTO,
        )
        from modules.procurement.infrastructure.persistence.django_budget_code_repository import (
            DjangoBudgetCodeRepository,
        )
        from modules.procurement.infrastructure.persistence.django_organizational_directory import (
            DjangoOrganizationalDirectory,
        )
        from modules.procurement.infrastructure.persistence.django_purchase_request_category_repository import (
            DjangoPurchaseRequestCategoryRepository,
        )
        from modules.procurement.infrastructure.persistence.django_purchase_request_repository import (
            DjangoPurchaseRequestRepository,
        )
        from modules.procurement.infrastructure.persistence.models import (
            PurchaseRequestCategory,
        )

        repository = DjangoPurchaseRequestRepository()
        policy = PurchaseRequestAuthorizationPolicy(directory=DjangoOrganizationalDirectory())
        budget_codes = DjangoBudgetCodeRepository()
        state = scenario.state

        dto = CreatePurchaseRequestDTO(
            requester_id=requester.pk,
            requester_name=f"{requester.first_name} {requester.surname}",
            department_id=requester.department_id,
            department_name=requester.department.name,
            designation=requester.position.title if requester.position else "",
            contact=requester.phone or requester.email,
            items=[
                PurchaseRequestItemDTO(
                    description=item.description,
                    quantity=item.quantity,
                    expected_delivery_period=item.period,
                    estimated_cost=item.cost,
                    category_id=PurchaseRequestCategory.objects.get(name=item.category).pk,
                )
                for item in scenario.items
            ],
        )
        request = CreatePurchaseRequest(
            repository, policy, DjangoPurchaseRequestCategoryRepository()
        ).execute(dto, self._actor(requester))
        if state == "DRAFT":
            return

        request_id = request.id
        SubmitPurchaseRequest(repository, policy).execute(request_id, self._actor(requester))
        if state == "PENDING_DEPARTMENT_HEAD":
            return

        head = requester.department.head
        if head is None:
            raise CommandError(f"{requester.department.name} has no head to act on its requests.")
        if state == "REJECTED":
            RejectPurchaseRequest(repository, policy).execute(
                request_id, self._actor(head), scenario.reason
            )
            return

        ApprovePurchaseRequestByDepartmentHead(repository, policy).execute(
            request_id, self._actor(head)
        )
        if state == "PENDING_ACCOUNTS":
            return

        accountant = self._actor(employees["accountant"])
        assignable = budget_codes.get_assignable()
        if not assignable:
            raise CommandError("No assignable budget codes; import_chart_of_accounts found none.")
        assign = AssignItemBudgetCode(repository, policy, budget_codes)
        for item in repository.get_by_id(request_id).items:
            assign.execute(request_id, item.id, assignable[0].id, accountant)
        VerifyPurchaseRequestByAccounts(repository, policy).execute(request_id, accountant)
        if state == "PENDING_GM":
            return

        RecommendPurchaseRequestByGM(repository, policy).execute(
            request_id, self._actor(employees["gm"])
        )
        if state == "PENDING_DIRECTOR":
            return

        ApprovePurchaseRequestByDirector(repository, policy).execute(
            request_id, self._actor(employees["director"])
        )
        if state == "PENDING_PROCUREMENT":
            return

        ProcessPurchaseRequestByProcurement(repository, policy).execute(
            request_id, self._actor(employees["procurement"]), scenario.po_number
        )

    @staticmethod
    def _actor(employee):
        """The Actor this employee's login would be (actor_from_request, without a request)."""
        from modules.identity.domain.value_objects import PermissionSet
        from modules.procurement.application.authorization import Actor

        employee.refresh_from_db(fields=["role", "department"])
        role = employee.role
        return Actor(
            employee_id=employee.pk,
            permissions=PermissionSet.from_list(list(role.permissions or [])),
            department_id=employee.department_id,
            role_name=role.name,
            user_id=employee.user_id,
            is_superuser=False,
        )

    # -- cleanup ----------------------------------------------------------------------

    def _remove_test_job_postings(self) -> None:
        """The interim seed's [TEST] jobs (seed_test_jobs) do not belong in an evaluation."""
        from modules.hr.infrastructure.persistence.models import Position
        from modules.recruitment.infrastructure.persistence.models import Job

        removed, _ = Job.objects.filter(title__startswith="[TEST]").delete()
        if removed:
            self._note("removed [TEST] job postings")
        Position.objects.filter(title__startswith="[TEST]", employees__isnull=True).delete()

    # -- report -----------------------------------------------------------------------

    def _report(self, employees: dict) -> None:
        if self.changes:
            for change in self.changes:
                self.stdout.write(f"  {change}")
        else:
            self.stdout.write("  nothing to change")
        self.stdout.write(self.style.SUCCESS("seed_evaluation complete. Logins (one per role):"))
        for key in LOGIN_KEYS:
            employee = employees[key]
            self.stdout.write(
                f"  {key:<12} {employee.employee_id:<8} {employee.email:<40} {employee.role.name}"
            )
