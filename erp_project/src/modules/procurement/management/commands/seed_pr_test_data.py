"""
Management command: seed_pr_test_data.

LOCAL DEVELOPMENT / MANUAL TESTING ONLY. Do not run against a shared,
staging, or production database - it creates real, logged-in-able accounts
with a known, published password.

Why this exists
----------------
The Purchase Request workflow (Employee -> Department Head -> Accounts ->
General Manager -> Director -> Procurement) already has a correct set of test
actors defined - but only inside
``erp_project/tests/integration/modules/procurement/conftest.py``, wrapped in
pytest-django's per-test transaction, which is rolled back the moment each
test finishes. That's exactly right for automated tests and useless for
manually clicking through the workflow in a running dev server: there is
nothing left in the database to log in as once the test process exits.

This command creates the same six actors, with the same names, emails,
password, and capability sets as those fixtures, as real persisted rows, so
they survive between requests and can actually be used to log into the
Employee Portal (which authenticates by EC number/employee_id, not email -
see modules.portal.application.services.auth_service.authenticate).

Why dedicated roles, not the existing HR default roles
--------------------------------------------------------
modules.hr.signals.create_default_roles seeds ADMIN/HR/ACCOUNTANT/
PROCUREMENT/SALES/MANAGER/STAFF, and
modules.procurement.application.authorization.permissions
.DEFAULT_PURCHASE_REQUEST_ROLE_PERMISSIONS documents a suggested mapping onto
them. Both were deliberately *not* reused here: those role rows may already
be attached to real (or other-seeded) employees in this database, and
mutating their ``permissions`` would silently change what those unrelated
employees can do - exactly the kind of side effect this command must avoid.
Instead, each test actor gets its own dedicated Role (PR_TEST_*), owned
entirely by this command, carrying exactly the Purchase Request permissions
that stage needs and nothing else - mirroring conftest.py's own
``make_employee`` fixture, which does the same thing for the same reason.
General Manager and Director have no existing role at all to reuse anyway -
see permissions.py's own note that GENERAL_MANAGER/DIRECTOR "are absent
because no such role exists in the current role vocabulary".

Employee IDs (EC numbers) are never hard-coded. They're produced by the
same application service and ID generator real employee creation uses
(EmployeeService.create_employee -> SequentialEmployeeIdGenerator), so the
values depend on this database's existing employees and are only known once
the command has actually run - see the printed summary.

Idempotency
-----------
Each actor is identified by their fixed @example.com test email (unique on
Employees.email). Re-running: if an actor with that email already exists and
matches the expected name, its department/position/role/password/active
state are reconciled (not recreated); if a *different* employee somehow
already owns that email, the command fails loudly rather than touching it.
"""

from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.hr.application.services import CreateEmployeeCommand, EmployeeService
from modules.hr.infrastructure.persistence.department_repository import (
    DjangoDepartmentRepository,
)
from modules.hr.infrastructure.persistence.employee_repository import (
    DjangoEmployeeRepository,
)
from modules.hr.infrastructure.persistence.position_repository import (
    DjangoPositionRepository,
)
from modules.identity.domain.value_objects import PermissionSet
from modules.procurement.application.authorization import PurchaseRequestPermissions as P
from shared.domain.exceptions import ValidationError

TEST_PASSWORD = "testpass123"

# Search order: prefer whichever of these already exists in this database
# (see the module docstring on "IT" vs "IT Department" naming) rather than
# ever creating a second, competing IT department.
IT_DEPARTMENT_NAME_CANDIDATES = ("IT Department", "IT")
IT_DEPARTMENT_NAME_IF_CREATED = "IT Department"

ACTORS = [
    {
        "key": "requester",
        "label": "Requester",
        "first_name": "Riley",
        "surname": "Requester",
        "email": "riley.requester@example.com",
        "role_name": "PR_TEST_REQUESTER",
        "permissions": [P.CREATE, P.VIEW, P.SUBMIT, P.CORRECT, P.RESUBMIT],
        "position_title": "PR Test - Requester",
        "in_it_department": True,
        "is_department_head": False,
    },
    {
        "key": "department_head",
        "label": "Department Head",
        "first_name": "Hana",
        "surname": "Head",
        "email": "hana.head@example.com",
        "role_name": "PR_TEST_DEPARTMENT_HEAD",
        "permissions": [P.DEPARTMENT_HEAD_APPROVE, P.VIEW, P.REJECT],
        "position_title": "PR Test - Department Head",
        "in_it_department": True,
        "is_department_head": True,
    },
    {
        "key": "accounts",
        "label": "Accounts",
        "first_name": "Adam",
        "surname": "Accounts",
        "email": "adam.accounts@example.com",
        "role_name": "PR_TEST_ACCOUNTS",
        "permissions": [P.ACCOUNTS_VERIFY, P.VIEW, P.REJECT],
        "position_title": "PR Test - Accounts",
        "in_it_department": False,
        "is_department_head": False,
    },
    {
        "key": "general_manager",
        "label": "General Manager",
        "first_name": "Gina",
        "surname": "Manager",
        "email": "gina.manager@example.com",
        "role_name": "PR_TEST_GENERAL_MANAGER",
        "permissions": [P.GM_RECOMMEND, P.VIEW, P.REJECT],
        "position_title": "PR Test - General Manager",
        "in_it_department": False,
        "is_department_head": False,
    },
    {
        "key": "director",
        "label": "Director",
        "first_name": "Dana",
        "surname": "Director",
        "email": "dana.director@example.com",
        "role_name": "PR_TEST_DIRECTOR",
        "permissions": [P.DIRECTOR_APPROVE, P.VIEW, P.REJECT],
        "position_title": "PR Test - Director",
        "in_it_department": False,
        "is_department_head": False,
    },
    {
        "key": "procurement",
        "label": "Procurement Officer",
        "first_name": "Pat",
        "surname": "Procure",
        "email": "pat.procure@example.com",
        "role_name": "PR_TEST_PROCUREMENT",
        "permissions": [P.PROCESS, P.VIEW],
        "position_title": "PR Test - Procurement Officer",
        "in_it_department": False,
        "is_department_head": False,
    },
]


@dataclass
class ActorResult:
    """
    Models are imported lazily inside methods (avoiding AppRegistryNotReady
    at module load time, matching seed_admin.py/seed_test_employees.py's own
    convention), so these are typed ``Any`` rather than imported for real.
    """

    spec: dict
    employee: Any  # modules.hr.infrastructure.persistence.models.Employees
    user: Any  # CustomUser
    role: Any  # modules.hr.infrastructure.persistence.models.Role
    created: bool


class Command(BaseCommand):
    help = (
        "LOCAL DEVELOPMENT ONLY: seed the six real, persisted test accounts "
        "needed to manually exercise the full Purchase Request workflow "
        "(Requester -> Department Head -> Accounts -> General Manager -> "
        "Director -> Procurement). Idempotent - safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change, then roll back without saving.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        employee_repo = DjangoEmployeeRepository()
        service = EmployeeService(
            employee_repository=employee_repo,
            department_repository=DjangoDepartmentRepository(),
            position_repository=DjangoPositionRepository(),
        )

        with transaction.atomic():
            department, department_created = self._resolve_it_department()

            results: list[ActorResult] = []
            for spec in ACTORS:
                results.append(self._seed_actor(spec, department, service))

            previous_head_id = department.head_id
            self._assign_department_head(department, results)

            self._verify(results, department)

            if dry_run:
                transaction.set_rollback(True)

        self._report(results, department, department_created, previous_head_id, dry_run)

    # ------------------------------------------------------------------
    # Department resolution
    # ------------------------------------------------------------------

    def _resolve_it_department(self):
        """
        Reuse the existing IT department under either known naming
        convention (see module docstring) rather than ever creating a
        second, competing one.
        """
        from modules.hr.infrastructure.persistence.models import Department

        for name in IT_DEPARTMENT_NAME_CANDIDATES:
            dept = Department.objects.filter(name__iexact=name).first()
            if dept:
                return dept, False

        dept = Department.objects.create(
            name=IT_DEPARTMENT_NAME_IF_CREATED,
            description="Information Technology (created by seed_pr_test_data)",
        )
        return dept, True

    # ------------------------------------------------------------------
    # Per-actor seeding
    # ------------------------------------------------------------------

    def _ensure_role(self, spec: dict):
        from modules.hr.infrastructure.persistence.models import Role

        role, _ = Role.objects.get_or_create(
            name=spec["role_name"],
            defaults={
                "display_name": f"[PR Test] {spec['label']}",
                "description": (
                    f"Local development/test role created by seed_pr_test_data. "
                    f"Grants exactly the Purchase Request permissions the "
                    f"{spec['label']} stage needs - nothing more."
                ),
                "permissions": list(spec["permissions"]),
            },
        )
        if list(role.permissions or []) != list(spec["permissions"]):
            role.permissions = list(spec["permissions"])
            role.save(update_fields=["permissions"])
        return role

    def _ensure_position(self, spec: dict, department):
        """
        A Position is only created when there's a real department to attach
        it to - modules.hr.domain.entities.position.Position._validate()
        requires department_id unconditionally, so a "position with no
        department" isn't a thing this domain allows. Accounts/GM/Director/
        Procurement have no department requirement in this dataset (see
        DEPARTMENT SETUP in the task this command implements), so they're
        simply left without a Position rather than inventing one.
        """
        if department is None:
            return None

        from modules.hr.infrastructure.persistence.models import Position

        position, _ = Position.objects.get_or_create(
            title=spec["position_title"],
            defaults={
                "department": department,
                "description": f"Local test position for {spec['label']} (seed_pr_test_data).",
            },
        )
        if position.department_id != department.id:
            position.department = department
            position.save(update_fields=["department"])
        return position

    def _seed_actor(self, spec: dict, it_department, service: EmployeeService) -> ActorResult:
        from modules.hr.infrastructure.persistence.models import Employees

        role = self._ensure_role(spec)
        department = it_department if spec["in_it_department"] else None
        position = self._ensure_position(spec, department)

        existing = Employees.objects.filter(email=spec["email"]).select_related("user").first()

        if existing is not None:
            if existing.first_name != spec["first_name"] or existing.surname != spec["surname"]:
                raise CommandError(
                    f"Refusing to touch {spec['email']}: expected "
                    f"{spec['first_name']} {spec['surname']} (this command's "
                    f"{spec['label']} test actor) but found "
                    f"{existing.first_name} {existing.surname}. This looks like "
                    f"a conflicting, non-test account - not something "
                    f"seed_pr_test_data created."
                )
            employee = existing
            created = False

            changed_fields = []
            if employee.department_id != (department.id if department else None):
                employee.department = department
                changed_fields.append("department")
            if employee.position_id != (position.id if position else None):
                employee.position = position
                changed_fields.append("position")
            if employee.role_id != role.id:
                employee.role = role
                changed_fields.append("role")
            if not employee.is_active:
                employee.is_active = True
                changed_fields.append("is_active")
            if changed_fields:
                employee.save(update_fields=changed_fields)
        else:
            command = CreateEmployeeCommand(
                first_name=spec["first_name"],
                surname=spec["surname"],
                email=spec["email"],
                department_id=department.id if department else None,
                position_id=position.id if position else None,
                role_id=role.id,
                employee_type="Full-time",
            )
            try:
                entity = service.create_employee(command)
            except ValidationError as exc:
                raise CommandError(
                    f"Failed to create {spec['label']} ({spec['email']}): {exc.message}"
                ) from exc
            employee = Employees.objects.select_related("user").get(pk=entity.id)
            created = True

        user = employee.user
        if user is None:
            # The post_save signal (modules.hr.signals
            # .create_employee_user_account) should have created and linked
            # this automatically. If it didn't, something about that
            # mechanism has changed - fail rather than improvise a login
            # this command didn't actually verify.
            raise CommandError(
                f"{spec['label']} ({spec['email']}) has no linked user account - "
                f"the employee-creation signal did not run as expected."
            )

        user_changed_fields = []
        if not user.check_password(TEST_PASSWORD):
            user.set_password(TEST_PASSWORD)
            user_changed_fields.append("password")
        if user.is_superuser or user.is_staff:
            user.is_superuser = False
            user.is_staff = False
            user_changed_fields += ["is_superuser", "is_staff"]
        if not user.is_active:
            user.is_active = True
            user_changed_fields.append("is_active")
        if user_changed_fields:
            user.save(update_fields=user_changed_fields)

        return ActorResult(spec=spec, employee=employee, user=user, role=role, created=created)

    def _assign_department_head(self, department, results: list[ActorResult]) -> None:
        head_result = next(r for r in results if r.spec["is_department_head"])
        if department.head_id != head_result.employee.id:
            department.head = head_result.employee
            department.save(update_fields=["head"])

    # ------------------------------------------------------------------
    # Verification (uses the application's real permission system, not
    # role-name string comparison - see module docstring)
    # ------------------------------------------------------------------

    def _verify(self, results: list[ActorResult], department) -> None:
        problems: list[str] = []
        by_key = {r.spec["key"]: r for r in results}

        for r in results:
            label = r.spec["label"]
            if r.employee.user_id is None:
                problems.append(f"{label}: no linked user account")
            if not r.employee.employee_id:
                problems.append(f"{label}: no employee_id (EC number) assigned")
            if not r.user.check_password(TEST_PASSWORD):
                problems.append(f"{label}: password authentication does not work")
            if r.user.is_superuser or r.user.is_staff:
                problems.append(f"{label}: is a superuser/staff account (must not be)")

        def has_permission(key: str, permission: str) -> bool:
            result = by_key[key]
            return PermissionSet.from_list(list(result.role.permissions or [])).has_permission(
                permission
            )

        required_permissions = [
            ("requester", P.CREATE),
            ("requester", P.VIEW),
            ("requester", P.SUBMIT),
            ("requester", P.CORRECT),
            ("requester", P.RESUBMIT),
            ("department_head", P.DEPARTMENT_HEAD_APPROVE),
            ("department_head", P.VIEW),
            ("department_head", P.REJECT),
            ("accounts", P.ACCOUNTS_VERIFY),
            ("accounts", P.VIEW),
            ("accounts", P.REJECT),
            ("general_manager", P.GM_RECOMMEND),
            ("general_manager", P.VIEW),
            ("general_manager", P.REJECT),
            ("director", P.DIRECTOR_APPROVE),
            ("director", P.VIEW),
            ("director", P.REJECT),
            ("procurement", P.PROCESS),
            ("procurement", P.VIEW),
        ]
        for key, permission in required_permissions:
            if not has_permission(key, permission):
                problems.append(f"{by_key[key].spec['label']}: missing permission '{permission}'")

        department.refresh_from_db(fields=["head"])
        head_employee = by_key["department_head"].employee
        if department.head_id != head_employee.id:
            problems.append(
                f"{department.name}.head is not Hana Head's employee id "
                f"(expected {head_employee.id}, got {department.head_id})"
            )

        requester_department_id = by_key["requester"].employee.department_id
        if requester_department_id != head_employee.department_id:
            problems.append(
                "Requester and Department Head are not in the same department "
                f"(requester={requester_department_id}, "
                f"department_head={head_employee.department_id})"
            )

        if problems:
            raise CommandError(
                "seed_pr_test_data verification failed - nothing was saved:\n  "
                + "\n  ".join(problems)
            )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _report(self, results, department, department_created, previous_head_id, dry_run) -> None:
        prefix = "[dry run - nothing saved] " if dry_run else ""
        by_key = {r.spec["key"]: r for r in results}

        self.stdout.write(self.style.SUCCESS(f"\n{prefix}PR TEST DATA READY (LOCAL DEVELOPMENT ONLY)"))
        self.stdout.write("=" * 60)

        if department_created:
            self.stdout.write(f"Created department: {department.name!r} (none of the existing naming conventions matched)")
        else:
            self.stdout.write(f"Reusing existing department: {department.name!r} (id={department.id})")
        if previous_head_id not in (None, by_key["department_head"].employee.id):
            self.stdout.write(
                self.style.WARNING(
                    f"  NOTE: {department.name} previously had a different head "
                    f"(employee id {previous_head_id}) - reassigned to Hana Head."
                )
            )

        for r in results:
            status = "created" if r.created else "reconciled (already existed)"
            self.stdout.write(f"\n{r.spec['label']}: [{status}]")
            self.stdout.write(f"  Name:       {r.spec['first_name']} {r.spec['surname']}")
            self.stdout.write(f"  EC Number:  {r.employee.employee_id}")
            self.stdout.write(f"  Login:      {r.employee.employee_id}")
            self.stdout.write(f"  Password:   {TEST_PASSWORD}")
            self.stdout.write(f"  Email:      {r.spec['email']}")
            dept_name = department.name if r.spec["in_it_department"] else "(none)"
            self.stdout.write(f"  Department: {dept_name}")
            if r.spec["is_department_head"]:
                self.stdout.write(f"  Department Head: YES ({department.name}.head_id = {department.head_id})")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.WARNING(
                f"{prefix}These are LOCAL DEVELOPMENT / TEST credentials only "
                "(password 'testpass123' on every account). Do not use in any "
                "shared or production environment."
            )
        )
