"""
ExpenseClaim aggregate root.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from shared.domain.base import AggregateRoot
from modules.portal.domain.value_objects import ExpenseStatus


@dataclass
class ExpenseClaim(AggregateRoot[int]):
    """
    Expense claim submitted by an employee.

    Tracks expense reimbursement requests through the approval workflow.
    """

    employee_id: int
    category_id: int
    title: str
    description: str
    amount: Decimal
    currency: str
    date_incurred: date
    receipt_path: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        employee_id: int,
        category_id: int,
        title: str,
        description: str,
        amount: Decimal,
        currency: str = "USD",
        date_incurred: Optional[date] = None,
        receipt_path: Optional[str] = None,
    ) -> "ExpenseClaim":
        """Create a new expense claim."""
        if amount <= Decimal("0"):
            raise ValueError("Amount must be positive")
        if currency not in ("USD", "ZiG"):
            raise ValueError("Currency must be USD or ZiG")

        return cls(
            id=None,
            employee_id=employee_id,
            category_id=category_id,
            title=title,
            description=description,
            amount=amount,
            currency=currency,
            date_incurred=date_incurred or date.today(),
            receipt_path=receipt_path,
            status=ExpenseStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: Optional[str] = None,
        date_incurred: Optional[date] = None,
        receipt_path: Optional[str] = None,
    ) -> None:
        """Update claim details (only in draft status)."""
        if not self.status.can_edit:
            raise ValueError("Cannot edit claim that is not in draft status")

        if title:
            self.title = title
        if description:
            self.description = description
        if amount is not None:
            if amount <= Decimal("0"):
                raise ValueError("Amount must be positive")
            self.amount = amount
        if currency:
            if currency not in ("USD", "ZiG"):
                raise ValueError("Currency must be USD or ZiG")
            self.currency = currency
        if date_incurred:
            self.date_incurred = date_incurred
        if receipt_path is not None:
            self.receipt_path = receipt_path

        self.updated_at = datetime.now()

    def submit(self) -> None:
        """Submit the claim for review."""
        if not self.status.can_submit:
            raise ValueError("Claim cannot be submitted")

        self.status = ExpenseStatus.SUBMITTED
        self.submitted_at = datetime.now()
        self.updated_at = datetime.now()

    def start_review(self) -> None:
        """Mark claim as under review."""
        if self.status != ExpenseStatus.SUBMITTED:
            raise ValueError("Claim must be submitted to start review")

        self.status = ExpenseStatus.UNDER_REVIEW
        self.updated_at = datetime.now()

    def approve(self, reviewer_id: int, notes: Optional[str] = None) -> None:
        """Approve the expense claim."""
        if self.status not in (ExpenseStatus.SUBMITTED, ExpenseStatus.UNDER_REVIEW):
            raise ValueError("Claim must be submitted or under review to approve")

        self.status = ExpenseStatus.APPROVED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.now()
        self.review_notes = notes
        self.updated_at = datetime.now()

    def reject(self, reviewer_id: int, reason: str) -> None:
        """Reject the expense claim."""
        if self.status not in (ExpenseStatus.SUBMITTED, ExpenseStatus.UNDER_REVIEW):
            raise ValueError("Claim must be submitted or under review to reject")

        self.status = ExpenseStatus.REJECTED
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.now()
        self.review_notes = reason
        self.updated_at = datetime.now()

    def mark_paid(self, payment_reference: Optional[str] = None) -> None:
        """Mark the claim as paid."""
        if self.status != ExpenseStatus.APPROVED:
            raise ValueError("Claim must be approved to mark as paid")

        self.status = ExpenseStatus.PAID
        self.paid_at = datetime.now()
        self.payment_reference = payment_reference
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the expense claim."""
        if not self.status.can_cancel:
            raise ValueError("Cannot cancel claim in current status")

        self.status = ExpenseStatus.DRAFT
        self.submitted_at = None
        self.updated_at = datetime.now()
