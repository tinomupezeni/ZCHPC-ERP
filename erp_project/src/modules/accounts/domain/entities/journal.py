"""
Journal aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.accounts.domain.value_objects import JournalType


@dataclass
class Journal(AggregateRoot[int]):
    """
    Aggregate root for journals.

    Represents a journal for categorizing transactions (sales, purchases, etc.).
    """

    code: str
    name: str
    journal_type: JournalType
    default_debit_account_id: Optional[int] = None
    default_credit_account_id: Optional[int] = None
    currency_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate journal."""
        if not self.code or not self.code.strip():
            raise ValidationError("Journal code is required")
        if not self.name or not self.name.strip():
            raise ValidationError("Journal name is required")

    def update_details(
        self,
        name: Optional[str] = None,
        default_debit_account_id: Optional[int] = None,
        default_credit_account_id: Optional[int] = None,
        currency_id: Optional[int] = None
    ) -> None:
        """Update journal details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Journal name cannot be empty")
            self.name = name.strip()
        if default_debit_account_id is not None:
            self.default_debit_account_id = default_debit_account_id
        if default_credit_account_id is not None:
            self.default_credit_account_id = default_credit_account_id
        if currency_id is not None:
            self.currency_id = currency_id
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate this journal."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this journal."""
        self.is_active = True
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        journal_type: JournalType,
        default_debit_account_id: Optional[int] = None,
        default_credit_account_id: Optional[int] = None,
        currency_id: Optional[int] = None
    ) -> "Journal":
        """Factory method to create a journal."""
        now = datetime.now()
        return cls(
            id=None,
            code=code.upper(),
            name=name,
            journal_type=journal_type,
            default_debit_account_id=default_debit_account_id,
            default_credit_account_id=default_credit_account_id,
            currency_id=currency_id,
            is_active=True,
            created_at=now,
            updated_at=now
        )
