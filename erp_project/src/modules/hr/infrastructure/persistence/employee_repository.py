"""
Django repository implementation for Employee aggregate.
"""

from datetime import date
from decimal import Decimal

from django.db import connection, transaction

from shared.domain.value_objects import Email, NationalId, PhoneNumber, EmployeeId

from modules.hr.application.interfaces import IEmployeeRepository
from modules.hr.domain.entities import Employee
from modules.hr.domain.value_objects import (
    BankAccount,
    EmergencyContact,
    EmployeeLifecycleStatus,
    EmploymentType,
    Gender,
    MaritalStatus,
    PayFrequency,
    Salary,
    StatutoryInfo,
)


# Advisory-lock key for EC number allocation (any constant unique to this use).
_EMPLOYEE_ID_ALLOCATION_LOCK = 2_026_020_005


class DjangoEmployeeRepository(IEmployeeRepository):
    """
    Django ORM implementation of IEmployeeRepository.

    Maps between Employee domain entity and Django's Employees model.
    """

    def __init__(self):
        """Initialize repository with lazy model import."""
        self._model = None

    @property
    def model(self):
        """Lazy import of Employees model to avoid circular imports."""
        if self._model is None:
            from modules.hr.infrastructure.persistence.models import Employees
            self._model = Employees
        return self._model

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Get employee by database ID."""
        try:
            db_employee = self.model.objects.select_related(
                "department", "position", "role"
            ).get(id=employee_id)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_id_for_update(self, employee_id: int) -> Employee | None:
        """
        Get employee by database ID, holding its row lock until the
        surrounding transaction ends. Must be called inside one.
        """
        db_employee = self.model.objects.select_for_update().filter(id=employee_id).first()
        return self._to_entity(db_employee) if db_employee else None

    def get_by_employee_id(self, employee_id: EmployeeId | str) -> Employee | None:
        """Get employee by employee number (EMP0001)."""
        emp_id_str = str(employee_id)
        try:
            db_employee = self.model.objects.select_related(
                "department", "position", "role"
            ).get(employee_id=emp_id_str)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Employee | None:
        """Get employee by email address."""
        try:
            db_employee = self.model.objects.select_related(
                "department", "position", "role"
            ).get(email__iexact=email)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_national_id(self, national_id: str) -> Employee | None:
        """Get employee by national ID."""
        try:
            db_employee = self.model.objects.select_related(
                "department", "position", "role"
            ).get(national_id=national_id)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> list[Employee]:
        """Get all employees."""
        queryset = self.model.objects.select_related(
            "department", "position", "role"
        )
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_by_department(self, department_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees in a department."""
        queryset = self.model.objects.select_related(
            "department", "position", "role"
        ).filter(department_id=department_id)
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_by_position(self, position_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees with a specific position."""
        queryset = self.model.objects.select_related(
            "department", "position", "role"
        ).filter(position_id=position_id)
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_max_employee_id(self) -> EmployeeId | None:
        """
        The highest EC number held by any employee, whatever their lifecycle
        state, compared by its number: as text "EMP9999" sorts after
        "EMP10000", which made the next number collide with an existing one.
        """
        numbers = [
            int(match.group(1))
            for value in self.model.objects.filter(employee_id__istartswith="EMP")
            .values_list("employee_id", flat=True)
            .iterator()
            if (match := EmployeeId.EMPLOYEE_ID_PATTERN.match(value))
        ]
        if not numbers:
            return None
        return EmployeeId.from_number(max(numbers))

    def lock_employee_id_allocation(self) -> None:
        """
        Serialize EC number allocation until the surrounding transaction
        ends, so two concurrent creations cannot both choose the same number
        (AUD-02). A PostgreSQL transaction-level advisory lock; on SQLite,
        used only for development and tests, writes are already serialized.
        """
        if connection.vendor != "postgresql":
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_EMPLOYEE_ID_ALLOCATION_LOCK])

    def exists_by_email(self, email: str) -> bool:
        """Check if an employee with the given email exists."""
        return self.model.objects.filter(email__iexact=email).exists()

    def exists_by_national_id(self, national_id: str) -> bool:
        """Check if an employee with the given national ID exists."""
        return self.model.objects.filter(national_id=national_id).exists()

    def exists_by_employee_id(self, employee_id: str) -> bool:
        """
        Check if an employee holds this EC number, ignoring case: the stored
        form is upper-case but the unique index is case-sensitive, so a
        legacy lower-case row must still count as holding it (AUD-02).
        """
        return self.model.objects.filter(employee_id__iexact=employee_id).exists()

    def count(self, include_inactive: bool = False) -> int:
        """Count employees."""
        queryset = self.model.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset.count()

    @transaction.atomic
    def add(self, employee: Employee) -> None:
        """Add a new employee."""
        db_employee = self.model(
            employee_id=str(employee.employee_id),
            user_id=employee.user_id,
            first_name=employee.first_name,
            surname=employee.surname,
            national_id=employee.national_id.value if employee.national_id else None,
            date_of_birth=employee.date_of_birth,
            gender=employee.gender.value if employee.gender else "",
            marital_status=employee.marital_status.value if employee.marital_status else "",
            email=employee.email.value if employee.email else "",
            phone=employee.phone.value if employee.phone else "",
            department_id=employee.department_id,
            position_id=employee.position_id,
            role_id=employee.role_id,
            employee_type=employee.employee_type.value,
            reports_to_id=employee.reports_to_id,
            date_joined=employee.date_joined,
            contract_from=employee.contract_from,
            contract_to=employee.contract_to,
            lifecycle_status=employee.lifecycle_status.value,
            is_active=employee.is_active,
            emergency_contact_name=employee.emergency_contact.name,
            emergency_contact_number=employee.emergency_contact.number,
            emergency_contact_relationship=employee.emergency_contact.relationship,
        )
        db_employee.save()
        # Update the entity with the generated ID (set _id, not id property)
        object.__setattr__(employee, "_id", db_employee.id)
        # The post_save signal provisions the login; relay its one-time
        # temporary password, if any, to the caller (REM-07).
        employee.temporary_password = getattr(db_employee, "temporary_password", None)

    @transaction.atomic
    def update(self, employee: Employee) -> None:
        """
        Update an existing employee.

        The EC number is not written: it is assigned once, on add, and never
        changes (AUD-02; the database refuses a change too).
        """
        self.model.objects.filter(id=employee.id).update(
            user_id=employee.user_id,
            first_name=employee.first_name,
            surname=employee.surname,
            national_id=employee.national_id.value if employee.national_id else None,
            date_of_birth=employee.date_of_birth,
            gender=employee.gender.value if employee.gender else "",
            marital_status=employee.marital_status.value if employee.marital_status else "",
            email=employee.email.value if employee.email else "",
            phone=employee.phone.value if employee.phone else "",
            department_id=employee.department_id,
            position_id=employee.position_id,
            role_id=employee.role_id,
            employee_type=employee.employee_type.value,
            reports_to_id=employee.reports_to_id,
            date_joined=employee.date_joined,
            contract_from=employee.contract_from,
            contract_to=employee.contract_to,
            lifecycle_status=employee.lifecycle_status.value,
            is_active=employee.is_active,
            emergency_contact_name=employee.emergency_contact.name,
            emergency_contact_number=employee.emergency_contact.number,
            emergency_contact_relationship=employee.emergency_contact.relationship,
        )

    def _to_entity(self, db_employee) -> Employee:
        """Convert Django model to domain entity."""
        # Build value objects
        national_id = None
        if db_employee.national_id:
            try:
                national_id = NationalId(db_employee.national_id)
            except ValueError:
                pass  # Invalid format, leave as None

        email = None
        if db_employee.email:
            try:
                email = Email(db_employee.email)
            except ValueError:
                pass

        phone = None
        if db_employee.phone:
            try:
                phone = PhoneNumber(db_employee.phone)
            except ValueError:
                pass

        gender = None
        if db_employee.gender:
            try:
                gender = Gender.from_string(db_employee.gender)
            except ValueError:
                pass

        marital_status = None
        if db_employee.marital_status:
            try:
                marital_status = MaritalStatus.from_string(db_employee.marital_status)
            except ValueError:
                pass

        return Employee(
            id=db_employee.id,
            employee_id=EmployeeId(db_employee.employee_id),
            user_id=db_employee.user_id,
            first_name=db_employee.first_name,
            surname=db_employee.surname,
            national_id=national_id,
            date_of_birth=db_employee.date_of_birth,
            gender=gender,
            marital_status=marital_status,
            email=email,
            phone=phone,
            department_id=db_employee.department_id,
            position_id=db_employee.position_id,
            role_id=db_employee.role_id,
            employee_type=EmploymentType.from_string(db_employee.employee_type),
            reports_to_id=db_employee.reports_to_id,
            date_joined=db_employee.date_joined,
            contract_from=db_employee.contract_from,
            contract_to=db_employee.contract_to,
            lifecycle_status=EmployeeLifecycleStatus.from_string(db_employee.lifecycle_status),
            emergency_contact=EmergencyContact(
                name=db_employee.emergency_contact_name or "",
                number=db_employee.emergency_contact_number or "",
                relationship=db_employee.emergency_contact_relationship or "",
            ),
        )
