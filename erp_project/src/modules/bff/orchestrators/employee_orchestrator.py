from modules.hr.infrastructure.persistence.models import Employees
from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
)
from modules.payroll.infrastructure.persistence.models import PayrollProfile, EmployeeBankAccount, StatutoryProfile
from shared.domain.exceptions import AuthorizationError

_policy = PayrollAuthorizationPolicy()

# Payload keys that belong to each payroll-owned section of the unified profile.
_PROFILE_KEYS = ("usd_salary", "zig_salary", "pay_frequency")
_BANK_KEYS = ("bank_name", "bank_account")
_STATUTORY_KEYS = ("nssa_number", "zimra_tax_number", "paye_number")
# HR fields written through EmployeeService.update_employee, so they are held
# to the same rules as PATCH /hr/employees/<id>/: authority over the employee
# for the ordinary fields (AUD-02 F1/F8), and the email's validation and
# uniqueness (AUD-02 F9). Same names as UpdateEmployeeCommand's fields.
_HR_SERVICE_KEYS = ("first_name", "surname", "phone", "email")


def _employee_service():
    from modules.hr.application.services import EmployeeService
    from modules.hr.infrastructure.persistence.department_repository import (
        DjangoDepartmentRepository,
    )
    from modules.hr.infrastructure.persistence.employee_repository import (
        DjangoEmployeeRepository,
    )
    from modules.hr.infrastructure.persistence.position_repository import (
        DjangoPositionRepository,
    )

    return EmployeeService(
        employee_repository=DjangoEmployeeRepository(),
        department_repository=DjangoDepartmentRepository(),
        position_repository=DjangoPositionRepository(),
    )


def _may(authorize, actor, employee_pk) -> bool:
    """Whether the payroll policy permits this read; denial redacts, it does not fail."""
    try:
        authorize(actor, employee_pk)
    except AuthorizationError:
        return False
    return True


class EmployeeOrchestrator:
    """
    Unified employee profile across HR and payroll.

    The salary, bank and statutory sections are payroll data and are governed
    by the payroll authorization policy (REM-02): a section the actor may not
    view is returned as nulls, and a write touching a section the actor may not
    manage is refused outright, before anything (including the HR fields in the
    same request) is saved.

    first_name, surname, phone and email are written by EmployeeService, not
    here, so the HR API's rules apply to them unchanged: editing another
    employee's ordinary fields needs authority over that employee (AUD-02
    F8), and an email is validated and must not be another employee's
    (AUD-02 F9). Everything in one request commits together or not at all.
    """

    @staticmethod
    def get_full_profile(uuid, actor: PayrollActor):
        try:
            employee = Employees.objects.get(uuid=uuid)
        except Employees.DoesNotExist:
            return None

        payroll_profile = bank_account = statutory_profile = None

        if _may(_policy.authorize_view_payroll_profile, actor, employee.pk):
            payroll_profile = PayrollProfile.objects.filter(employee=employee).first()

        if _may(_policy.authorize_view_bank_accounts, actor, employee.pk):
            bank_account = EmployeeBankAccount.objects.filter(employee=employee, is_primary=True).first()
            if not bank_account:
                bank_account = EmployeeBankAccount.objects.filter(employee=employee).first()

        if _may(_policy.authorize_view_statutory_profile, actor, employee.pk):
            statutory_profile = StatutoryProfile.objects.filter(employee=employee).first()

        return {
            # HR
            "uuid": employee.uuid,
            "employee_id": employee.employee_id,
            "first_name": employee.first_name,
            "surname": employee.surname,
            "email": employee.email,
            "phone": employee.phone,

            # Payroll
            "usd_salary": payroll_profile.usd_salary if payroll_profile else None,
            "zig_salary": payroll_profile.zig_salary if payroll_profile else None,
            "pay_frequency": payroll_profile.pay_frequency if payroll_profile else None,

            # Bank
            "bank_name": bank_account.bank_name if bank_account else None,
            "bank_account": bank_account.account_number if bank_account else None,

            # Statutory
            "nssa_number": statutory_profile.nssa_number if statutory_profile else None,
            "zimra_tax_number": statutory_profile.zimra_tax_number if statutory_profile else None,
            "paye_number": statutory_profile.paye_number if statutory_profile else None,
        }

    @staticmethod
    def update_full_profile(uuid, data, actor: PayrollActor):
        from django.db import transaction

        touches_profile = any(k in data for k in _PROFILE_KEYS)
        touches_bank = any(k in data for k in _BANK_KEYS)
        touches_statutory = any(k in data for k in _STATUTORY_KEYS)

        # Authorize every payroll section this request touches before anything
        # is loaded beyond the target's id, and before anything is saved.
        employee_pk = Employees.objects.filter(uuid=uuid).values_list("pk", flat=True).first()
        if touches_profile:
            _policy.authorize_manage_payroll_profile(actor, employee_pk)
        if touches_bank:
            _policy.authorize_manage_bank_accounts(actor, employee_pk)
        if touches_statutory:
            _policy.authorize_manage_statutory_profile(actor, employee_pk)

        if employee_pk is None:
            return None

        from modules.hr.application.services import UpdateEmployeeCommand

        hr_changes = {key: data[key] for key in _HR_SERVICE_KEYS if key in data}

        try:
            with transaction.atomic():
                # 1. Update HR fields. The service authorizes before it writes;
                # a refusal here, or any failure below, rolls the whole
                # request back.
                if hr_changes:
                    _employee_service().update_employee(
                        UpdateEmployeeCommand(employee_id=employee_pk, **hr_changes),
                        actor_permissions=actor.permissions,
                        actor_employee_id=actor.employee_id,
                    )

                employee = Employees.objects.get(uuid=uuid)

                # 2. Update Payroll Profile
                if touches_profile:
                    payroll_profile, _ = PayrollProfile.objects.get_or_create(employee=employee)
                    if 'usd_salary' in data: payroll_profile.usd_salary = data['usd_salary']
                    if 'zig_salary' in data: payroll_profile.zig_salary = data['zig_salary']
                    if 'pay_frequency' in data: payroll_profile.pay_frequency = data['pay_frequency']
                    payroll_profile.save()

                # 3. Update Bank Account
                if touches_bank:
                    bank_account, _ = EmployeeBankAccount.objects.get_or_create(employee=employee, is_primary=True)
                    if 'bank_name' in data: bank_account.bank_name = data['bank_name']
                    if 'bank_account' in data: bank_account.account_number = data['bank_account']
                    bank_account.save()

                # 4. Update Statutory Info
                if touches_statutory:
                    statutory_profile, _ = StatutoryProfile.objects.get_or_create(employee=employee)
                    if 'nssa_number' in data: statutory_profile.nssa_number = data['nssa_number']
                    if 'zimra_tax_number' in data: statutory_profile.zimra_tax_number = data['zimra_tax_number']
                    if 'paye_number' in data: statutory_profile.paye_number = data['paye_number']
                    statutory_profile.save()

                return EmployeeOrchestrator.get_full_profile(uuid, actor)

        except Employees.DoesNotExist:
            return None
