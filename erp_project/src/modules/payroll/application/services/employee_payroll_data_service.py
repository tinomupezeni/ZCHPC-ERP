"""
Actor-aware access to an employee's payroll profile, statutory profile and bank
accounts.

Targets arrive as ``Employees.uuid`` (that is what the URLs carry). The only
thing resolved before authorization is the target's integer primary key - the
identifier payroll tables and PayrollActor.employee_id use - and it is resolved
without loading any payroll data. Authorization then runs against that id
(``None`` when the employee does not exist, so an unauthorized caller cannot
tell existing from missing). Only after it succeeds is anything read or written.
"""

from uuid import UUID

from modules.hr.infrastructure.persistence.models import Employees
from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
)
from modules.payroll.infrastructure.persistence.models import (
    EmployeeBankAccount,
    PayrollProfile,
    StatutoryProfile,
)
from shared.domain.exceptions import NotFoundError


class EmployeePayrollDataService:
    def __init__(self, policy: PayrollAuthorizationPolicy | None = None) -> None:
        self._policy = policy or PayrollAuthorizationPolicy()

    # ------------------------------------------------------------ profile

    def get_payroll_profile(self, actor: PayrollActor, employee_uuid: UUID | str) -> PayrollProfile:
        """
        An employee with no profile row yet reads as the model defaults. The
        read never creates the row (this replaces the get_or_create on a
        related-field lookup, which raised for a missing row).
        """
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_view_payroll_profile(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        return PayrollProfile.objects.filter(employee_id=employee_pk).select_related(
            "employee"
        ).first() or PayrollProfile(employee=Employees.objects.get(pk=employee_pk))

    def update_payroll_profile(
        self, actor: PayrollActor, employee_uuid: UUID | str, values: dict
    ) -> PayrollProfile:
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_manage_payroll_profile(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        profile = self._existing(PayrollProfile, employee_pk, "Payroll profile")
        for key, value in values.items():
            setattr(profile, key, value)
        profile.save()
        return profile

    # ---------------------------------------------------------- statutory

    def get_statutory_profile(
        self, actor: PayrollActor, employee_uuid: UUID | str
    ) -> StatutoryProfile:
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_view_statutory_profile(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        return StatutoryProfile.objects.filter(employee_id=employee_pk).first() or StatutoryProfile(
            employee_id=employee_pk
        )

    def update_statutory_profile(
        self, actor: PayrollActor, employee_uuid: UUID | str, values: dict
    ) -> StatutoryProfile:
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_manage_statutory_profile(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        profile = self._existing(StatutoryProfile, employee_pk, "Statutory profile")
        for key, value in values.items():
            setattr(profile, key, value)
        profile.save()
        return profile

    # ------------------------------------------------------------- banks

    def list_bank_accounts(
        self, actor: PayrollActor, employee_uuid: UUID | str
    ) -> list[EmployeeBankAccount]:
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_view_bank_accounts(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        return list(EmployeeBankAccount.objects.filter(employee_id=employee_pk))

    def add_bank_account(
        self, actor: PayrollActor, employee_uuid: UUID | str, values: dict
    ) -> EmployeeBankAccount:
        employee_pk = self._resolve(employee_uuid)
        self._policy.authorize_manage_bank_accounts(actor, employee_pk)
        employee_pk = self._require_found(employee_pk)
        return EmployeeBankAccount.objects.create(employee_id=employee_pk, **values)

    # ---------------------------------------------------------- internal

    @staticmethod
    def _resolve(employee_uuid: UUID | str) -> int | None:
        """Employees.uuid -> Employees.pk, loading nothing else. None if absent."""
        return (
            Employees.objects.filter(uuid=employee_uuid)
            .values_list("pk", flat=True)
            .first()
        )

    @staticmethod
    def _require_found(employee_pk: int | None) -> int:
        if employee_pk is None:
            raise NotFoundError("Employee not found")
        return employee_pk

    @staticmethod
    def _existing(model, employee_pk: int, label: str):
        record = model.objects.filter(employee_id=employee_pk).first()
        if record is None:
            raise NotFoundError(f"{label} not found")
        return record
