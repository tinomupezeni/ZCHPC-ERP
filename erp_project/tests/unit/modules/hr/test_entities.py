"""
Tests for HR module entities.
"""

from datetime import date
from decimal import Decimal

import pytest

from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import Email, EmployeeId, NationalId, PhoneNumber

from modules.hr.domain.entities import Department, Employee, Position
from modules.hr.domain.value_objects import (
    BankAccount,
    EmergencyContact,
    EmploymentType,
    Gender,
    MaritalStatus,
    PayFrequency,
    Salary,
    StatutoryInfo,
)


# =============================================================================
# Test Department Entity
# =============================================================================


class TestDepartment:
    """Tests for Department aggregate root."""

    def test_create_department(self):
        """Test creating a department."""
        dept = Department.create(
            id=1,
            name="Engineering",
            description="Software development team",
        )

        assert dept.id == 1
        assert dept.name == "Engineering"
        assert dept.description == "Software development team"

    def test_create_department_without_description(self):
        """Test creating department without description."""
        dept = Department.create(id=1, name="HR")

        assert dept.name == "HR"
        assert dept.description == ""

    def test_empty_name_raises_error(self):
        """Test that empty name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Department.create(id=1, name="")

        assert exc_info.value.code == "EMPTY_NAME"

    def test_update_department(self):
        """Test updating department."""
        dept = Department.create(id=1, name="Engineering")

        dept.update(name="Software Engineering", description="New description")

        assert dept.name == "Software Engineering"
        assert dept.description == "New description"

    def test_str_representation(self):
        """Test string representation."""
        dept = Department.create(id=1, name="Engineering")

        assert str(dept) == "Engineering"


# =============================================================================
# Test Position Entity
# =============================================================================


class TestPosition:
    """Tests for Position aggregate root."""

    def test_create_position(self):
        """Test creating a position."""
        pos = Position.create(
            id=1,
            title="Software Engineer",
            department_id=1,
            description="Develops software",
        )

        assert pos.id == 1
        assert pos.title == "Software Engineer"
        assert pos.department_id == 1
        assert pos.description == "Develops software"

    def test_empty_title_raises_error(self):
        """Test that empty title raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Position.create(id=1, title="", department_id=1)

        assert exc_info.value.code == "EMPTY_TITLE"

    def test_missing_department_raises_error(self):
        """Test that missing department raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Position.create(id=1, title="Engineer", department_id=0)

        assert exc_info.value.code == "MISSING_DEPARTMENT"

    def test_move_to_department(self):
        """Test moving position to another department."""
        pos = Position.create(id=1, title="Engineer", department_id=1)

        pos.move_to_department(2)

        assert pos.department_id == 2

    def test_update_position(self):
        """Test updating position."""
        pos = Position.create(id=1, title="Engineer", department_id=1)

        pos.update(title="Senior Engineer", description="Senior level")

        assert pos.title == "Senior Engineer"
        assert pos.description == "Senior level"


# =============================================================================
# Test Employee Entity
# =============================================================================


class TestEmployee:
    """Tests for Employee aggregate root."""

    def test_create_employee(self):
        """Test creating an employee."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        assert employee.id == 1
        assert str(employee.employee_id) == "EMP0001"
        assert employee.first_name == "John"
        assert employee.surname == "Doe"
        assert employee.is_active

    def test_employee_full_name(self):
        """Test full name property."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        assert employee.full_name == "John Doe"

    def test_empty_first_name_raises_error(self):
        """Test that empty first name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Employee(
                id=1,
                employee_id=EmployeeId("EMP0001"),
                first_name="",
                surname="Doe",
            )

        assert exc_info.value.code == "EMPTY_FIRST_NAME"

    def test_empty_surname_raises_error(self):
        """Test that empty surname raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Employee(
                id=1,
                employee_id=EmployeeId("EMP0001"),
                first_name="John",
                surname="",
            )

        assert exc_info.value.code == "EMPTY_SURNAME"

    def test_update_personal_info(self):
        """Test updating personal information."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        employee.update_personal_info(
            first_name="Jane",
            gender=Gender.FEMALE,
            marital_status=MaritalStatus.MARRIED,
        )

        assert employee.first_name == "Jane"
        assert employee.gender == Gender.FEMALE
        assert employee.marital_status == MaritalStatus.MARRIED

    def test_update_contact_info(self):
        """Test updating contact information."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        employee.update_contact_info(
            email="john@example.com",
            phone="+263771234567",
        )

        assert employee.email.value == "john@example.com"
        assert "+263" in employee.phone.value

    def test_update_employment(self):
        """Test updating employment details."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        employee.update_employment(
            department_id=1,
            position_id=2,
            employee_type=EmploymentType.CONTRACT,
        )

        assert employee.department_id == 1
        assert employee.position_id == 2
        assert employee.employee_type == EmploymentType.CONTRACT

    def test_employee_cannot_report_to_self(self):
        """Test that employee cannot report to themselves."""
        employee = Employee(
            id=1,
            employee_id=EmployeeId("EMP0001"),
            first_name="John",
            surname="Doe",
        )

        with pytest.raises(ValidationError) as exc_info:
            employee.update_employment(reports_to_id=1)

        assert exc_info.value.code == "INVALID_REPORTS_TO"

