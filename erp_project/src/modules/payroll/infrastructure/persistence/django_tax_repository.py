"""
Django ORM repository for TaxTable.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from modules.payroll.infrastructure.persistence.models import TaxBracket as TaxBracketModel

from modules.payroll.domain.entities import TaxTable
from modules.payroll.domain.value_objects import Currency, TaxBracket
from modules.payroll.application.interfaces import ITaxTableRepository


class DjangoTaxTableRepository(ITaxTableRepository):
    """Django ORM implementation of ITaxTableRepository."""

    def get_by_id(self, table_id: int) -> Optional[TaxTable]:
        """Get tax table by ID."""
        # Tax tables are stored as individual brackets in the legacy system
        # We group them by currency and effective date
        try:
            bracket = TaxBracketModel.objects.get(id=table_id)
            return self._bracket_to_table(bracket)
        except TaxBracketModel.DoesNotExist:
            return None

    def get_active_for_currency(
        self, currency: Currency, as_of: date
    ) -> Optional[TaxTable]:
        """Get the active tax table for a currency as of a specific date."""
        brackets = TaxBracketModel.objects.filter(
            currency=currency.value,
            active_from__lte=as_of
        ).order_by("-active_from")

        if not brackets.exists():
            return None

        # Get the most recent effective date
        latest_date = brackets.first().active_from

        # Get all brackets for that effective date
        active_brackets = brackets.filter(active_from=latest_date)

        return self._brackets_to_table(currency, latest_date, active_brackets)

    def get_brackets_for_currency(
        self, currency: Currency, as_of: date
    ) -> List[Tuple[Decimal, Decimal, Decimal, Decimal]]:
        """Get tax brackets as tuples for a currency."""
        brackets = TaxBracketModel.objects.filter(
            currency=currency.value,
            active_from__lte=as_of
        ).order_by("-active_from")

        if not brackets.exists():
            return []

        latest_date = brackets.first().active_from
        active_brackets = brackets.filter(active_from=latest_date)

        return [
            (
                b.min_income,
                b.max_income,
                b.rate,
                b.deduction
            )
            for b in active_brackets.order_by("min_income")
        ]

    def save(self, tax_table: TaxTable) -> TaxTable:
        """Save a tax table by saving its brackets."""
        # Delete existing brackets for this currency and date
        TaxBracketModel.objects.filter(
            currency=tax_table.currency.value,
            active_from=tax_table.effective_from
        ).delete()

        # Create new brackets
        for bracket in tax_table.brackets:
            TaxBracketModel.objects.create(
                currency=tax_table.currency.value,
                min_income=bracket.min_income,
                max_income=bracket.max_income,
                rate=bracket.rate,
                deduction=bracket.deduction,
                active_from=tax_table.effective_from,
                provider=tax_table.provider
            )

        return tax_table

    def get_all(self, currency: Optional[Currency] = None) -> List[TaxTable]:
        """Get all tax tables, optionally filtered by currency."""
        queryset = TaxBracketModel.objects.all()
        if currency:
            queryset = queryset.filter(currency=currency.value)

        # Group by currency and effective date
        tables = {}
        for bracket in queryset.order_by("currency", "-active_from", "min_income"):
            key = (bracket.currency, bracket.active_from)
            if key not in tables:
                tables[key] = []
            tables[key].append(bracket)

        result = []
        for (curr_str, eff_date), brackets in tables.items():
            try:
                curr = Currency.from_string(curr_str)
                result.append(self._brackets_to_table(curr, eff_date, brackets))
            except ValueError:
                continue

        return result

    def _bracket_to_table(self, bracket_model: TaxBracketModel) -> TaxTable:
        """Convert a single bracket model to a table with one bracket."""
        currency = Currency.from_string(bracket_model.currency)
        bracket = TaxBracket(
            min_income=bracket_model.min_income,
            max_income=bracket_model.max_income,
            rate=bracket_model.rate,
            deduction=bracket_model.deduction,
            currency=currency
        )
        return TaxTable(
            id=bracket_model.id,
            currency=currency,
            effective_from=bracket_model.active_from,
            brackets=[bracket],
            provider=bracket_model.provider,
            is_active=True
        )

    def _brackets_to_table(
        self, currency: Currency, effective_from: date, bracket_models
    ) -> TaxTable:
        """Convert multiple bracket models to a single TaxTable."""
        brackets = []
        table_id = None

        for bm in bracket_models:
            if table_id is None:
                table_id = bm.id
            brackets.append(TaxBracket(
                min_income=bm.min_income,
                max_income=bm.max_income,
                rate=bm.rate,
                deduction=bm.deduction,
                currency=currency
            ))

        return TaxTable(
            id=table_id,
            currency=currency,
            effective_from=effective_from,
            brackets=brackets,
            provider=bracket_models[0].provider if bracket_models else None,
            is_active=True
        )
