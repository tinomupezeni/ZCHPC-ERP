"""
Account aggregate root for chart of accounts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError
from modules.accounts.domain.value_objects import AccountCode, AccountType


@dataclass
class Account(AggregateRoot[int]):
    """
    Aggregate root for chart of accounts.

    Represents an account in the hierarchical chart of accounts.
    Supports parent-child relationships for account grouping.
    """

    code: str
    name: str
    account_type: AccountType
    parent_id: Optional[int] = None
    currency_id: Optional[int] = None
    is_reconcilable: bool = False
    is_active: bool = True
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate account."""
        if not self.code or not self.code.strip():
            raise ValidationError("Account code is required")
        if not self.name or not self.name.strip():
            raise ValidationError("Account name is required")

    @property
    def account_code(self) -> AccountCode:
        """Get as AccountCode value object."""
        return AccountCode(value=self.code)

    @property
    def is_posting_account(self) -> bool:
        """Check if this account allows posting entries."""
        return self.account_type.is_posting

    @property
    def normal_balance(self) -> str:
        """Get the normal balance side for this account."""
        return self.account_type.normal_balance

    def can_post_entry(self) -> bool:
        """Check if entries can be posted to this account."""
        return self.is_posting_account and self.is_active

    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_reconcilable: Optional[bool] = None,
        currency_id: Optional[int] = None
    ) -> None:
        """Update account details."""
        if name is not None:
            if not name.strip():
                raise ValidationError("Account name cannot be empty")
            self.name = name.strip()
        if description is not None:
            self.description = description
        if is_reconcilable is not None:
            self.is_reconcilable = is_reconcilable
        if currency_id is not None:
            self.currency_id = currency_id
        self.updated_at = datetime.now()

    def move_to_parent(self, new_parent_id: Optional[int]) -> None:
        """Move this account under a new parent."""
        if new_parent_id == self.id:
            raise ValidationError("Account cannot be its own parent")
        self.parent_id = new_parent_id
        self.updated_at = datetime.now()

    def deactivate(self) -> None:
        """Deactivate this account."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Activate this account."""
        self.is_active = True
        self.updated_at = datetime.now()

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        account_type: AccountType,
        parent_id: Optional[int] = None,
        currency_id: Optional[int] = None,
        is_reconcilable: bool = False,
        description: Optional[str] = None
    ) -> "Account":
        """Factory method to create an account."""
        now = datetime.now()
        return cls(
            id=None,
            code=code,
            name=name,
            account_type=account_type,
            parent_id=parent_id,
            currency_id=currency_id,
            is_reconcilable=is_reconcilable,
            is_active=True,
            description=description,
            created_at=now,
            updated_at=now
        )

    @classmethod
    def create_view_account(
        cls,
        code: str,
        name: str,
        parent_id: Optional[int] = None
    ) -> "Account":
        """Create a non-posting view account for grouping."""
        return cls.create(
            code=code,
            name=name,
            account_type=AccountType.VIEW,
            parent_id=parent_id,
            is_reconcilable=False
        )
