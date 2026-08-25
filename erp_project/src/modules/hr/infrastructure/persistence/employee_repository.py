"""
Django repository implementation for Employee aggregate.
"""

from datetime import date
from decimal import Decimal

from django.db import transaction

from shared.domain.value_objects import Email, NationalId, PhoneNumber, EmployeeId

from modules.hr.application.interfaces import IEmployeeRepository
from modules.hr.domain.entities import Employee
from modules.hr.domain.value_objects import (
    BankAccount,
    EmergencyContact,
    EmploymentType,
    Gender,
    MaritalStatus,
    PayFrequency,
    Salary,
    StatutoryInfo,
)


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

    # select_related traverses the reverse OneToOne into EmploymentDetails and
    # its own department/position FKs in a single join; emergency_contacts is a
    # reverse FK (multiple rows possible) so it needs prefetch_related instead.
    _RELATED = ("role", "employment_details__department", "employment_details__position")

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Get employee by database ID."""
        try:
            db_employee = self.model.objects.select_related(
                *self._RELATED
            ).prefetch_related("emergency_contacts").get(id=employee_id)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_employee_id(self, employee_id: EmployeeId | str) -> Employee | None:
        """Get employee by employee number (EMP0001)."""
        emp_id_str = str(employee_id)
        try:
            db_employee = self.model.objects.select_related(
                *self._RELATED
            ).prefetch_related("emergency_contacts").get(employee_id=emp_id_str)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Employee | None:
        """Get employee by email address."""
        try:
            db_employee = self.model.objects.select_related(
                *self._RELATED
            ).prefetch_related("emergency_contacts").get(email__iexact=email)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_by_national_id(self, national_id: str) -> Employee | None:
        """Get employee by national ID."""
        try:
            db_employee = self.model.objects.select_related(
                *self._RELATED
            ).prefetch_related("emergency_contacts").get(national_id=national_id)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> list[Employee]:
        """Get all employees."""
        queryset = self.model.objects.select_related(
            *self._RELATED
        ).prefetch_related("emergency_contacts")
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_by_department(self, department_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees in a department."""
        queryset = self.model.objects.select_related(
            *self._RELATED
        ).prefetch_related("emergency_contacts").filter(
            employment_details__department_id=department_id
        )
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_by_position(self, position_id: int, include_inactive: bool = False) -> list[Employee]:
        """Get employees with a specific position."""
        queryset = self.model.objects.select_related(
            *self._RELATED
        ).prefetch_related("emergency_contacts").filter(
            employment_details__position_id=position_id
        )
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return [self._to_entity(e) for e in queryset]

    def get_max_employee_id(self) -> EmployeeId | None:
        """Get the highest employee ID number."""
        last_employee = self.model.objects.filter(
            employee_id__startswith="EMP"
        ).order_by("-employee_id").first()

        if not last_employee or not last_employee.employee_id:
            return None

        try:
            return EmployeeId(last_employee.employee_id)
        except ValueError:
            return None

    def exists_by_email(self, email: str) -> bool:
        """Check if an employee with the given email exists."""
        return self.model.objects.filter(email__iexact=email).exists()

    def exists_by_national_id(self, national_id: str) -> bool:
        """Check if an employee with the given national ID exists."""
        return self.model.objects.filter(national_id=national_id).exists()

    def exists_by_employee_id(self, employee_id: str) -> bool:
        """Check if an employee with the given employee ID (EC Number) exists."""
        return self.model.objects.filter(employee_id=employee_id).exists()

    def count(self, include_inactive: bool = False) -> int:
        """Count employees."""
        queryset = self.model.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset.count()

    @property
    def _employment_details_model(self):
        from modules.hr.infrastructure.persistence.models import EmploymentDetails
        return EmploymentDetails

    @property
    def _emergency_contact_model(self):
        from modules.hr.infrastructure.persistence.models import EmergencyContact as EmergencyContactModel
        return EmergencyContactModel

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
            role_id=employee.role_id,
            is_active=employee.is_active,
        )
        db_employee.save()
        # Update the entity with the generated ID (set _id, not id property)
        object.__setattr__(employee, "_id", db_employee.id)

        self._employment_details_model.objects.create(
            employee=db_employee,
            department_id=employee.department_id,
            position_id=employee.position_id,
            reports_to_id=employee.reports_to_id,
            date_joined=employee.date_joined,
            contract_from=employee.contract_from,
            contract_to=employee.contract_to,
            employee_type=employee.employee_type.value,
        )
        self._emergency_contact_model.objects.create(
            employee=db_employee,
            name=employee.emergency_contact.name,
            relationship=employee.emergency_contact.relationship,
            phone=employee.emergency_contact.number,
        )

    @transaction.atomic
    def update(self, employee: Employee) -> None:
        """Update an existing employee."""
        self.model.objects.filter(id=employee.id).update(
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
            role_id=employee.role_id,
            is_active=employee.is_active,
        )

        self._employment_details_model.objects.update_or_create(
            employee_id=employee.id,
            defaults={
                "department_id": employee.department_id,
                "position_id": employee.position_id,
                "reports_to_id": employee.reports_to_id,
                "date_joined": employee.date_joined,
                "contract_from": employee.contract_from,
                "contract_to": employee.contract_to,
                "employee_type": employee.employee_type.value,
            },
        )

        emergency_contact_model = self._emergency_contact_model
        emergency_contact = emergency_contact_model.objects.filter(employee_id=employee.id).first()
        if emergency_contact is None:
            emergency_contact_model.objects.create(
                employee_id=employee.id,
                name=employee.emergency_contact.name,
                relationship=employee.emergency_contact.relationship,
                phone=employee.emergency_contact.number,
            )
        else:
            emergency_contact.name = employee.emergency_contact.name
            emergency_contact.relationship = employee.emergency_contact.relationship
            emergency_contact.phone = employee.emergency_contact.number
            emergency_contact.save()

    @transaction.atomic
    def delete(self, employee_id: int) -> bool:
        """Hard delete an employee. Returns True if deleted."""
        deleted, _ = self.model.objects.filter(id=employee_id).delete()
        return deleted > 0

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

        # Reverse OneToOne descriptor raises RelatedObjectDoesNotExist (a subclass
        # of AttributeError) when absent, so getattr(..., None) is safe here.
        employment_details = getattr(db_employee, "employment_details", None)

        # Use .all() (not .first()) so a prefetch_related cache is reused instead
        # of triggering a fresh query per employee.
        emergency_contacts = list(db_employee.emergency_contacts.all())
        emergency_contact_row = emergency_contacts[0] if emergency_contacts else None

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
            department_id=employment_details.department_id if employment_details else None,
            position_id=employment_details.position_id if employment_details else None,
            role_id=db_employee.role_id,
            employee_type=EmploymentType.from_string(
                employment_details.employee_type if employment_details else "Full-time"
            ),
            reports_to_id=employment_details.reports_to_id if employment_details else None,
            date_joined=employment_details.date_joined if employment_details else None,
            contract_from=employment_details.contract_from if employment_details else None,
            contract_to=employment_details.contract_to if employment_details else None,
            is_active=db_employee.is_active,
            emergency_contact=EmergencyContact(
                name=emergency_contact_row.name if emergency_contact_row else "",
                number=emergency_contact_row.phone if emergency_contact_row else "",
                relationship=emergency_contact_row.relationship if emergency_contact_row else "",
            ),
        )
