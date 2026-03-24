"""
Application service for account management.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.accounts.domain.entities import Account, JournalEntry, JournalEntryLine
from modules.accounts.domain.value_objects import AccountType
from modules.accounts.domain.events import AccountCreated, AccountDeactivated
from modules.accounts.application.interfaces import (
    IAccountRepository,
    IJournalEntryRepository,
)


@dataclass
class CreateAccountDTO:
    """DTO for creating an account."""

    code: str
    name: str
    account_type: str
    parent_id: Optional[int] = None
    currency_id: Optional[int] = None
    is_reconcilable: bool = False
    description: Optional[str] = None


@dataclass
class UpdateAccountDTO:
    """DTO for updating an account."""

    name: Optional[str] = None
    description: Optional[str] = None
    is_reconcilable: Optional[bool] = None
    currency_id: Optional[int] = None


class AccountService:
    """
    Application service for managing accounts.

    Coordinates account operations and enforces business rules.
    """

    def __init__(
        self,
        account_repo: IAccountRepository,
        entry_repo: IJournalEntryRepository
    ) -> None:
        self._account_repo = account_repo
        self._entry_repo = entry_repo

    def create_account(self, dto: CreateAccountDTO) -> Account:
        """
        Create a new account.

        Args:
            dto: Account creation data

        Returns:
            Created account

        Raises:
            ValidationError: If account code already exists
        """
        # Check for duplicate code
        if self._account_repo.exists_by_code(dto.code):
            raise ValidationError(f"Account with code '{dto.code}' already exists")

        # Validate parent exists if specified
        if dto.parent_id is not None:
            parent = self._account_repo.get_by_id(dto.parent_id)
            if parent is None:
                raise NotFoundError(f"Parent account {dto.parent_id} not found")

        # Parse account type
        try:
            account_type = AccountType(dto.account_type)
        except ValueError:
            raise ValidationError(f"Invalid account type: {dto.account_type}")

        # Create account
        account = Account.create(
            code=dto.code,
            name=dto.name,
            account_type=account_type,
            parent_id=dto.parent_id,
            currency_id=dto.currency_id,
            is_reconcilable=dto.is_reconcilable,
            description=dto.description
        )

        # Save
        saved_account = self._account_repo.save(account)

        return saved_account

    def update_account(
        self,
        account_id: int,
        dto: UpdateAccountDTO
    ) -> Account:
        """
        Update an existing account.

        Args:
            account_id: ID of account to update
            dto: Update data

        Returns:
            Updated account
        """
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        account.update_details(
            name=dto.name,
            description=dto.description,
            is_reconcilable=dto.is_reconcilable,
            currency_id=dto.currency_id
        )

        return self._account_repo.save(account)

    def deactivate_account(self, account_id: int) -> Account:
        """
        Deactivate an account.

        Args:
            account_id: ID of account to deactivate

        Returns:
            Deactivated account

        Raises:
            ValidationError: If account has children or posted entries
        """
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        # Check for children
        children = self._account_repo.get_children(account_id)
        if children:
            raise ValidationError(
                "Cannot deactivate account with child accounts"
            )

        # Check for posted entries
        posted_lines = self._entry_repo.get_posted_lines_for_account(account_id)
        if posted_lines:
            raise ValidationError(
                "Cannot deactivate account with posted entries"
            )

        account.deactivate()
        return self._account_repo.save(account)

    def activate_account(self, account_id: int) -> Account:
        """Activate a deactivated account."""
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        account.activate()
        return self._account_repo.save(account)

    def get_account(self, account_id: int) -> Account:
        """Get an account by ID."""
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")
        return account

    def get_account_by_code(self, code: str) -> Account:
        """Get an account by code."""
        account = self._account_repo.get_by_code(code)
        if account is None:
            raise NotFoundError(f"Account with code '{code}' not found")
        return account

    def list_accounts(
        self,
        account_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Account]:
        """
        List accounts with optional filtering.

        Args:
            account_type: Optional type filter
            include_inactive: Include inactive accounts

        Returns:
            List of accounts
        """
        if account_type:
            try:
                parsed_type = AccountType(account_type)
                return self._account_repo.get_by_type(
                    parsed_type,
                    include_inactive=include_inactive
                )
            except ValueError:
                raise ValidationError(f"Invalid account type: {account_type}")

        return self._account_repo.get_all(include_inactive=include_inactive)

    def get_chart_of_accounts(self) -> List[dict]:
        """
        Get hierarchical chart of accounts.

        Returns:
            List of account trees with children nested
        """
        all_accounts = self._account_repo.get_all()

        # Build a map of parent_id to children
        children_map: dict[Optional[int], List[Account]] = {}
        for account in all_accounts:
            parent_id = account.parent_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(account)

        def build_tree(parent_id: Optional[int]) -> List[dict]:
            result = []
            for account in sorted(
                children_map.get(parent_id, []),
                key=lambda a: a.code
            ):
                node = {
                    "id": account.id,
                    "code": account.code,
                    "name": account.name,
                    "account_type": account.account_type.value,
                    "is_active": account.is_active,
                    "children": build_tree(account.id)
                }
                result.append(node)
            return result

        return build_tree(None)

    def move_account(
        self,
        account_id: int,
        new_parent_id: Optional[int]
    ) -> Account:
        """
        Move an account to a new parent.

        Args:
            account_id: ID of account to move
            new_parent_id: New parent ID (None for root)

        Returns:
            Updated account
        """
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found")

        if new_parent_id is not None:
            parent = self._account_repo.get_by_id(new_parent_id)
            if parent is None:
                raise NotFoundError(f"Parent account {new_parent_id} not found")

            # Prevent circular reference
            if self._would_create_cycle(account_id, new_parent_id):
                raise ValidationError("Moving account would create a cycle")

        account.move_to_parent(new_parent_id)
        return self._account_repo.save(account)

    def _would_create_cycle(
        self,
        account_id: int,
        new_parent_id: int
    ) -> bool:
        """Check if moving would create a cycle."""
        # Check if new_parent_id is a descendant of account_id
        current = new_parent_id
        while current is not None:
            if current == account_id:
                return True
            parent = self._account_repo.get_by_id(current)
            if parent is None:
                break
            current = parent.parent_id
        return False
