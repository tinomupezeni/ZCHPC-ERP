"""
Exchange rate application service.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError

from modules.payroll.domain.entities import ExchangeRate
from modules.payroll.application.interfaces import IExchangeRateRepository


@dataclass
class CreateExchangeRateCommand:
    """Command to create an exchange rate."""

    rate_date: date
    zig_to_usd_rate: Decimal
    source: Optional[str] = None


@dataclass
class UpdateExchangeRateCommand:
    """Command to update an exchange rate."""

    rate_id: int
    zig_to_usd_rate: Decimal
    source: Optional[str] = None


class ExchangeRateService:
    """Application service for exchange rate management."""

    def __init__(self, repository: IExchangeRateRepository):
        self.repository = repository

    def get_latest(self, as_of: Optional[date] = None) -> Optional[ExchangeRate]:
        """Get the latest exchange rate."""
        return self.repository.get_latest(as_of)

    def get_by_date(self, rate_date: date) -> Optional[ExchangeRate]:
        """Get exchange rate for a specific date."""
        return self.repository.get_by_date(rate_date)

    def get_by_id(self, rate_id: int) -> Optional[ExchangeRate]:
        """Get exchange rate by ID."""
        return self.repository.get_by_id(rate_id)

    def get_range(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRate]:
        """Get exchange rates within a date range."""
        return self.repository.get_range(start_date, end_date)

    def create(self, command: CreateExchangeRateCommand) -> ExchangeRate:
        """
        Create a new exchange rate.

        If a rate already exists for the date, it will be updated.
        """
        existing = self.repository.get_by_date(command.rate_date)
        if existing:
            existing.update_rate(command.zig_to_usd_rate, command.source)
            return self.repository.save(existing)

        rate = ExchangeRate.create(
            rate_date=command.rate_date,
            zig_to_usd_rate=command.zig_to_usd_rate,
            source=command.source
        )
        return self.repository.save(rate)

    def update(self, command: UpdateExchangeRateCommand) -> ExchangeRate:
        """Update an existing exchange rate."""
        rate = self.repository.get_by_id(command.rate_id)
        if not rate:
            raise NotFoundError(f"Exchange rate {command.rate_id} not found")

        rate.update_rate(command.zig_to_usd_rate, command.source)
        return self.repository.save(rate)

    def delete(self, rate_id: int) -> bool:
        """Delete an exchange rate."""
        rate = self.repository.get_by_id(rate_id)
        if not rate:
            raise NotFoundError(f"Exchange rate {rate_id} not found")

        return self.repository.delete(rate_id)

    def convert_zig_to_usd(
        self, amount: Decimal, as_of: Optional[date] = None
    ) -> Decimal:
        """Convert ZIG to USD using the latest rate."""
        rate = self.repository.get_latest(as_of)
        if not rate:
            raise ValidationError("No exchange rate available")
        return rate.convert_zig_to_usd(amount)

    def convert_usd_to_zig(
        self, amount: Decimal, as_of: Optional[date] = None
    ) -> Decimal:
        """Convert USD to ZIG using the latest rate."""
        rate = self.repository.get_latest(as_of)
        if not rate:
            raise ValidationError("No exchange rate available")
        return rate.convert_usd_to_zig(amount)
