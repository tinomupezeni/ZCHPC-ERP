"""
API serializers for the accounts module.
"""

from decimal import Decimal
from rest_framework import serializers


# ============================
# Account Serializers
# ============================

class AccountSerializer(serializers.Serializer):
    """Serializer for account display."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    account_type = serializers.CharField()
    parent_id = serializers.IntegerField(allow_null=True)
    currency_id = serializers.IntegerField(allow_null=True)
    is_reconcilable = serializers.BooleanField()
    is_active = serializers.BooleanField()
    description = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateAccountSerializer(serializers.Serializer):
    """Serializer for creating an account."""

    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    account_type = serializers.ChoiceField(choices=[
        "Asset", "Liability", "Equity", "Revenue", "Expense", "View", "Consolidation"
    ])
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    currency_id = serializers.IntegerField(required=False, allow_null=True)
    is_reconcilable = serializers.BooleanField(default=False)
    description = serializers.CharField(required=False, allow_null=True)


class UpdateAccountSerializer(serializers.Serializer):
    """Serializer for updating an account."""

    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_null=True)
    is_reconcilable = serializers.BooleanField(required=False)
    currency_id = serializers.IntegerField(required=False, allow_null=True)


class ChartOfAccountsSerializer(serializers.Serializer):
    """Serializer for hierarchical chart of accounts."""

    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    account_type = serializers.CharField()
    is_active = serializers.BooleanField()
    children = serializers.ListField(child=serializers.DictField())


# ============================
# Currency Serializers
# ============================

class CurrencySerializer(serializers.Serializer):
    """Serializer for currency display."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    symbol = serializers.CharField(allow_null=True)
    rate_to_base = serializers.DecimalField(max_digits=18, decimal_places=6)
    is_base = serializers.BooleanField()
    is_active = serializers.BooleanField()


class CreateCurrencySerializer(serializers.Serializer):
    """Serializer for creating a currency."""

    code = serializers.CharField(max_length=8)
    name = serializers.CharField(max_length=32)
    symbol = serializers.CharField(max_length=8, required=False, allow_null=True)
    rate_to_base = serializers.DecimalField(
        max_digits=18, decimal_places=6, default=Decimal("1")
    )
    is_base = serializers.BooleanField(default=False)


class UpdateCurrencyRateSerializer(serializers.Serializer):
    """Serializer for updating currency rate."""

    rate_to_base = serializers.DecimalField(max_digits=18, decimal_places=6)


# ============================
# Journal Serializers
# ============================

class JournalSerializer(serializers.Serializer):
    """Serializer for journal display."""

    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    journal_type = serializers.CharField()
    default_debit_account_id = serializers.IntegerField(allow_null=True)
    default_credit_account_id = serializers.IntegerField(allow_null=True)
    currency_id = serializers.IntegerField(allow_null=True)
    is_active = serializers.BooleanField()


class CreateJournalSerializer(serializers.Serializer):
    """Serializer for creating a journal."""

    code = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=255)
    journal_type = serializers.ChoiceField(choices=[
        "Sale", "Purchase", "Cash", "Bank", "General"
    ])
    default_debit_account_id = serializers.IntegerField(required=False, allow_null=True)
    default_credit_account_id = serializers.IntegerField(required=False, allow_null=True)
    currency_id = serializers.IntegerField(required=False, allow_null=True)


# ============================
# Journal Entry Serializers
# ============================

class JournalEntryLineSerializer(serializers.Serializer):
    """Serializer for journal entry line."""

    id = serializers.IntegerField(read_only=True)
    account_id = serializers.IntegerField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    credit = serializers.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    partner_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)


class JournalEntrySerializer(serializers.Serializer):
    """Serializer for journal entry display."""

    id = serializers.IntegerField(read_only=True)
    journal_id = serializers.IntegerField()
    entry_date = serializers.DateField()
    reference = serializers.CharField(allow_null=True)
    narration = serializers.CharField(allow_null=True)
    is_posted = serializers.BooleanField()
    total_debit = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    is_balanced = serializers.BooleanField(read_only=True)
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateJournalEntrySerializer(serializers.Serializer):
    """Serializer for creating a journal entry."""

    journal_id = serializers.IntegerField()
    entry_date = serializers.DateField()
    reference = serializers.CharField(required=False, allow_null=True)
    narration = serializers.CharField(required=False, allow_null=True)
    lines = JournalEntryLineSerializer(many=True)
    auto_post = serializers.BooleanField(default=False)


class UpdateJournalEntrySerializer(serializers.Serializer):
    """Serializer for updating a journal entry."""

    reference = serializers.CharField(required=False, allow_null=True)
    narration = serializers.CharField(required=False, allow_null=True)
    entry_date = serializers.DateField(required=False)


class AddEntryLineSerializer(serializers.Serializer):
    """Serializer for adding a line to an entry."""

    account_id = serializers.IntegerField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    credit = serializers.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    partner_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)


class CreateReversingEntrySerializer(serializers.Serializer):
    """Serializer for creating a reversing entry."""

    reversal_date = serializers.DateField()
    reference = serializers.CharField(required=False, allow_null=True)


# ============================
# Partner Serializers
# ============================

class PartnerSerializer(serializers.Serializer):
    """Serializer for partner display."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    partner_type = serializers.CharField()
    vat_number = serializers.CharField(allow_null=True)
    currency_id = serializers.IntegerField(allow_null=True)
    email = serializers.CharField(allow_null=True)
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField(allow_null=True)
    is_active = serializers.BooleanField()


class CreatePartnerSerializer(serializers.Serializer):
    """Serializer for creating a partner."""

    name = serializers.CharField(max_length=255)
    partner_type = serializers.ChoiceField(choices=["Customer", "Supplier", "Employee"])
    vat_number = serializers.CharField(max_length=64, required=False, allow_null=True)
    currency_id = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.CharField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_null=True)


# ============================
# Report Serializers
# ============================

class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance."""

    account_id = serializers.IntegerField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    debit_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance = serializers.DecimalField(max_digits=18, decimal_places=2)


class TrialBalanceItemSerializer(serializers.Serializer):
    """Serializer for trial balance item."""

    account_code = serializers.CharField()
    account_name = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)


class TrialBalanceSerializer(serializers.Serializer):
    """Serializer for trial balance report."""

    as_of_date = serializers.DateField()
    items = TrialBalanceItemSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    is_balanced = serializers.BooleanField()


class ProfitLossSerializer(serializers.Serializer):
    """Serializer for P&L report."""

    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=18, decimal_places=2)
    is_profitable = serializers.BooleanField()
    revenue_items = AccountBalanceSerializer(many=True, source="revenue_section.items")
    expense_items = AccountBalanceSerializer(many=True, source="expense_section.items")


class BalanceSheetSerializer(serializers.Serializer):
    """Serializer for balance sheet report."""

    as_of_date = serializers.DateField()
    total_assets = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_equity = serializers.DecimalField(max_digits=18, decimal_places=2)
    retained_earnings = serializers.DecimalField(max_digits=18, decimal_places=2)
    is_balanced = serializers.BooleanField()
    asset_items = AccountBalanceSerializer(many=True, source="assets_section.items")
    liability_items = AccountBalanceSerializer(many=True, source="liabilities_section.items")
    equity_items = AccountBalanceSerializer(many=True, source="equity_section.items")


class GeneralLedgerEntrySerializer(serializers.Serializer):
    """Serializer for general ledger entry."""

    entry_date = serializers.DateField()
    reference = serializers.CharField()
    description = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    running_balance = serializers.DecimalField(max_digits=18, decimal_places=2)


class GeneralLedgerSerializer(serializers.Serializer):
    """Serializer for general ledger report."""

    account_id = serializers.IntegerField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    opening_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    entries = GeneralLedgerEntrySerializer(many=True)
    closing_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
