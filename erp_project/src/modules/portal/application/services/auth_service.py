"""
Portal authentication service.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shared.domain.exceptions import ValidationError, NotFoundError
from modules.portal.application.interfaces import (
    IEmployeeProvider,
    EmployeeDTO,
)


@dataclass
class AuthResult:
    """Result of authentication attempt."""

    success: bool
    employee: Optional[EmployeeDTO] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    message: Optional[str] = None


class PortalAuthService:
    """
    Authentication service for employee portal.

    Handles EC number based login and token management.
    """

    def __init__(
        self,
        employee_provider: IEmployeeProvider,
    ) -> None:
        self._employee_provider = employee_provider

    def authenticate(
        self,
        ec_number: str,
        password: str,
    ) -> AuthResult:
        """
        Authenticate employee by EC number and password.

        Args:
            ec_number: Employee ID (e.g., EMP0001)
            password: User password

        Returns:
            AuthResult with employee data and tokens if successful
        """
        if not ec_number or not password:
            return AuthResult(
                success=False,
                message="EC number and password are required"
            )

        # Authenticate through provider
        employee = self._employee_provider.authenticate(
            ec_number=ec_number.strip().upper(),
            password=password,
        )

        if employee is None:
            return AuthResult(
                success=False,
                message="Invalid EC number or password"
            )

        if not employee.is_active:
            return AuthResult(
                success=False,
                message="Account is deactivated"
            )

        # Token generation would be handled by infrastructure layer
        # Return success with employee data
        return AuthResult(
            success=True,
            employee=employee,
            message="Login successful"
        )

    def get_current_employee(
        self,
        user_id: int,
    ) -> EmployeeDTO:
        """
        Get the current authenticated employee.

        Args:
            user_id: Django user ID

        Returns:
            Employee data

        Raises:
            NotFoundError: If employee not found
        """
        employee = self._employee_provider.get_by_user_id(user_id)
        if employee is None:
            raise NotFoundError("Employee not found for this user")
        return employee

    def get_employee_by_id(
        self,
        employee_id: int,
    ) -> EmployeeDTO:
        """
        Get employee by internal ID.

        Args:
            employee_id: Internal employee ID

        Returns:
            Employee data

        Raises:
            NotFoundError: If employee not found
        """
        employee = self._employee_provider.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError(f"Employee {employee_id} not found")
        return employee

    def get_employee_by_ec_number(
        self,
        ec_number: str,
    ) -> EmployeeDTO:
        """
        Get employee by EC number.

        Args:
            ec_number: Employee ID (e.g., EMP0001)

        Returns:
            Employee data

        Raises:
            NotFoundError: If employee not found
        """
        employee = self._employee_provider.get_by_ec_number(
            ec_number.strip().upper()
        )
        if employee is None:
            raise NotFoundError(f"Employee {ec_number} not found")
        return employee
