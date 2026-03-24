"""
Statutory information value objects.
"""

from dataclasses import dataclass

from shared.domain.base import ValueObject


@dataclass(frozen=True)
class StatutoryInfo(ValueObject):
    """
    Statutory registration information for an employee.

    Contains NSSA, ZIMRA, and PAYE registration numbers.

    Attributes:
        nssa_number: National Social Security Authority number
        zimra_number: Zimbabwe Revenue Authority number
        paye_number: Pay As You Earn tax number
        pays_aids_levy: Whether the employee pays AIDS levy
    """

    nssa_number: str
    zimra_number: str
    paye_number: str
    pays_aids_levy: bool = True

    @classmethod
    def empty(cls) -> "StatutoryInfo":
        """Create empty statutory info."""
        return cls(
            nssa_number="",
            zimra_number="",
            paye_number="",
            pays_aids_levy=True,
        )

    @property
    def has_nssa(self) -> bool:
        """Check if NSSA number is set."""
        return bool(self.nssa_number)

    @property
    def has_zimra(self) -> bool:
        """Check if ZIMRA number is set."""
        return bool(self.zimra_number)

    @property
    def has_paye(self) -> bool:
        """Check if PAYE number is set."""
        return bool(self.paye_number)

    @property
    def is_complete(self) -> bool:
        """Check if all statutory numbers are set."""
        return self.has_nssa and self.has_zimra and self.has_paye

    def __str__(self) -> str:
        """String representation."""
        parts = []
        if self.has_nssa:
            parts.append(f"NSSA: {self.nssa_number}")
        if self.has_zimra:
            parts.append(f"ZIMRA: {self.zimra_number}")
        if self.has_paye:
            parts.append(f"PAYE: {self.paye_number}")
        return ", ".join(parts) if parts else "No statutory info"


@dataclass(frozen=True)
class EmergencyContact(ValueObject):
    """
    Emergency contact information for an employee.

    Attributes:
        name: Contact person's name
        phone: Contact phone number
        relationship: Relationship to the employee
    """

    name: str
    phone: str
    relationship: str

    @classmethod
    def empty(cls) -> "EmergencyContact":
        """Create empty emergency contact."""
        return cls(name="", phone="", relationship="")

    @property
    def is_empty(self) -> bool:
        """Check if contact info is empty."""
        return not self.name and not self.phone

    def __str__(self) -> str:
        """String representation."""
        if self.is_empty:
            return "No emergency contact"
        parts = [self.name]
        if self.relationship:
            parts.append(f"({self.relationship})")
        if self.phone:
            parts.append(f"- {self.phone}")
        return " ".join(parts)
