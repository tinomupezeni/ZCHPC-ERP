"""
Tests for HR module value objects.
"""

from decimal import Decimal

import pytest

from shared.domain.exceptions import ValidationError

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
# Test EmploymentType
# =============================================================================


class TestEmploymentType:
    """Tests for EmploymentType enum."""

    def test_employment_type_values(self):
        """Test employment type values."""
        assert EmploymentType.FULL_TIME.value == "Full-time"
        assert EmploymentType.PART_TIME.value == "Part-time"
        assert EmploymentType.CONTRACT.value == "Contract"
        assert EmploymentType.INTERN.value == "Intern"

    def test_from_string(self):
        """Test creating from string."""
        assert EmploymentType.from_string("Full-time") == EmploymentType.FULL_TIME
        assert EmploymentType.from_string("fulltime") == EmploymentType.FULL_TIME
        assert EmploymentType.from_string("FULLTIME") == EmploymentType.FULL_TIME
        assert EmploymentType.from_string("Part-time") == EmploymentType.PART_TIME

    def test_from_string_invalid_raises_error(self):
        """Test invalid string raises error."""
        with pytest.raises(ValueError):
            EmploymentType.from_string("invalid")


# =============================================================================
# Test Gender
# =============================================================================


class TestGender:
    """Tests for Gender enum."""

    def test_gender_values(self):
        """Test gender values."""
        assert Gender.MALE.value == "Male"
        assert Gender.FEMALE.value == "Female"
        assert Gender.OTHER.value == "Other"

    def test_from_string(self):
        """Test creating from string."""
        assert Gender.from_string("Male") == Gender.MALE
        assert Gender.from_string("male") == Gender.MALE
        assert Gender.from_string("M") == Gender.MALE
        assert Gender.from_string("Female") == Gender.FEMALE
        assert Gender.from_string("f") == Gender.FEMALE

    def test_from_string_invalid_raises_error(self):
        """Test invalid string raises error."""
        with pytest.raises(ValueError):
            Gender.from_string("invalid")


# =============================================================================
# Test MaritalStatus
# =============================================================================


class TestMaritalStatus:
    """Tests for MaritalStatus enum."""

    def test_marital_status_values(self):
        """Test marital status values."""
        assert MaritalStatus.SINGLE.value == "Single"
        assert MaritalStatus.MARRIED.value == "Married"
        assert MaritalStatus.DIVORCED.value == "Divorced"
        assert MaritalStatus.WIDOWED.value == "Widowed"

    def test_from_string(self):
        """Test creating from string."""
        assert MaritalStatus.from_string("Single") == MaritalStatus.SINGLE
        assert MaritalStatus.from_string("single") == MaritalStatus.SINGLE
        assert MaritalStatus.from_string("Married") == MaritalStatus.MARRIED


# =============================================================================
# Test PayFrequency
# =============================================================================


class TestPayFrequency:
    """Tests for PayFrequency enum."""

    def test_pay_frequency_values(self):
        """Test pay frequency values."""
        assert PayFrequency.MONTHLY.value == "Monthly"
        assert PayFrequency.WEEKLY.value == "Weekly"
        assert PayFrequency.BI_WEEKLY.value == "Bi-Weekly"

    def test_from_string(self):
        """Test creating from string."""
        assert PayFrequency.from_string("Monthly") == PayFrequency.MONTHLY
        assert PayFrequency.from_string("Bi-Weekly") == PayFrequency.BI_WEEKLY
        assert PayFrequency.from_string("biweekly") == PayFrequency.BI_WEEKLY


# =============================================================================
# Test Salary
# =============================================================================


        """Test that zero salary raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Salary.create(usd_amount=0, zig_amount=0)

        assert exc_info.value.code == "ZERO_SALARY"

    def test_negative_salary_raises_error(self):
        """Test that negative salary raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Salary.create(usd_amount=-100, zig_amount=1000)

        assert exc_info.value.code == "NEGATIVE_SALARY"

    def test_with_increase(self):
        """Test salary increase."""
        salary = Salary.create(usd_amount=1000, zig_amount=5000)
        new_salary = salary.with_increase(usd_increase=Decimal("200"), zig_increase=Decimal("500"))

        assert new_salary.usd_amount == Decimal("1200")
        assert new_salary.zig_amount == Decimal("5500")

    def test_with_percentage_increase(self):
        """Test percentage salary increase."""
        salary = Salary.create(usd_amount=1000, zig_amount=10000)
        new_salary = salary.with_percentage_increase(Decimal("10"))

        assert new_salary.usd_amount == Decimal("1100")
        assert new_salary.zig_amount == Decimal("11000")

    def test_total_in_usd(self):
        """Test calculating total in USD."""
        salary = Salary.create(usd_amount=1000, zig_amount=10000)
        # With exchange rate of 10 ZIG per USD
        total = salary.total_in_usd(Decimal("10"))

        assert total.amount == Decimal("2000")  # 1000 + (10000/10)

    def test_str_representation(self):
        """Test string representation."""
        salary = Salary.create(usd_amount=1000, zig_amount=5000)
        assert "$1,000.00" in str(salary)
        assert "ZIG 5,000.00" in str(salary)


# =============================================================================
# Test BankAccount
# =============================================================================


        """Test that account number without bank name raises error."""
        with pytest.raises(ValueError):
            BankAccount(bank_name="", account_number="123456789")


# =============================================================================
# Test StatutoryInfo
# =============================================================================


class TestStatutoryInfo:
    """Tests for StatutoryInfo value object."""

    def test_create_statutory_info(self):
        """Test creating statutory info."""
        info = StatutoryInfo(
            nssa_number="N12345",
            zimra_number="Z67890",
            paye_number="P11111",
            pays_aids_levy=True,
        )

        assert info.nssa_number == "N12345"
        assert info.zimra_number == "Z67890"
        assert info.paye_number == "P11111"
        assert info.pays_aids_levy
        assert info.is_complete

    def test_empty_statutory_info(self):
        """Test empty statutory info."""
        info = StatutoryInfo.empty()

        assert not info.has_nssa
        assert not info.has_zimra
        assert not info.has_paye
        assert not info.is_complete

    def test_partial_statutory_info(self):
        """Test partial statutory info."""
        info = StatutoryInfo(
            nssa_number="N12345",
            zimra_number="",
            paye_number="",
        )

        assert info.has_nssa
        assert not info.has_zimra
        assert not info.has_paye
        assert not info.is_complete


# =============================================================================
# Test EmergencyContact
# =============================================================================


class TestEmergencyContact:
    """Tests for EmergencyContact value object."""

    def test_create_emergency_contact(self):
        """Test creating emergency contact."""
        contact = EmergencyContact(
            name="John Doe",
            number="+263771234567",
            relationship="Spouse",
        )

        assert contact.name == "John Doe"
        assert contact.number == "+263771234567"
        assert contact.relationship == "Spouse"
        assert not contact.is_empty

    def test_empty_emergency_contact(self):
        """Test empty emergency contact."""
        contact = EmergencyContact.empty()

        assert contact.is_empty
        assert contact.name == ""
        assert contact.number == ""

    def test_str_representation(self):
        """Test string representation."""
        contact = EmergencyContact(
            name="Jane Doe",
            number="+263771234567",
            relationship="Sister",
        )

        assert "Jane Doe" in str(contact)
        assert "Sister" in str(contact)
        assert "+263771234567" in str(contact)
