"""
Employee ID generator domain service.
"""

from abc import ABC, abstractmethod

from shared.domain.value_objects import EmployeeId


class IEmployeeIdGenerator(ABC):
    """
    Interface for generating unique employee IDs.

    This is a domain service interface that generates the next
    available employee ID in the EMP0001 format.
    """

    @abstractmethod
    def next_id(self) -> EmployeeId:
        """
        Generate the next employee ID.

        Returns:
            Next available EmployeeId
        """
        ...

    @abstractmethod
    def is_available(self, employee_id: EmployeeId) -> bool:
        """
        Check if an employee ID is available.

        Args:
            employee_id: The employee ID to check

        Returns:
            True if available, False otherwise
        """
        ...


class SequentialEmployeeIdGenerator(IEmployeeIdGenerator):
    """
    Sequential employee ID generator.

    Generates employee IDs in sequential order (EMP0001, EMP0002, etc.).
    Uses a callback to check existing IDs in the repository.
    """

    def __init__(self, get_max_id_callback: callable):
        """
        Initialize generator.

        Args:
            get_max_id_callback: Callback that returns the current max ID number
        """
        self._get_max_id = get_max_id_callback

    def next_id(self) -> EmployeeId:
        """Generate the next employee ID."""
        current_max = self._get_max_id()
        if current_max is None:
            return EmployeeId.from_number(1)
        return current_max.next()

    def is_available(self, employee_id: EmployeeId) -> bool:
        """Check if an employee ID is available."""
        # This would need to be implemented with a repository check
        # For now, always return True - real check happens in repository
        return True
