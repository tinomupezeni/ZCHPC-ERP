"""
Django implementation of currency repository.
"""

from decimal import Decimal
from typing import List, Optional

from modules.accounts.infrastructure.persistence.models import Currency as CurrencyModel
from modules.accounts.domain.entities import Currency
from modules.accounts.application.interfaces import ICurrencyRepository


class DjangoCurrencyRepository(ICurrencyRepository):
    """Django ORM implementation of currency repository."""

    def _to_domain(self, model: CurrencyModel) -> Currency:
        """Convert Django model to domain entity."""
        return Currency(
            id=model.id,
            code=model.code,
            name=model.name,
            symbol=model.symbol,
            rate_to_base=model.rate_to_base,
            is_base=model.rate_to_base == Decimal("1"),
            is_active=True,  # Legacy model doesn't have is_active
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model_data(self, currency: Currency) -> dict:
        """Convert domain entity to model data."""
        return {
            "code": currency.code,
            "name": currency.name,
            "symbol": currency.symbol,
            "rate_to_base": currency.rate_to_base,
        }

    def save(self, currency: Currency) -> Currency:
        """Save a currency."""
        data = self._to_model_data(currency)

        if currency.id is None:
            model = CurrencyModel.objects.create(**data)
        else:
            CurrencyModel.objects.filter(id=currency.id).update(**data)
            model = CurrencyModel.objects.get(id=currency.id)

        return self._to_domain(model)

    def get_by_id(self, currency_id: int) -> Optional[Currency]:
        """Get a currency by ID."""
        try:
            model = CurrencyModel.objects.get(id=currency_id)
            return self._to_domain(model)
        except CurrencyModel.DoesNotExist:
            return None

    def get_by_code(self, code: str) -> Optional[Currency]:
        """Get a currency by code."""
        try:
            model = CurrencyModel.objects.get(code=code.upper())
            return self._to_domain(model)
        except CurrencyModel.DoesNotExist:
            return None

    def get_all(self, include_inactive: bool = False) -> List[Currency]:
        """Get all currencies."""
        models = CurrencyModel.objects.all().order_by("code")
        return [self._to_domain(m) for m in models]

    def get_base_currency(self) -> Optional[Currency]:
        """Get the base currency (rate = 1)."""
        try:
            model = CurrencyModel.objects.get(rate_to_base=Decimal("1"))
            return self._to_domain(model)
        except CurrencyModel.DoesNotExist:
            return None
        except CurrencyModel.MultipleObjectsReturned:
            # Return the first one
            model = CurrencyModel.objects.filter(
                rate_to_base=Decimal("1")
            ).first()
            return self._to_domain(model) if model else None

    def delete(self, currency_id: int) -> bool:
        """Delete a currency."""
        deleted, _ = CurrencyModel.objects.filter(id=currency_id).delete()
        return deleted > 0
