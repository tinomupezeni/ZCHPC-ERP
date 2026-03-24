"""
Tests for accounts domain entities.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from shared.domain.exceptions import ValidationError
from modules.accounts.domain.entities import (
    Account,
    Currency,
    Journal,
    JournalEntry,
    JournalEntryLine,
    Partner,
)
from modules.accounts.domain.value_objects import (
    AccountType,
    JournalType,
    PartnerType,
)


class TestCurrency:
    """Tests for Currency aggregate."""

    def test_create_currency(self):
        currency = Currency.create(
            code="USD",
            name="US Dollar",
            symbol="$",
            rate_to_base=Decimal("1"),
            is_base=True
        )
        assert currency.code == "USD"
        assert currency.name == "US Dollar"
        assert currency.symbol == "$"
        assert currency.is_base is True

    def test_code_is_uppercase(self):
        currency = Currency.create(code="usd", name="US Dollar")
        assert currency.code == "USD"

    def test_invalid_code_raises(self):
        with pytest.raises(ValidationError):
            Currency(
                id=None,
                code="",
                name="Test",
                rate_to_base=Decimal("1")
            )

    def test_invalid_rate_raises(self):
        with pytest.raises(ValidationError):
            Currency(
                id=None,
                code="USD",
                name="US Dollar",
                rate_to_base=Decimal("-1")
            )

    def test_update_rate(self):
        currency = Currency.create(code="ZIG", name="Zimbabwe Gold")
        currency.update_rate(Decimal("25.50"))
        assert currency.rate_to_base == Decimal("25.50")

    def test_cannot_update_base_rate(self):
        currency = Currency.create(code="USD", name="US Dollar", is_base=True)
        with pytest.raises(ValidationError):
            currency.update_rate(Decimal("2"))

    def test_convert_to_base(self):
        currency = Currency.create(
            code="ZIG",
            name="Zimbabwe Gold",
            rate_to_base=Decimal("25")
        )
        result = currency.convert_to_base(Decimal("100"))
        assert result == Decimal("2500.00")

    def test_convert_from_base(self):
        currency = Currency.create(
            code="ZIG",
            name="Zimbabwe Gold",
            rate_to_base=Decimal("25")
        )
        result = currency.convert_from_base(Decimal("2500"))
        assert result == Decimal("100.00")


class TestAccount:
    """Tests for Account aggregate."""

    def test_create_account(self):
        account = Account.create(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET
        )
        assert account.code == "1000"
        assert account.name == "Cash"
        assert account.account_type == AccountType.ASSET

    def test_invalid_code_raises(self):
        with pytest.raises(ValidationError):
            Account(
                id=None,
                code="",
                name="Test",
                account_type=AccountType.ASSET
            )

    def test_invalid_name_raises(self):
        with pytest.raises(ValidationError):
            Account(
                id=None,
                code="1000",
                name="",
                account_type=AccountType.ASSET
            )

    def test_is_posting_account(self):
        posting = Account.create(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET
        )
        view = Account.create(
            code="0000",
            name="Assets Group",
            account_type=AccountType.VIEW
        )
        assert posting.is_posting_account is True
        assert view.is_posting_account is False

    def test_can_post_entry(self):
        account = Account.create(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET
        )
        assert account.can_post_entry() is True

        account.deactivate()
        assert account.can_post_entry() is False

    def test_update_details(self):
        account = Account.create(
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET
        )
        account.update_details(
            name="Cash and Cash Equivalents",
            description="All cash accounts"
        )
        assert account.name == "Cash and Cash Equivalents"
        assert account.description == "All cash accounts"

    def test_move_to_parent(self):
        account = Account.create(
            code="1100",
            name="Bank",
            account_type=AccountType.ASSET
        )
        account.move_to_parent(1)
        assert account.parent_id == 1

    def test_cannot_be_own_parent(self):
        account = Account(
            id=1,
            code="1000",
            name="Cash",
            account_type=AccountType.ASSET
        )
        with pytest.raises(ValidationError):
            account.move_to_parent(1)

    def test_create_view_account(self):
        account = Account.create_view_account(
            code="0000",
            name="Root"
        )
        assert account.account_type == AccountType.VIEW
        assert account.is_posting_account is False


class TestJournal:
    """Tests for Journal aggregate."""

    def test_create_journal(self):
        journal = Journal.create(
            code="SALES",
            name="Sales Journal",
            journal_type=JournalType.SALE
        )
        assert journal.code == "SALES"
        assert journal.name == "Sales Journal"
        assert journal.journal_type == JournalType.SALE

    def test_code_is_uppercase(self):
        journal = Journal.create(
            code="sales",
            name="Sales Journal",
            journal_type=JournalType.SALE
        )
        assert journal.code == "SALES"

    def test_invalid_code_raises(self):
        with pytest.raises(ValidationError):
            Journal(
                id=None,
                code="",
                name="Test",
                journal_type=JournalType.GENERAL
            )

    def test_update_details(self):
        journal = Journal.create(
            code="SALES",
            name="Sales",
            journal_type=JournalType.SALE
        )
        journal.update_details(name="Sales Journal")
        assert journal.name == "Sales Journal"


class TestJournalEntryLine:
    """Tests for JournalEntryLine entity."""

    def test_create_debit_line(self):
        line = JournalEntryLine.create_debit(
            account_id=1,
            amount=Decimal("100.00"),
            description="Test debit"
        )
        assert line.debit == Decimal("100.00")
        assert line.credit == Decimal("0")
        assert line.is_debit is True
        assert line.is_credit is False

    def test_create_credit_line(self):
        line = JournalEntryLine.create_credit(
            account_id=2,
            amount=Decimal("100.00"),
            description="Test credit"
        )
        assert line.debit == Decimal("0")
        assert line.credit == Decimal("100.00")
        assert line.is_credit is True
        assert line.is_debit is False

    def test_balance_debit(self):
        line = JournalEntryLine.create_debit(
            account_id=1,
            amount=Decimal("100.00")
        )
        assert line.balance == Decimal("100.00")

    def test_balance_credit(self):
        line = JournalEntryLine.create_credit(
            account_id=1,
            amount=Decimal("100.00")
        )
        assert line.balance == Decimal("-100.00")

    def test_negative_debit_raises(self):
        with pytest.raises(ValidationError):
            JournalEntryLine(
                id=None,
                entry_id=None,
                account_id=1,
                debit=Decimal("-100"),
                credit=Decimal("0")
            )

    def test_negative_credit_raises(self):
        with pytest.raises(ValidationError):
            JournalEntryLine(
                id=None,
                entry_id=None,
                account_id=1,
                debit=Decimal("0"),
                credit=Decimal("-100")
            )

    def test_both_debit_and_credit_raises(self):
        with pytest.raises(ValidationError):
            JournalEntryLine(
                id=None,
                entry_id=None,
                account_id=1,
                debit=Decimal("100"),
                credit=Decimal("100")
            )


class TestJournalEntry:
    """Tests for JournalEntry aggregate."""

    def test_create_entry(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15),
            reference="INV-001",
            narration="Test entry"
        )
        assert entry.journal_id == 1
        assert entry.entry_date == date(2024, 1, 15)
        assert entry.reference == "INV-001"
        assert entry.is_posted is False

    def test_add_debit_line(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(
            account_id=1,
            amount=Decimal("100.00"),
            description="Debit cash"
        )
        assert len(entry.lines) == 1
        assert entry.total_debit == Decimal("100.00")

    def test_add_credit_line(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_credit(
            account_id=2,
            amount=Decimal("100.00"),
            description="Credit revenue"
        )
        assert len(entry.lines) == 1
        assert entry.total_credit == Decimal("100.00")

    def test_is_balanced(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        assert entry.is_balanced is True

    def test_is_not_balanced(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("50.00"))
        assert entry.is_balanced is False
        assert entry.balance_difference == Decimal("50.00")

    def test_validate_balanced_entry(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        # Should not raise
        entry.validate()

    def test_validate_unbalanced_entry_raises(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("50.00"))
        with pytest.raises(ValidationError):
            entry.validate()

    def test_validate_empty_entry_raises(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        with pytest.raises(ValidationError):
            entry.validate()

    def test_validate_only_debits_raises(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_debit(account_id=2, amount=Decimal("-100.00"))  # Not allowed anyway
        # But even with balanced zeros, need both debit and credit
        entry2 = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry2.add_debit(account_id=1, amount=Decimal("100.00"))
        with pytest.raises(ValidationError):
            entry2.validate()

    def test_post_entry(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        entry.post()
        assert entry.is_posted is True

    def test_post_already_posted_raises(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        entry.post()
        with pytest.raises(ValidationError):
            entry.post()

    def test_unpost_entry(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        entry.post()
        entry.unpost()
        assert entry.is_posted is False

    def test_cannot_modify_posted_entry(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.add_credit(account_id=2, amount=Decimal("100.00"))
        entry.post()

        with pytest.raises(ValidationError):
            entry.add_debit(account_id=3, amount=Decimal("50.00"))

    def test_remove_line(self):
        entry = JournalEntry.create(
            journal_id=1,
            entry_date=date(2024, 1, 15)
        )
        entry.add_debit(account_id=1, amount=Decimal("100.00"))
        entry.lines[0].id = 1
        result = entry.remove_line(1)
        assert result is True
        assert len(entry.lines) == 0


class TestPartner:
    """Tests for Partner aggregate."""

    def test_create_customer(self):
        partner = Partner.create_customer(
            name="Acme Corp",
            vat_number="VAT123"
        )
        assert partner.name == "Acme Corp"
        assert partner.partner_type == PartnerType.CUSTOMER
        assert partner.is_customer is True

    def test_create_supplier(self):
        partner = Partner.create_supplier(
            name="Supplier Inc"
        )
        assert partner.partner_type == PartnerType.SUPPLIER
        assert partner.is_supplier is True

    def test_create_with_type(self):
        partner = Partner.create(
            name="John Doe",
            partner_type=PartnerType.EMPLOYEE
        )
        assert partner.is_employee is True

    def test_invalid_name_raises(self):
        with pytest.raises(ValidationError):
            Partner(
                id=None,
                name="",
                partner_type=PartnerType.CUSTOMER
            )

    def test_update_details(self):
        partner = Partner.create_customer(name="Acme")
        partner.update_details(
            name="Acme Corporation",
            email="contact@acme.com",
            phone="123-456-7890"
        )
        assert partner.name == "Acme Corporation"
        assert partner.email == "contact@acme.com"
        assert partner.phone == "123-456-7890"

    def test_change_type(self):
        partner = Partner.create_customer(name="Test")
        partner.change_type(PartnerType.SUPPLIER)
        assert partner.partner_type == PartnerType.SUPPLIER
        assert partner.is_supplier is True
        assert partner.is_customer is False

    def test_deactivate(self):
        partner = Partner.create_customer(name="Test")
        assert partner.is_active is True
        partner.deactivate()
        assert partner.is_active is False

    def test_activate(self):
        partner = Partner.create_customer(name="Test")
        partner.deactivate()
        partner.activate()
        assert partner.is_active is True
