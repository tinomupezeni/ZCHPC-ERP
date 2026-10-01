"""
Management command to seed realistic employees for functionality testing.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

FIRST_NAMES = [
    "Tinotenda", "Rutendo", "Tapiwa", "Chiedza", "Farai", "Tanaka", "Nyasha",
    "Kudzai", "Tatenda", "Rumbidzai", "Munashe", "Tafadzwa", "Ropafadzo",
    "Simbarashe", "Vimbai", "Takudzwa", "Chipo", "Blessing", "Panashe",
    "Anesu", "Tawanda", "Rutendo", "Nomsa", "Tendai", "Fadzai", "Wadzanai",
    "Gamuchirai", "Prosper", "Praise", "Ngonidzashe",
]
LAST_NAMES = [
    "Moyo", "Ncube", "Sibanda", "Mutasa", "Chikwanha", "Muzenda", "Gwaze",
    "Mukamuri", "Chirwa", "Dube", "Chitiyo", "Marufu", "Mangwende",
    "Nyathi", "Chigumba", "Zvobgo", "Mapfumo", "Chirinda", "Gumbo", "Mhlanga",
]
DEPARTMENTS = [
    ("Systems Support", ["Systems Engineer", "Systems Technician", "Network Administrator"]),
    ("Human Resources", ["HR Officer", "HR Manager", "Recruitment Coordinator"]),
    ("Finance", ["Accountant", "Finance Manager", "Payroll Officer"]),
    ("Procurement", ["Procurement Officer", "Supply Chain Coordinator"]),
    ("Research", ["Research Scientist", "Research Assistant", "Lab Technician"]),
    ("Administration", ["Administrative Assistant", "Office Manager", "Receptionist"]),
]
LEAVE_TYPES = [
    ("Annual Leave", 21),
    ("Sick Leave", 14),
    ("Compassionate Leave", 5),
    ("Maternity Leave", 98),
    ("Paternity Leave", 10),
]
GENDERS = ["Male", "Female"]
MARITAL_STATUSES = ["Single", "Married", "Divorced"]
EMPLOYEE_TYPES = ["Full-time", "Full-time", "Full-time", "Part-time", "Contract"]
BANKS = ["CBZ", "Steward Bank", "NMB Bank", "ZB Bank", "Ecobank"]
PAY_FREQUENCIES = ["Monthly", "Monthly", "Monthly", "Weekly"]

EMPLOYEE_COUNT = 50
EMAIL_DOMAIN = "test.zchpc.ac.zw"


def _random_dob(rng: random.Random) -> date:
    """A random DOB that's always at least 18 (22-60 years old)."""
    age_days = rng.randint(22 * 365, 60 * 365)
    return date.today() - timedelta(days=age_days)


def _random_national_id(rng: random.Random, index: int) -> str:
    # Zimbabwe National ID format: XX-NNNNNN-L-NN (district-serial-checkletter-checkdigits).
    # The serial is index-based so it's unique per index even across re-runs.
    district = rng.randint(10, 99)
    serial = 100000 + index
    check_letter = rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    check_digits = rng.randint(10, 99)
    return f"{district}-{serial:06d}-{check_letter}-{check_digits}"


class Command(BaseCommand):
    help = f"Seed {EMPLOYEE_COUNT} realistic employees (with department/position/salary/banking/leave data) for functionality testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=EMPLOYEE_COUNT, help=f"How many employees to seed (default: {EMPLOYEE_COUNT})"
        )
        parser.add_argument("--seed", type=int, default=42, help="Random seed, for reproducible names/data (default: 42)")

    def handle(self, *args, **options):
        from modules.hr.application.services import CreateEmployeeCommand, EmployeeService
        from modules.hr.infrastructure.persistence.department_repository import DjangoDepartmentRepository
        from modules.hr.infrastructure.persistence.employee_repository import DjangoEmployeeRepository
        from modules.hr.infrastructure.persistence.position_repository import DjangoPositionRepository
        from modules.hr.infrastructure.persistence.models import Department, Position
        from modules.leave.infrastructure.persistence.models import LeaveType
        from shared.domain.exceptions import ValidationError

        count = options["count"]
        rng = random.Random(options["seed"])

        for name, default_days in LEAVE_TYPES:
            _, created = LeaveType.objects.get_or_create(
                name=name, defaults={"default_days_allowed": default_days}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created leave type: {name}"))

        service = EmployeeService(
            employee_repository=DjangoEmployeeRepository(),
            department_repository=DjangoDepartmentRepository(),
            position_repository=DjangoPositionRepository(),
        )

        # Ensure departments/positions exist.
        dept_positions = []  # [(department_id, position_id), ...]
        with transaction.atomic():
            for dept_name, position_titles in DEPARTMENTS:
                department, created = Department.objects.get_or_create(name=dept_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created department: {dept_name}"))
                for title in position_titles:
                    position, created = Position.objects.get_or_create(
                        title=title, defaults={"department": department}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created position: {title}"))
                    dept_positions.append((department.id, position.id))

        created_count = 0
        skipped_count = 0

        for i in range(1, count + 1):
            first_name = rng.choice(FIRST_NAMES)
            last_name = rng.choice(LAST_NAMES)
            email = f"testemployee{i:03d}@{EMAIL_DOMAIN}"
            department_id, position_id = rng.choice(dept_positions)

            command = CreateEmployeeCommand(
                first_name=first_name,
                surname=last_name,
                email=email,
                phone=f"077{rng.randint(1000000, 9999999)}",
                national_id=_random_national_id(rng, i),
                date_of_birth=_random_dob(rng),
                gender=rng.choice(GENDERS),
                marital_status=rng.choice(MARITAL_STATUSES),
                department_id=department_id,
                position_id=position_id,
                employee_type=rng.choice(EMPLOYEE_TYPES),
                date_joined=date.today() - timedelta(days=rng.randint(30, 1500)),
                leave_days_entitled=rng.choice([18, 21, 22, 24]),
                usd_salary=Decimal(rng.randrange(400, 3000, 50)),
                zig_salary=Decimal(rng.randrange(8000, 60000, 500)),
                pay_frequency=rng.choice(PAY_FREQUENCIES),
                bank_name=rng.choice(BANKS),
                bank_account=str(rng.randint(1000000000, 9999999999)),
                nssa_number=f"NSSA-{rng.randint(100000, 999999)}",
                pension_fund="NSSA",
                emergency_contact_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                emergency_contact_number=f"078{rng.randint(1000000, 9999999)}",
                emergency_contact_relationship=rng.choice(["Spouse", "Parent", "Sibling", "Friend"]),
            )

            try:
                service.create_employee(command)
                created_count += 1
            except ValidationError as exc:
                if exc.code in ("DUPLICATE_EMAIL", "DUPLICATE_NATIONAL_ID", "DUPLICATE_EMPLOYEE_ID"):
                    skipped_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"[{i}] {email}: {exc.message}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone - {created_count} employee(s) created, {skipped_count} skipped "
                f"(already existed). Safe to re-run (idempotent by email/national ID)."
            )
        )
