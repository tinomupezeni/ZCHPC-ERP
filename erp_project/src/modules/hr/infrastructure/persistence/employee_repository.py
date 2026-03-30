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

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Get employee by database ID."""
        try:
            db_employee = self.model.objects.select_related(
                "department", "position", "role"
            ).get(id=employee_id)
            return self._to_entity(db_employee)
        except self.model.DoesNotExist:
            return None

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
            leave_days_entitled=employee.leave_days_entitled,
            is_active=employee.is_active,
            usd_salary=employee.salary.usd_amount if employee.salary else None,
            zig_salary=employee.salary.zig_amount if employee.salary else None,
            pay_frequency=employee.pay_frequency.value,
            bank_name=employee.bank_account.bank_name,
            bank_account=employee.bank_account.account_number,
            pension_fund=employee.pension_fund,
            nssa_number=employee.statutory_info.nssa_number,
            zimra_tax_number=employee.statutory_info.zimra_number,
            paye_number=employee.statutory_info.paye_number,
            pays_aids_levy=employee.statutory_info.pays_aids_levy,
            emergency_contact_name=employee.emergency_contact.name,
            emergency_contact_number=employee.emergency_contact.number,
            emergency_contact_relationship=employee.emergency_contact.relationship,
        )
        db_employee.save()
        # Update the entity with the generated ID
        object.__setattr__(employee, "id", db_employee.id)

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
            department_id=employee.department_id,
            position_id=employee.position_id,
            role_id=employee.role_id,
            employee_type=employee.employee_type.value,
            reports_to_id=employee.reports_to_id,
            date_joined=employee.date_joined,
            contract_from=employee.contract_from,
            contract_to=employee.contract_to,
            leave_days_entitled=employee.leave_days_entitled,
            is_active=employee.is_active,
            usd_salary=employee.salary.usd_amount if employee.salary else None,
            zig_salary=employee.salary.zig_amount if employee.salary else None,
            pay_frequency=employee.pay_frequency.value,
            bank_name=employee.bank_account.bank_name,
            bank_account=employee.bank_account.account_number,
            pension_fund=employee.pension_fund,
            nssa_number=employee.statutory_info.nssa_number,
            zimra_tax_number=employee.statutory_info.zimra_number,
            paye_number=employee.statutory_info.paye_number,
            pays_aids_levy=employee.statutory_info.pays_aids_levy,
            emergency_contact_name=employee.emergency_contact.name,
            emergency_contact_number=employee.emergency_contact.number,
            emergency_contact_relationship=employee.emergency_contact.relationship,
        )

    @transaction.atomic
    def delete(self, employee_id: int) -> bool:
        """Hard delete an employee. Returns True if deleted."""
        deleted, _ = self.model.objects.filter(id=employee_id).delete()
        return deleted > 0

    def _to_entity(self, db_employee) -> Employee:
        """Convert Django model to domain entity."""
        # Build salary
        salary = None
        if db_employee.usd_salary or db_employee.zig_salary:
            salary = Salary.create(
                usd_amount=db_employee.usd_salary or Decimal("0"),
                zig_amount=db_employee.zig_salary or Decimal("0"),
            )

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
            leave_days_entitled=db_employee.leave_days_entitled,
            is_active=db_employee.is_active,
            salary=salary,
            pay_frequency=PayFrequency.from_string(db_employee.pay_frequency),
            bank_account=BankAccount(
                bank_name=db_employee.bank_name or "",
                account_number=db_employee.bank_account or "",
            ),
            statutory_info=StatutoryInfo(
                nssa_number=db_employee.nssa_number or "",
                zimra_number=db_employee.zimra_tax_number or "",
                paye_number=db_employee.paye_number or "",
                pays_aids_levy=db_employee.pays_aids_levy,
            ),
            pension_fund=db_employee.pension_fund or "",
            emergency_contact=EmergencyContact(
                name=db_employee.emergency_contact_name or "",
                phone=db_employee.emergency_contact_number or "",
                relationship=db_employee.emergency_contact_relationship or "",
            ),
        )
