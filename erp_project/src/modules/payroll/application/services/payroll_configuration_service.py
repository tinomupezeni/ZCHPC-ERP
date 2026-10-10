"""
Actor-aware access to payroll configuration: tax brackets, exchange rates and
allowance/deduction types.

The same AllowanceType/DeductionType tables are administered through both the
payroll routes and the HR routes; both go through this service so that neither
remains an unprotected way to change them. As with RoleService (REM-05), it
works against the Django models directly - the pre-existing view logic moved
here unchanged, with the authorization boundary added in front of it.

Reading configuration and changing it are distinct capabilities.
"""

from datetime import date
from decimal import Decimal

from modules.hr.infrastructure.persistence.models import AllowanceType, DeductionType
from modules.payroll.application.authorization import (
    PayrollActor,
    PayrollAuthorizationPolicy,
)
from modules.payroll.infrastructure.persistence.models import DailyZiGRateToUSD, TaxBracket
from shared.domain.exceptions import NotFoundError, ValidationError


class PayrollConfigurationService:
    def __init__(self, policy: PayrollAuthorizationPolicy | None = None) -> None:
        self._policy = policy or PayrollAuthorizationPolicy()

    def _view(self, actor: PayrollActor) -> None:
        self._policy.authorize_view_configuration(actor)

    def _manage(self, actor: PayrollActor) -> None:
        self._policy.authorize_manage_configuration(actor)

    # ------------------------------------------------------- tax brackets

    def list_tax_brackets(self, actor: PayrollActor, currency: str | None = None):
        self._view(actor)
        queryset = TaxBracket.objects.all().order_by("currency", "min_income", "-active_from")
        if currency:
            # Stored as the model's choice ("ZiG"); match any spelling. PY-12.
            queryset = queryset.filter(currency__iexact=currency)
        return list(queryset)

    def get_tax_bracket(self, actor: PayrollActor, bracket_id: int) -> TaxBracket:
        self._view(actor)
        return self._get(TaxBracket, bracket_id, "Tax bracket not found")

    def create_tax_bracket(self, actor: PayrollActor, data: dict) -> TaxBracket:
        self._manage(actor)
        return TaxBracket.objects.create(
            currency=data["currency"],
            min_income=data["min_income"],
            max_income=data.get("max_income"),
            rate=data["rate"],
            deduction=data["deduction"],
            active_from=data["active_from"],
            provider=data.get("provider", ""),
        )

    def update_tax_bracket(self, actor: PayrollActor, bracket_id: int, data: dict) -> TaxBracket:
        self._manage(actor)
        bracket = self._get(TaxBracket, bracket_id, "Tax bracket not found")
        for key, value in data.items():
            setattr(bracket, key, value)
        bracket.save()
        return bracket

    def delete_tax_bracket(self, actor: PayrollActor, bracket_id: int) -> None:
        self._manage(actor)
        TaxBracket.objects.filter(id=bracket_id).delete()

    # ---------------------------------------------------- exchange rates

    def list_exchange_rates(self, actor: PayrollActor, limit: int = 365):
        self._view(actor)
        return list(DailyZiGRateToUSD.objects.all().order_by("-date")[:limit])

    def get_exchange_rate(self, actor: PayrollActor, rate_id: int) -> DailyZiGRateToUSD:
        self._view(actor)
        return self._get(DailyZiGRateToUSD, rate_id, "Exchange rate not found")

    def get_latest_exchange_rate(self, actor: PayrollActor) -> DailyZiGRateToUSD:
        self._view(actor)
        rate = DailyZiGRateToUSD.objects.order_by("-date").first()
        if rate is None:
            raise NotFoundError("No exchange rates available")
        return rate

    def save_exchange_rate(
        self, actor: PayrollActor, rate_date: date, zig_rate: Decimal
    ) -> DailyZiGRateToUSD:
        """Create the rate for the date, or overwrite the existing one."""
        self._manage(actor)
        existing = DailyZiGRateToUSD.objects.filter(date=rate_date).first()
        if existing:
            existing.average = zig_rate
            existing.save()
            return existing
        return DailyZiGRateToUSD.objects.create(date=rate_date, average=zig_rate)

    def delete_exchange_rate(self, actor: PayrollActor, rate_id: int) -> None:
        self._manage(actor)
        DailyZiGRateToUSD.objects.filter(id=rate_id).delete()

    # ---------------------------------------- allowance / deduction types

    def list_allowance_types(self, actor: PayrollActor, active_only: bool = False):
        self._view(actor)
        queryset = AllowanceType.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.order_by("name"))

    def list_deduction_types(self, actor: PayrollActor, active_only: bool = False):
        self._view(actor)
        queryset = DeductionType.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return list(queryset.order_by("name"))

    def get_deduction_type(self, actor: PayrollActor, deduction_id: int) -> DeductionType:
        self._view(actor)
        return self._get(DeductionType, deduction_id, "Deduction type not found")

    def create_allowance_type(self, actor: PayrollActor, **fields) -> AllowanceType:
        self._manage(actor)
        self._require_unique_name(AllowanceType, fields, "Allowance")
        return AllowanceType.objects.create(**fields)

    def create_deduction_type(self, actor: PayrollActor, **fields) -> DeductionType:
        self._manage(actor)
        self._require_unique_name(DeductionType, fields, "Deduction")
        return DeductionType.objects.create(**fields)

    def update_deduction_type(
        self, actor: PayrollActor, deduction_id: int, changes: dict
    ) -> DeductionType:
        self._manage(actor)
        deduction = self._get(DeductionType, deduction_id, "Deduction type not found")
        for key, value in changes.items():
            setattr(deduction, key, value)
        deduction.save()
        return deduction

    def deactivate_deduction_type(self, actor: PayrollActor, deduction_id: int) -> None:
        self._manage(actor)
        deduction = self._get(DeductionType, deduction_id, "Deduction type not found")
        deduction.is_active = False
        deduction.save()

    def deactivate_allowance_type(self, actor: PayrollActor, allowance_id: int) -> None:
        self._manage(actor)
        allowance = self._get(AllowanceType, allowance_id, "Allowance type not found")
        allowance.is_active = False
        allowance.save()

    # ---------------------------------------------------------- internal

    @staticmethod
    def _get(model, pk: int, not_found_message: str):
        try:
            return model.objects.get(id=pk)
        except model.DoesNotExist:
            raise NotFoundError(not_found_message)

    @staticmethod
    def _require_unique_name(model, fields: dict, label: str) -> None:
        if not fields.get("name"):
            raise ValidationError("Name is required", code="NAME_REQUIRED")
        if model.objects.filter(name=fields["name"]).exists():
            raise ValidationError(
                f"{label} type with this name already exists", code="DUPLICATE_NAME"
            )
