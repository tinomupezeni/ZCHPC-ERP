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
    EmployeeLifecycleStatus,
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
        lifecycle_status: EmployeeLifecycleStatus = EmployeeLifecycleStatus.ACTIVE,
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
        self.lifecycle_status = EmployeeLifecycleStatus(lifecycle_status)
        self.emergency_contact = emergency_contact or EmergencyContact.empty()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        # Set only on the instance that was just created, when a login was
        # provisioned for it: the one-time temporary password for the
        # authorized creator (REM-07). Never persisted or reloaded.
        self.temporary_password: str | None = None
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
    def is_active(self) -> bool:
        """Whether the employee is in normal employment (derived, read-only)."""
        return self.lifecycle_status is EmployeeLifecycleStatus.ACTIVE

    @property
    def is_deactivated(self) -> bool:
        """Whether the employee is temporarily suspended."""
        return self.lifecycle_status is EmployeeLifecycleStatus.DEACTIVATED

    @property
    def is_archived(self) -> bool:
        """Whether this employment lifecycle is permanently closed."""
        return self.lifecycle_status is EmployeeLifecycleStatus.ARCHIVED

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

    def deactivate(self) -> bool:
        """
        ACTIVE -> DEACTIVATED (temporary suspension).

        Returns True if the state changed, False if the employee was already
        deactivated (nothing is touched). An archived employee is refused.
        """
        return self._move_to(EmployeeLifecycleStatus.DEACTIVATED, "deactivated")

    def reactivate(self) -> bool:
        """
        DEACTIVATED -> ACTIVE.

        Returns True if the state changed, False if the employee was already
        active (nothing is touched). An archived employee is refused.
        """
        return self._move_to(EmployeeLifecycleStatus.ACTIVE, "reactivated")

    def _move_to(self, target: EmployeeLifecycleStatus, action: str) -> bool:
        self._ensure_not_archived(action)
        if self.lifecycle_status is target:
            return False
        self.lifecycle_status = target
        self.updated_at = datetime.utcnow()
        return True

    def _ensure_not_archived(self, action: str) -> None:
        """An archived employment lifecycle is closed and is not reopened."""
        if self.is_archived:
            raise ValidationError(
                message=f"An archived employee cannot be {action}",
                code="EMPLOYEE_ARCHIVED",
            )

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
