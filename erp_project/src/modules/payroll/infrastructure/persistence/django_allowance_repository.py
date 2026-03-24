"""
Django ORM repositories for allowances and deductions.
"""

from decimal import Decimal
from typing import List, Optional

from modules.hr.infrastructure.persistence.models import (
    AllowanceType as AllowanceTypeModel,
    DeductionType as DeductionTypeModel,
    EmployeeAllowance as EmployeeAllowanceModel,
    EmployeeDeduction as EmployeeDeductionModel,
)

from modules.payroll.domain.entities import (
    AllowanceType,
    DeductionType,
    EmployeeAllowance,
    EmployeeDeduction,
)
from modules.payroll.domain.value_objects import Currency
from modules.payroll.application.interfaces import (
    IAllowanceTypeRepository,
    IDeductionTypeRepository,
    IEmployeeAllowanceRepository,
    IEmployeeDeductionRepository,
)


class DjangoAllowanceTypeRepository(IAllowanceTypeRepository):
    """Django ORM implementation of IAllowanceTypeRepository."""

    def get_by_id(self, type_id: int) -> Optional[AllowanceType]:
        """Get allowance type by ID."""
        try:
            model = AllowanceTypeModel.objects.get(id=type_id)
            return self._to_entity(model)
        except AllowanceTypeModel.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Optional[AllowanceType]:
        """Get allowance type by name."""
        model = AllowanceTypeModel.objects.filter(name__iexact=name).first()
        return self._to_entity(model) if model else None

    def get_all(self, active_only: bool = True) -> List[AllowanceType]:
        """Get all allowance types."""
        models = AllowanceTypeModel.objects.all().order_by("name")
        return [self._to_entity(m) for m in models]

    def save(self, allowance_type: AllowanceType) -> AllowanceType:
        """Save an allowance type."""
        if allowance_type.id:
            model = AllowanceTypeModel.objects.get(id=allowance_type.id)
            model.name = allowance_type.name
            model.description = allowance_type.description
            model.amount = allowance_type.default_amount
            model.save()
        else:
            model = AllowanceTypeModel.objects.create(
                name=allowance_type.name,
                description=allowance_type.description,
                amount=allowance_type.default_amount
            )
        return self._to_entity(model)

    def delete(self, type_id: int) -> bool:
        """Delete an allowance type."""
        try:
            AllowanceTypeModel.objects.filter(id=type_id).delete()
            return True
        except Exception:
            return False

    def _to_entity(self, model: AllowanceTypeModel) -> AllowanceType:
        """Convert Django model to domain entity."""
        return AllowanceType(
            id=model.id,
            name=model.name,
            description=model.description,
            default_amount=model.amount or Decimal("0"),
            default_currency=Currency.USD,
            is_taxable=True,
            is_active=True
        )


class DjangoDeductionTypeRepository(IDeductionTypeRepository):
    """Django ORM implementation of IDeductionTypeRepository."""

    def get_by_id(self, type_id: int) -> Optional[DeductionType]:
        """Get deduction type by ID."""
        try:
            model = DeductionTypeModel.objects.get(id=type_id)
            return self._to_entity(model)
        except DeductionTypeModel.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> Optional[DeductionType]:
        """Get deduction type by name."""
        model = DeductionTypeModel.objects.filter(name__iexact=name).first()
        return self._to_entity(model) if model else None

    def get_all(self, active_only: bool = True) -> List[DeductionType]:
        """Get all deduction types."""
        models = DeductionTypeModel.objects.all().order_by("name")
        return [self._to_entity(m) for m in models]

    def save(self, deduction_type: DeductionType) -> DeductionType:
        """Save a deduction type."""
        if deduction_type.id:
            model = DeductionTypeModel.objects.get(id=deduction_type.id)
            model.name = deduction_type.name
            model.description = deduction_type.description
            model.amount = deduction_type.default_amount
            model.save()
        else:
            model = DeductionTypeModel.objects.create(
                name=deduction_type.name,
                description=deduction_type.description,
                amount=deduction_type.default_amount
            )
        return self._to_entity(model)

    def delete(self, type_id: int) -> bool:
        """Delete a deduction type."""
        try:
            DeductionTypeModel.objects.filter(id=type_id).delete()
            return True
        except Exception:
            return False

    def _to_entity(self, model: DeductionTypeModel) -> DeductionType:
        """Convert Django model to domain entity."""
        return DeductionType(
            id=model.id,
            name=model.name,
            description=model.description,
            default_amount=model.amount or Decimal("0"),
            default_currency=Currency.USD,
            is_percentage=False,
            is_pre_tax=False,
            is_active=True
        )


class DjangoEmployeeAllowanceRepository(IEmployeeAllowanceRepository):
    """Django ORM implementation of IEmployeeAllowanceRepository."""

    def get_by_employee(self, employee_id: int) -> List[EmployeeAllowance]:
        """Get all allowances for an employee."""
        models = EmployeeAllowanceModel.objects.filter(
            employee_id=employee_id
        ).select_related("allowance_type")

        return [self._to_entity(m) for m in models]

    def save(self, allowance: EmployeeAllowance) -> EmployeeAllowance:
        """Save an employee allowance."""
        if allowance.id:
            model = EmployeeAllowanceModel.objects.get(id=allowance.id)
            model.amount = allowance.amount
            model.currency = allowance.currency.value
            model.save()
        else:
            model = EmployeeAllowanceModel.objects.create(
                employee_id=allowance.employee_id,
                allowance_type_id=allowance.allowance_type_id,
                amount=allowance.amount,
                currency=allowance.currency.value
            )
        return self._to_entity(model)

    def delete(self, allowance_id: int) -> bool:
        """Delete an employee allowance."""
        try:
            EmployeeAllowanceModel.objects.filter(id=allowance_id).delete()
            return True
        except Exception:
            return False

    def _to_entity(self, model: EmployeeAllowanceModel) -> EmployeeAllowance:
        """Convert Django model to domain entity."""
        currency = Currency.USD
        if hasattr(model, "currency") and model.currency:
            try:
                currency = Currency.from_string(model.currency)
            except ValueError:
                pass

        return EmployeeAllowance(
            id=model.id,
            employee_id=model.employee_id,
            allowance_type_id=model.allowance_type_id,
            allowance_type_name=model.allowance_type.name,
            amount=model.amount or Decimal("0"),
            currency=currency
        )


class DjangoEmployeeDeductionRepository(IEmployeeDeductionRepository):
    """Django ORM implementation of IEmployeeDeductionRepository."""

    def get_by_employee(self, employee_id: int) -> List[EmployeeDeduction]:
        """Get all deductions for an employee."""
        models = EmployeeDeductionModel.objects.filter(
            employee_id=employee_id
        ).select_related("deduction_type")

        return [self._to_entity(m) for m in models]

    def save(self, deduction: EmployeeDeduction) -> EmployeeDeduction:
        """Save an employee deduction."""
        if deduction.id:
            model = EmployeeDeductionModel.objects.get(id=deduction.id)
            model.amount = deduction.amount
            model.currency = deduction.currency.value
            model.save()
        else:
            model = EmployeeDeductionModel.objects.create(
                employee_id=deduction.employee_id,
                deduction_type_id=deduction.deduction_type_id,
                amount=deduction.amount,
                currency=deduction.currency.value
            )
        return self._to_entity(model)

    def delete(self, deduction_id: int) -> bool:
        """Delete an employee deduction."""
        try:
            EmployeeDeductionModel.objects.filter(id=deduction_id).delete()
            return True
        except Exception:
            return False

    def _to_entity(self, model: EmployeeDeductionModel) -> EmployeeDeduction:
        """Convert Django model to domain entity."""
        currency = Currency.USD
        if hasattr(model, "currency") and model.currency:
            try:
                currency = Currency.from_string(model.currency)
            except ValueError:
                pass

        return EmployeeDeduction(
            id=model.id,
            employee_id=model.employee_id,
            deduction_type_id=model.deduction_type_id,
            deduction_type_name=model.deduction_type.name,
            amount=model.amount or Decimal("0"),
            currency=currency,
            is_percentage=False
        )
