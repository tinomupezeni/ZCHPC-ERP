"""
Which AccountChart rows Accounts may assign as a Purchase Request budget code.

Finance-confirmed: only rows whose external_account_type (the type exactly as
exported by the external accounting system) is one of these. This is NOT the
internal structural AccountChart.account_type field (view/regular/
consolidation), which is unrelated.
"""

from dataclasses import dataclass

ALLOWED_BUDGET_CODE_EXTERNAL_TYPES: frozenset[str] = frozenset(
    {"Revenue", "Other Income", "Other Expense"}
)


@dataclass(frozen=True)
class BudgetCode:
    """A read-only view of an assignable AccountChart row."""

    id: int
    code: str
    name: str
    external_account_type: str
