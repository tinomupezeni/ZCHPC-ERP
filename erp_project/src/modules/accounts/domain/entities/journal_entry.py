"""
JournalEntry aggregate root with entry lines.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot, Entity
from shared.domain.exceptions import ValidationError
from modules.accounts.domain.value_objects import DebitCredit


@dataclass
class JournalEntryLine(Entity[int]):
    """
    Entity representing a line in a journal entry.

    Each line debits or credits a specific account.
    """

    entry_id: Optional[int]
    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    partner_id: Optional[int] = None
    currency_id: Optional[int] = None
    amount_currency: Optional[Decimal] = None
    analytic_account_id: Optional[int] = None
    description: Optional[str] = None
    line_date: Optional[date] = None

    def __post_init__(self) -> None:
        """Validate entry line."""
        if self.debit < 0:
            raise ValidationError("Debit cannot be negative")
        if self.credit < 0:
            raise ValidationError("Credit cannot be negative")
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Line cannot have both debit and credit")

    @property
    def balance(self) -> Decimal:
        """Get line balance (debit - credit)."""
        return self.debit - self.credit

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit line."""
        return self.debit > 0

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit line."""
        return self.credit > 0

    @classmethod
    def create_debit(
        cls,
        account_id: int,
        amount: Decimal,
        partner_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> "JournalEntryLine":
        """Create a debit line."""
        return cls(
            id=None,
            entry_id=None,
            account_id=account_id,
            debit=amount,
            credit=Decimal("0"),
            partner_id=partner_id,
            description=description
        )

    @classmethod
    def create_credit(
        cls,
        account_id: int,
        amount: Decimal,
        partner_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> "JournalEntryLine":
        """Create a credit line."""
        return cls(
            id=None,
            entry_id=None,
            account_id=account_id,
            debit=Decimal("0"),
            credit=amount,
            partner_id=partner_id,
            description=description
        )


@dataclass
class JournalEntry(AggregateRoot[int]):
    """
    Aggregate root for journal entries.

    Represents a complete journal entry with multiple lines.
    Enforces double-entry bookkeeping (debits must equal credits).
    """

    journal_id: int
    entry_date: date
    reference: Optional[str] = None
    narration: Optional[str] = None
    is_posted: bool = False
    lines: List[JournalEntryLine] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def total_debit(self) -> Decimal:
        """Sum of all debit amounts."""
        return sum((line.debit for line in self.lines), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        """Sum of all credit amounts."""
        return sum((line.credit for line in self.lines), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        """Check if debits equal credits."""
        return self.total_debit == self.total_credit

    @property
    def balance_difference(self) -> Decimal:
        """Get the difference between debits and credits."""
        return self.total_debit - self.total_credit

    def add_line(self, line: JournalEntryLine) -> None:
        """Add a line to the entry."""
        if self.is_posted:
            raise ValidationError("Cannot modify a posted entry")
        line.entry_id = self.id
        self.lines.append(line)

    def add_debit(
        self,
        account_id: int,
        amount: Decimal,
        partner_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> None:
        """Add a debit line."""
        line = JournalEntryLine.create_debit(
            account_id=account_id,
            amount=amount,
            partner_id=partner_id,
            description=description
        )
        self.add_line(line)

    def add_credit(
        self,
        account_id: int,
        amount: Decimal,
        partner_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> None:
        """Add a credit line."""
        line = JournalEntryLine.create_credit(
            account_id=account_id,
            amount=amount,
            partner_id=partner_id,
            description=description
        )
        self.add_line(line)

    def remove_line(self, line_id: int) -> bool:
        """Remove a line by ID."""
        if self.is_posted:
            raise ValidationError("Cannot modify a posted entry")
        for i, line in enumerate(self.lines):
            if line.id == line_id:
                self.lines.pop(i)
                return True
        return False

    def clear_lines(self) -> None:
        """Remove all lines."""
        if self.is_posted:
            raise ValidationError("Cannot modify a posted entry")
        self.lines.clear()

    def validate(self) -> None:
        """Validate the entry before posting."""
        if not self.lines:
            raise ValidationError("Journal entry must have at least one line")
        if not self.is_balanced:
            raise ValidationError(
                f"Entry is not balanced. Difference: {self.balance_difference}"
            )
        # Check that at least one debit and one credit exist
        has_debit = any(line.is_debit for line in self.lines)
        has_credit = any(line.is_credit for line in self.lines)
        if not (has_debit and has_credit):
            raise ValidationError(
                "Entry must have at least one debit and one credit line"
            )

    def post(self) -> None:
        """Post the journal entry."""
        if self.is_posted:
            raise ValidationError("Entry is already posted")
        self.validate()
        self.is_posted = True
        self.updated_at = datetime.now()

    def unpost(self) -> None:
        """Unpost the journal entry (reverse posting)."""
        if not self.is_posted:
            raise ValidationError("Entry is not posted")
        self.is_posted = False
        self.updated_at = datetime.now()

    def update_details(
        self,
        reference: Optional[str] = None,
        narration: Optional[str] = None,
        entry_date: Optional[date] = None
    ) -> None:
        """Update entry details."""
        if self.is_posted:
            raise ValidationError("Cannot modify a posted entry")
        if reference is not None:
            self.reference = reference
        if narration is not None:
            self.narration = narration
        if entry_date is not None:
            self.entry_date = entry_date
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        journal_id: int,
        entry_date: date,
        reference: Optional[str] = None,
        narration: Optional[str] = None
    ) -> "JournalEntry":
        """Factory method to create a journal entry."""
        now = datetime.now()
        return cls(
            id=None,
            journal_id=journal_id,
            entry_date=entry_date,
            reference=reference,
            narration=narration,
            is_posted=False,
            lines=[],
            created_at=now,
            updated_at=now
        )
