"""
PurchaseRequestCategory aggregate root.
"""

from dataclasses import dataclass
from datetime import datetime

from shared.domain.base import AggregateRoot
from shared.domain.exceptions import ValidationError


@dataclass
class PurchaseRequestCategory(AggregateRoot[int]):
    """
    An employee-facing Purchase Request category.

    Maps a plain-language label an employee can choose (e.g. "IT
    Consumables") onto exactly one AccountChart row via account_chart_id.
    AccountChart itself is not duplicated here - code, name and
    external_account_type stay owned by the accounts module; this entity
    carries only the id needed to resolve a category to a budget_code_id.

    See modules.procurement.infrastructure.persistence.models
    .PurchaseRequestCategory for the persistence-level rationale (why this
    is Finance-curated rather than inferred, and why the FK is one-to-one).
    """

    name: str
    account_chart_id: int
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not hasattr(self, "_id"):
            self._id = None
        if not self.name or not self.name.strip():
            raise ValidationError("Category name must not be empty")
