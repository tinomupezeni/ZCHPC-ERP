"""
Employee aggregate root.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import Email, NationalId, PhoneNumber, EmployeeId

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


class Employee(AggregateRoot[int]):
    """
    Employee aggregate root.

    Core entity representing an employee in the organization.
    """

    def __init__(
        self,
        id: int,
        employee_id: EmployeeId,
        first_name: str,
        surname: str,
        user_id: UUID | None = None,
        national_id: NationalId | None = None,
        date_of_birth: date | None = None,
        gender: Gender | None = None,
        marital_status: MaritalStatus | None = None,
        email: Email | None = None,
        phone: PhoneNumber | None = None,
        department_id: int | None = None,
        position_id: int | None = None,
        role_id: int | None = None,
        employee_type: EmploymentType = EmploymentType.FULL_TIME,
        reports_to_id: int | None = None,
        date_joined: date | None = None,
        contract_from: date | None = None,
        contract_to: date | None = None,
        leave_days_entitled: int = 22,
        is_active: bool = True,
        salary: Salary | None = None,
        pay_frequency: PayFrequency = PayFrequency.MONTHLY,
        bank_account: BankAccount | None = None,
        statutory_info: StatutoryInfo | None = None,
        pension_fund: str = "",
        emergency_contact: EmergencyContact | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        """Initialize employee."""
        super().__init__(id)
        self.employee_id = employee_id
        self.user_id = user_id
        self.first_name = first_name
        self.surname = surname
        self.national_id = national_id
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.marital_status = marital_status
        self.email = email
        self.phone = phone
        self.department_id = department_id
        self.position_id = position_id
        self.role_id = role_id
        self.employee_type = employee_type
        self.reports_to_id = reports_to_id
        self.date_joined = date_joined or date.today()
        self.contract_from = contract_from
        self.contract_to = contract_to
        self.leave_days_entitled = leave_days_entitled
        self.is_active = is_active
        self.salary = salary
        self.pay_frequency = pay_frequency
        self.bank_account = bank_account or BankAccount.empty()
        self.statutory_info = statutory_info or StatutoryInfo.empty()
        self.pension_fund = pension_fund
        self.emergency_contact = emergency_contact or EmergencyContact.empty()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate_basic()

    def _validate_basic(self) -> None:
        """Validate basic required fields."""
        if not self.first_name:
            raise ValidationError(
                message="First name is required",
                code="EMPTY_FIRST_NAME",
            )
        if not self.surname:
            raise ValidationError(
                message="Surname is required",
                code="EMPTY_SURNAME",
            )

    @property
    def full_name(self) -> str:
        """Get employee's full name."""
        return f"{self.first_name} {self.surname}"

    @property
    def is_on_contract(self) -> bool:
        """Check if employee is on a fixed-term contract."""
        return self.contract_to is not None

    @property
    def contract_expired(self) -> bool:
        """Check if contract has expired."""
        if not self.contract_to:
            return False
        return date.today() > self.contract_to

    @property
    def years_of_service(self) -> int:
        """Calculate years of service."""
        today = date.today()
        years = today.year - self.date_joined.year
        if (today.month, today.day) < (self.date_joined.month, self.date_joined.day):
            years -= 1
        return max(0, years)

    def update_personal_info(
        self,
        first_name: str | None = None,
        surname: str | None = None,
        date_of_birth: date | None = None,
        gender: Gender | None = None,
        marital_status: MaritalStatus | None = None,
    ) -> None:
        """Update personal information."""
        if first_name is not None:
            self.first_name = first_name.strip()
        if surname is not None:
            self.surname = surname.strip()
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        if gender is not None:
            self.gender = gender
        if marital_status is not None:
            self.marital_status = marital_status

        self._validate_basic()
        self.updated_at = datetime.utcnow()

    def update_contact_info(
        self,
        email: Email | str | None = None,
        phone: PhoneNumber | str | None = None,
    ) -> None:
        """Update contact information."""
        if email is not None:
            self.email = Email(email) if isinstance(email, str) else email
        if phone is not None:
            self.phone = PhoneNumber(phone) if isinstance(phone, str) else phone
        self.updated_at = datetime.utcnow()

    def update_employment(
        self,
        department_id: int | None = None,
        position_id: int | None = None,
        role_id: int | None = None,
        employee_type: EmploymentType | None = None,
        reports_to_id: int | None = None,
    ) -> None:
        """Update employment details."""
        if department_id is not None:
            self.department_id = department_id
        if position_id is not None:
            self.position_id = position_id
        if role_id is not None:
            self.role_id = role_id
        if employee_type is not None:
            self.employee_type = employee_type
        if reports_to_id is not None:
            if reports_to_id == self.id:
                raise ValidationError(
                    message="Employee cannot report to themselves",
                    code="INVALID_REPORTS_TO",
                )
            self.reports_to_id = reports_to_id
        self.updated_at = datetime.utcnow()

    def update_salary(self, new_salary: Salary) -> Salary | None:
        """
        Update employee salary.

        Args:
            new_salary: New salary

        Returns:
            Previous salary for audit
        """
        old_salary = self.salary
        self.salary = new_salary
        self.updated_at = datetime.utcnow()
        return old_salary

    def update_bank_account(self, bank_account: BankAccount) -> None:
        """Update bank account information."""
        self.bank_account = bank_account
        self.updated_at = datetime.utcnow()

    def update_statutory_info(self, statutory_info: StatutoryInfo) -> None:
        """Update statutory information."""
        self.statutory_info = statutory_info
        self.updated_at = datetime.utcnow()

    def update_emergency_contact(self, contact: EmergencyContact) -> None:
        """Update emergency contact."""
        self.emergency_contact = contact
        self.updated_at = datetime.utcnow()

    def update_contract(
        self,
        contract_from: date | None = None,
        contract_to: date | None = None,
    ) -> None:
        """Update contract dates."""
        if contract_from is not None:
            self.contract_from = contract_from
        if contract_to is not None:
            if self.contract_from and contract_to < self.contract_from:
                raise ValidationError(
                    message="Contract end date must be after start date",
                    code="INVALID_CONTRACT_DATES",
                )
            self.contract_to = contract_to
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the employee (soft delete)."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def reactivate(self) -> None:
        """Reactivate a deactivated employee."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def link_user(self, user_id: UUID) -> None:
        """Link employee to a user account."""
        self.user_id = user_id
        self.updated_at = datetime.utcnow()

    def unlink_user(self) -> None:
        """Remove link to user account."""
        self.user_id = None
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation."""
        return f"{self.full_name} ({self.employee_id})"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Employee(id={self.id}, employee_id={self.employee_id}, name='{self.full_name}')"
