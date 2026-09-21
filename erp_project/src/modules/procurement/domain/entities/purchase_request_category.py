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

    A plain-language label an employee can choose (e.g. "IT Hardware &
    Accessories"). F25: purely descriptive - it does not resolve to a GL
    account. account_chart_id is optional legacy data from F11-A and is None
    for every newer category; the authoritative accounting code is assigned
    by Accounts per item.

    See modules.procurement.infrastructure.persistence.models
    .PurchaseRequestCategory for the persistence-level rationale (why this
    is Finance-curated rather than inferred, and why the FK is one-to-one).
    """

    name: str
    account_chart_id: int | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not hasattr(self, "_id"):
            self._id = None
        if not self.name or not self.name.strip():
            raise ValidationError("Category name must not be empty")
