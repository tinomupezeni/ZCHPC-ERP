"""
Recruitment value objects.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from shared.domain.base import ValueObject


class JobStatus(str, Enum):
    """Job posting status."""

    DRAFT = "Draft"
    OPEN = "Open"
    CLOSED = "Closed"
    PENDING = "Pending"

    @classmethod
    def from_string(cls, value: str) -> "JobStatus":
        """Create status from string value."""
        for status in cls:
            if status.value.lower() == value.lower():
                return status
        raise ValueError(f"Invalid job status: {value}")


class ApplicationStatus(str, Enum):
    """Job application status."""

    PENDING = "Pending"
    SHORTLISTED = "Shortlisted"
    INTERVIEW = "Interview"
    OFFERED = "Offered"
    HIRED = "Hired"
    REJECTED = "Rejected"

    @classmethod
    def from_string(cls, value: str) -> "ApplicationStatus":
        """Create status from string value."""
        for status in cls:
            if status.value.lower() == value.lower():
                return status
        raise ValueError(f"Invalid application status: {value}")

    @property
    def is_final(self) -> bool:
        """Check if this is a final status."""
        return self in (ApplicationStatus.HIRED, ApplicationStatus.REJECTED)

    @property
    def is_active(self) -> bool:
        """Check if application is still active."""
        return not self.is_final


@dataclass(frozen=True)
class SalaryRange(ValueObject):
    """
    Value object representing a salary range.

    Supports both USD and ZIG currencies.
    """

    usd_min: Optional[Decimal] = None
    usd_max: Optional[Decimal] = None
    zig_min: Optional[Decimal] = None
    zig_max: Optional[Decimal] = None

    def __post_init__(self) -> None:
        """Validate salary range."""
        if self.usd_min is not None and self.usd_max is not None:
            if self.usd_min < 0 or self.usd_max < 0:
                raise ValueError("Salary values cannot be negative")
            if self.usd_min > self.usd_max:
                raise ValueError("USD minimum salary cannot exceed maximum")

        if self.zig_min is not None and self.zig_max is not None:
            if self.zig_min < 0 or self.zig_max < 0:
                raise ValueError("Salary values cannot be negative")
            if self.zig_min > self.zig_max:
                raise ValueError("ZIG minimum salary cannot exceed maximum")

    @property
    def has_usd_range(self) -> bool:
        """Check if USD salary range is defined."""
        return self.usd_min is not None or self.usd_max is not None

    @property
    def has_zig_range(self) -> bool:
        """Check if ZIG salary range is defined."""
        return self.zig_min is not None or self.zig_max is not None

    @property
    def usd_display(self) -> str:
        """Get formatted USD salary range."""
        if self.usd_min is not None and self.usd_max is not None:
            return f"${self.usd_min:,.2f} - ${self.usd_max:,.2f}"
        if self.usd_min is not None:
            return f"From ${self.usd_min:,.2f}"
        if self.usd_max is not None:
            return f"Up to ${self.usd_max:,.2f}"
        return ""

    @property
    def zig_display(self) -> str:
        """Get formatted ZIG salary range."""
        if self.zig_min is not None and self.zig_max is not None:
            return f"ZIG {self.zig_min:,.2f} - ZIG {self.zig_max:,.2f}"
        if self.zig_min is not None:
            return f"From ZIG {self.zig_min:,.2f}"
        if self.zig_max is not None:
            return f"Up to ZIG {self.zig_max:,.2f}"
        return ""

    @classmethod
    def empty(cls) -> "SalaryRange":
        """Create an empty salary range."""
        return cls()
