"""
Django ORM repository for ExchangeRate.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from modules.payroll.infrastructure.persistence.models import DailyZiGRateToUSD

from modules.payroll.domain.entities import ExchangeRate
from modules.payroll.application.interfaces import IExchangeRateRepository


class DjangoExchangeRateRepository(IExchangeRateRepository):
    """Django ORM implementation of IExchangeRateRepository."""

    def get_by_id(self, rate_id: int) -> Optional[ExchangeRate]:
        """Get exchange rate by ID."""
        try:
            model = DailyZiGRateToUSD.objects.get(id=rate_id)
            return self._to_entity(model)
        except DailyZiGRateToUSD.DoesNotExist:
            return None

    def get_by_date(self, rate_date: date) -> Optional[ExchangeRate]:
        """Get exchange rate for a specific date."""
        try:
            model = DailyZiGRateToUSD.objects.get(date=rate_date)
            return self._to_entity(model)
        except DailyZiGRateToUSD.DoesNotExist:
            return None

    def get_latest(self, as_of: Optional[date] = None) -> Optional[ExchangeRate]:
        """Get the latest exchange rate, optionally as of a specific date."""
        queryset = DailyZiGRateToUSD.objects.all()
        if as_of:
            queryset = queryset.filter(date__lte=as_of)

        model = queryset.order_by("-date").first()
        return self._to_entity(model) if model else None

    def save(self, exchange_rate: ExchangeRate) -> ExchangeRate:
        """Save an exchange rate."""
        if exchange_rate.id:
            # Update existing
            try:
                model = DailyZiGRateToUSD.objects.get(id=exchange_rate.id)
                model.average = exchange_rate.zig_to_usd_rate
                model.save()
            except DailyZiGRateToUSD.DoesNotExist:
                model = self._create_model(exchange_rate)
        else:
            # Check for existing rate on same date
            try:
                model = DailyZiGRateToUSD.objects.get(date=exchange_rate.rate_date)
                model.average = exchange_rate.zig_to_usd_rate
                model.save()
            except DailyZiGRateToUSD.DoesNotExist:
                model = self._create_model(exchange_rate)

        return self._to_entity(model)

    def delete(self, rate_id: int) -> bool:
        """Delete an exchange rate."""
        try:
            DailyZiGRateToUSD.objects.filter(id=rate_id).delete()
            return True
        except Exception:
            return False

    def get_range(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRate]:
        """Get exchange rates within a date range."""
        models = DailyZiGRateToUSD.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by("-date")

        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: DailyZiGRateToUSD) -> ExchangeRate:
        """Convert Django model to domain entity."""
        return ExchangeRate(
            id=model.id,
            rate_date=model.date,
            zig_to_usd_rate=model.average,
            source=None,  # Legacy model doesn't store source
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _create_model(self, entity: ExchangeRate) -> DailyZiGRateToUSD:
        """Create Django model from entity."""
        return DailyZiGRateToUSD.objects.create(
            date=entity.rate_date,
            average=entity.zig_to_usd_rate
        )
