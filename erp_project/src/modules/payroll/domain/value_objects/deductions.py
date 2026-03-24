"""
Deductions value object for payroll calculations.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List

from shared.domain.base import ValueObject


@dataclass(frozen=True)
class DeductionItem(ValueObject):
    """Individual deduction item."""

    name: str
    amount_usd: Decimal = Decimal("0")
    amount_zig: Decimal = Decimal("0")
    is_statutory: bool = False

    @property
    def total_usd(self) -> Decimal:
        """Get USD amount."""
        return self.amount_usd

    @property
    def total_zig(self) -> Decimal:
        """Get ZIG amount."""
        return self.amount_zig


@dataclass(frozen=True)
class Deductions(ValueObject):
    """
    Represents all deductions for a payslip.

    Includes statutory (PAYE, NSSA, AIDS levy) and voluntary deductions.
    """

    # Statutory deductions
    paye_usd: Decimal = Decimal("0")
    paye_zig: Decimal = Decimal("0")
    aids_levy_usd: Decimal = Decimal("0")
    aids_levy_zig: Decimal = Decimal("0")
    nssa_employee_usd: Decimal = Decimal("0")
    nssa_employee_zig: Decimal = Decimal("0")

    # Employer contributions (not deducted from employee)
    nssa_employer_usd: Decimal = Decimal("0")
    nssa_employer_zig: Decimal = Decimal("0")

    # Other deductions
    other_deductions: tuple = field(default_factory=tuple)

    @property
    def total_statutory_usd(self) -> Decimal:
        """Sum of all statutory deductions in USD."""
        return (
            self.paye_usd +
            self.aids_levy_usd +
            self.nssa_employee_usd
        )

    @property
    def total_statutory_zig(self) -> Decimal:
        """Sum of all statutory deductions in ZIG."""
        return (
            self.paye_zig +
            self.aids_levy_zig +
            self.nssa_employee_zig
        )

    @property
    def total_other_usd(self) -> Decimal:
        """Sum of all other deductions in USD."""
        return sum(
            (d.amount_usd for d in self.other_deductions),
            Decimal("0")
        )

    @property
    def total_other_zig(self) -> Decimal:
        """Sum of all other deductions in ZIG."""
        return sum(
            (d.amount_zig for d in self.other_deductions),
            Decimal("0")
        )

    @property
    def total_usd(self) -> Decimal:
        """Total deductions in USD (excluding employer contributions)."""
        return self.total_statutory_usd + self.total_other_usd

    @property
    def total_zig(self) -> Decimal:
        """Total deductions in ZIG (excluding employer contributions)."""
        return self.total_statutory_zig + self.total_other_zig

    @property
    def total_employer_usd(self) -> Decimal:
        """Total employer contributions in USD."""
        return self.nssa_employer_usd

    @property
    def total_employer_zig(self) -> Decimal:
        """Total employer contributions in ZIG."""
        return self.nssa_employer_zig

    def with_deduction(self, name: str, amount_usd: Decimal = Decimal("0"),
                       amount_zig: Decimal = Decimal("0")) -> "Deductions":
        """Create new Deductions with an additional deduction item."""
        new_deduction = DeductionItem(
            name=name,
            amount_usd=amount_usd,
            amount_zig=amount_zig,
            is_statutory=False
        )
        return Deductions(
            paye_usd=self.paye_usd,
            paye_zig=self.paye_zig,
            aids_levy_usd=self.aids_levy_usd,
            aids_levy_zig=self.aids_levy_zig,
            nssa_employee_usd=self.nssa_employee_usd,
            nssa_employee_zig=self.nssa_employee_zig,
            nssa_employer_usd=self.nssa_employer_usd,
            nssa_employer_zig=self.nssa_employer_zig,
            other_deductions=self.other_deductions + (new_deduction,)
        )

    @classmethod
    def create_statutory(
        cls,
        paye_usd: Decimal,
        paye_zig: Decimal,
        aids_levy_usd: Decimal,
        aids_levy_zig: Decimal,
        nssa_employee_usd: Decimal,
        nssa_employee_zig: Decimal,
        nssa_employer_usd: Decimal,
        nssa_employer_zig: Decimal,
        other_deductions: List[Dict] = None
    ) -> "Deductions":
        """Factory method to create Deductions with statutory amounts."""
        items = []
        if other_deductions:
            for d in other_deductions:
                items.append(DeductionItem(
                    name=d.get("name", "Unknown"),
                    amount_usd=Decimal(str(d.get("amount_usd", 0))),
                    amount_zig=Decimal(str(d.get("amount_zig", 0))),
                    is_statutory=False
                ))
        return cls(
            paye_usd=paye_usd,
            paye_zig=paye_zig,
            aids_levy_usd=aids_levy_usd,
            aids_levy_zig=aids_levy_zig,
            nssa_employee_usd=nssa_employee_usd,
            nssa_employee_zig=nssa_employee_zig,
            nssa_employer_usd=nssa_employer_usd,
            nssa_employer_zig=nssa_employer_zig,
            other_deductions=tuple(items)
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "paye_usd": str(self.paye_usd),
            "paye_zig": str(self.paye_zig),
            "aids_levy_usd": str(self.aids_levy_usd),
            "aids_levy_zig": str(self.aids_levy_zig),
            "nssa_employee_usd": str(self.nssa_employee_usd),
            "nssa_employee_zig": str(self.nssa_employee_zig),
            "nssa_employer_usd": str(self.nssa_employer_usd),
            "nssa_employer_zig": str(self.nssa_employer_zig),
            "total_statutory_usd": str(self.total_statutory_usd),
            "total_statutory_zig": str(self.total_statutory_zig),
            "total_other_usd": str(self.total_other_usd),
            "total_other_zig": str(self.total_other_zig),
            "total_usd": str(self.total_usd),
            "total_zig": str(self.total_zig),
            "other_deductions": [
                {
                    "name": d.name,
                    "amount_usd": str(d.amount_usd),
                    "amount_zig": str(d.amount_zig)
                }
                for d in self.other_deductions
            ]
        }
