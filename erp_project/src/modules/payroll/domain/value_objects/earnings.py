"""
Earnings value object for payroll calculations.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from shared.domain.base import ValueObject


@dataclass(frozen=True)
class AllowanceItem(ValueObject):
    """Individual allowance item."""

    name: str
    amount_usd: Decimal = Decimal("0")
    amount_zig: Decimal = Decimal("0")

    @property
    def total_usd(self) -> Decimal:
        """Get USD amount."""
        return self.amount_usd

    @property
    def total_zig(self) -> Decimal:
        """Get ZIG amount."""
        return self.amount_zig


@dataclass(frozen=True)
class Earnings(ValueObject):
    """
    Represents all earnings for a payslip.

    Includes base salary and all allowances in both USD and ZIG.
    """

    base_salary_usd: Decimal = Decimal("0")
    base_salary_zig: Decimal = Decimal("0")
    allowances: tuple = field(default_factory=tuple)

    @property
    def total_allowances_usd(self) -> Decimal:
        """Sum of all USD allowances."""
        return sum(
            (a.amount_usd for a in self.allowances),
            Decimal("0")
        )

    @property
    def total_allowances_zig(self) -> Decimal:
        """Sum of all ZIG allowances."""
        return sum(
            (a.amount_zig for a in self.allowances),
            Decimal("0")
        )

    @property
    def gross_usd(self) -> Decimal:
        """Total gross earnings in USD."""
        return self.base_salary_usd + self.total_allowances_usd

    @property
    def gross_zig(self) -> Decimal:
        """Total gross earnings in ZIG."""
        return self.base_salary_zig + self.total_allowances_zig

    def with_allowance(self, name: str, amount_usd: Decimal = Decimal("0"),
                       amount_zig: Decimal = Decimal("0")) -> "Earnings":
        """Create new Earnings with an additional allowance."""
        new_allowance = AllowanceItem(
            name=name,
            amount_usd=amount_usd,
            amount_zig=amount_zig
        )
        return Earnings(
            base_salary_usd=self.base_salary_usd,
            base_salary_zig=self.base_salary_zig,
            allowances=self.allowances + (new_allowance,)
        )

    @classmethod
    def create(cls, base_usd: Decimal, base_zig: Decimal,
               allowances_list: List[Dict] = None) -> "Earnings":
        """
        Factory method to create Earnings.

        Args:
            base_usd: Base salary in USD
            base_zig: Base salary in ZIG
            allowances_list: List of dicts with 'name', 'amount_usd', 'amount_zig'
        """
        items = []
        if allowances_list:
            for a in allowances_list:
                items.append(AllowanceItem(
                    name=a.get("name", "Unknown"),
                    amount_usd=Decimal(str(a.get("amount_usd", 0))),
                    amount_zig=Decimal(str(a.get("amount_zig", 0)))
                ))
        return cls(
            base_salary_usd=base_usd,
            base_salary_zig=base_zig,
            allowances=tuple(items)
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "base_salary_usd": str(self.base_salary_usd),
            "base_salary_zig": str(self.base_salary_zig),
            "total_allowances_usd": str(self.total_allowances_usd),
            "total_allowances_zig": str(self.total_allowances_zig),
            "gross_usd": str(self.gross_usd),
            "gross_zig": str(self.gross_zig),
            "allowances": [
                {
                    "name": a.name,
                    "amount_usd": str(a.amount_usd),
                    "amount_zig": str(a.amount_zig)
                }
                for a in self.allowances
            ]
        }
