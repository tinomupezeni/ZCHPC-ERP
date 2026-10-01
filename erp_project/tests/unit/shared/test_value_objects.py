"""
Tests for shared value objects: Money, DateRange, Period, Email, etc.
"""

from datetime import date
from decimal import Decimal

import pytest

from shared.domain.exceptions import ValidationError
from shared.domain.value_objects import (
    Currency,
    DateRange,
    Email,
    EmployeeId,
    Money,
    NationalId,
    Period,
    PhoneNumber,
)


# =============================================================================
# Test Money
# =============================================================================


class TestMoney:
    """Tests for Money value object."""

    def test_create_money_with_decimal(self):
        money = Money(amount=Decimal("100.50"), currency=Currency.USD)
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.USD

    def test_create_money_usd_convenience(self):
        money = Money.usd(1500)
        assert money.amount == Decimal("1500")
        assert money.currency == Currency.USD

    def test_create_money_zig_convenience(self):
        money = Money.zig(25000)
        assert money.amount == Decimal("25000")
        assert money.currency == Currency.ZIG

    def test_create_money_zero(self):
        money = Money.zero(Currency.USD)
        assert money.amount == Decimal("0")
        assert money.is_zero()

    def test_add_same_currency(self):
        m1 = Money.usd(100)
        m2 = Money.usd(50)
        result = m1.add(m2)
        assert result.amount == Decimal("150")
        assert result.currency == Currency.USD

    def test_add_different_currency_raises_error(self):
        m1 = Money.usd(100)
        m2 = Money.zig(50)
        with pytest.raises(ValidationError) as exc_info:
            m1.add(m2)
        assert exc_info.value.code == "CURRENCY_MISMATCH"

    def test_subtract(self):
        m1 = Money.usd(100)
        m2 = Money.usd(30)
        result = m1.subtract(m2)
        assert result.amount == Decimal("70")

    def test_multiply(self):
        money = Money.usd(100)
        result = money.multiply(0.25)
        assert result.amount == Decimal("25")

    def test_divide(self):
        money = Money.usd(100)
        result = money.divide(4)
        assert result.amount == Decimal("25")

    def test_divide_by_zero_raises_error(self):
        money = Money.usd(100)
        with pytest.raises(ValidationError) as exc_info:
            money.divide(0)
        assert exc_info.value.code == "DIVISION_BY_ZERO"

    def test_round(self):
        money = Money.usd("100.456")
        result = money.round(2)
        assert result.amount == Decimal("100.46")

    def test_is_positive(self):
        assert Money.usd(100).is_positive()
        assert not Money.usd(-100).is_positive()
        assert not Money.usd(0).is_positive()

    def test_is_negative(self):
        assert Money.usd(-100).is_negative()
        assert not Money.usd(100).is_negative()

    def test_comparisons(self):
        m1 = Money.usd(100)
        m2 = Money.usd(50)
        assert m1.is_greater_than(m2)
        assert m2.is_less_than(m1)
        assert m1.is_greater_or_equal(m1)
        assert m2.is_less_or_equal(m2)

    def test_negate(self):
        money = Money.usd(100)
        result = money.negate()
        assert result.amount == Decimal("-100")

    def test_abs(self):
        money = Money.usd(-100)
        result = money.abs()
        assert result.amount == Decimal("100")

    def test_str_representation(self):
        money = Money.usd("1234.56")
        assert str(money) == "USD 1,234.56"


# =============================================================================
# Test DateRange
# =============================================================================


class TestDateRange:
    """Tests for DateRange value object."""

    def test_create_date_range(self):
        start = date(2026, 3, 1)
        end = date(2026, 3, 31)
        dr = DateRange(start_date=start, end_date=end)
        assert dr.start_date == start
        assert dr.end_date == end

    def test_invalid_date_range_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start_date=date(2026, 3, 31), end_date=date(2026, 3, 1))
        assert exc_info.value.code == "INVALID_DATE_RANGE"

    def test_single_day_range(self):
        day = date(2026, 3, 15)
        dr = DateRange.single_day(day)
        assert dr.start_date == day
        assert dr.end_date == day
        assert dr.days == 1

    def test_month_range(self):
        dr = DateRange.month(2026, 3)
        assert dr.start_date == date(2026, 3, 1)
        assert dr.end_date == date(2026, 3, 31)
        assert dr.days == 31

    def test_year_range(self):
        dr = DateRange.year(2026)
        assert dr.start_date == date(2026, 1, 1)
        assert dr.end_date == date(2026, 12, 31)

    def test_days_property(self):
        dr = DateRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 10))
        assert dr.days == 10

    def test_contains_date(self):
        dr = DateRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        assert dr.contains(date(2026, 3, 15))
        assert not dr.contains(date(2026, 4, 1))

    def test_overlaps(self):
        dr1 = DateRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 15))
        dr2 = DateRange(start_date=date(2026, 3, 10), end_date=date(2026, 3, 25))
        dr3 = DateRange(start_date=date(2026, 3, 20), end_date=date(2026, 3, 31))

        assert dr1.overlaps(dr2)
        assert not dr1.overlaps(dr3)

    def test_intersection(self):
        dr1 = DateRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 15))
        dr2 = DateRange(start_date=date(2026, 3, 10), end_date=date(2026, 3, 25))

        intersection = dr1.intersection(dr2)
        assert intersection is not None
        assert intersection.start_date == date(2026, 3, 10)
        assert intersection.end_date == date(2026, 3, 15)

    def test_iteration(self):
        dr = DateRange(start_date=date(2026, 3, 1), end_date=date(2026, 3, 3))
        dates = list(dr)
        assert dates == [date(2026, 3, 1), date(2026, 3, 2), date(2026, 3, 3)]


# =============================================================================
# Test Period
# =============================================================================


class TestPeriod:
    """Tests for Period value object."""

    def test_create_period(self):
        period = Period(year=2026, month=3)
        assert period.year == 2026
        assert period.month == 3

    def test_invalid_month_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Period(year=2026, month=13)
        assert exc_info.value.code == "INVALID_MONTH"

    def test_from_date(self):
        period = Period.from_date(date(2026, 3, 15))
        assert period.year == 2026
        assert period.month == 3

    def test_from_string(self):
        period = Period.from_string("2026-03")
        assert period.year == 2026
        assert period.month == 3

    def test_first_and_last_day(self):
        period = Period(year=2026, month=3)
        assert period.first_day == date(2026, 3, 1)
        assert period.last_day == date(2026, 3, 31)

    def test_next_period(self):
        period = Period(year=2026, month=3)
        next_p = period.next()
        assert next_p.year == 2026
        assert next_p.month == 4

    def test_next_period_year_rollover(self):
        period = Period(year=2026, month=12)
        next_p = period.next()
        assert next_p.year == 2027
        assert next_p.month == 1

    def test_previous_period(self):
        period = Period(year=2026, month=3)
        prev_p = period.previous()
        assert prev_p.year == 2026
        assert prev_p.month == 2

    def test_previous_period_year_rollback(self):
        period = Period(year=2026, month=1)
        prev_p = period.previous()
        assert prev_p.year == 2025
        assert prev_p.month == 12

    def test_add_months(self):
        period = Period(year=2026, month=3)
        result = period.add_months(5)
        assert result.year == 2026
        assert result.month == 8

    def test_add_months_negative(self):
        period = Period(year=2026, month=3)
        result = period.add_months(-5)
        assert result.year == 2025
        assert result.month == 10

    def test_to_date_range(self):
        period = Period(year=2026, month=3)
        dr = period.to_date_range()
        assert dr.start_date == date(2026, 3, 1)
        assert dr.end_date == date(2026, 3, 31)

    def test_comparisons(self):
        p1 = Period(year=2026, month=3)
        p2 = Period(year=2026, month=5)
        assert p1 < p2
        assert p2 > p1
        assert p1.is_before(p2)
        assert p2.is_after(p1)

    def test_str_format(self):
        period = Period(year=2026, month=3)
        assert str(period) == "2026-03"


# =============================================================================
# Test Email
# =============================================================================


class TestEmail:
    """Tests for Email value object."""

    def test_valid_email(self):
        email = Email("user@example.com")
        assert email.value == "user@example.com"

    def test_email_normalized_to_lowercase(self):
        email = Email("User@EXAMPLE.COM")
        assert email.value == "user@example.com"

    def test_invalid_email_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Email("not-an-email")
        assert exc_info.value.code == "INVALID_EMAIL_FORMAT"

    def test_empty_email_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Email("")
        assert exc_info.value.code == "EMPTY_EMAIL"

    def test_domain_property(self):
        email = Email("user@example.com")
        assert email.domain == "example.com"

    def test_local_part_property(self):
        email = Email("user@example.com")
        assert email.local_part == "user"


# =============================================================================
# Test PhoneNumber
# =============================================================================


class TestPhoneNumber:
    """Tests for PhoneNumber value object."""

    def test_valid_phone(self):
        phone = PhoneNumber("+263771234567")
        assert phone.value == "+263771234567"

    def test_phone_normalized(self):
        phone = PhoneNumber("+263 77 123 4567")
        assert phone.value == "+263771234567"

    def test_invalid_phone_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PhoneNumber("123")  # Too short
        assert exc_info.value.code == "INVALID_PHONE_FORMAT"

    def test_is_mobile(self):
        phone = PhoneNumber("0771234567")
        assert phone.is_mobile

    def test_to_international(self):
        phone = PhoneNumber("0771234567")
        international = phone.to_international()
        assert international.value == "+263771234567"


# =============================================================================
# Test NationalId
# =============================================================================


class TestNationalId:
    """Tests for NationalId value object."""

    def test_valid_national_id(self):
        nid = NationalId("63-123456-A-78")
        assert nid.value == "63-123456-A-78"

    def test_national_id_uppercase(self):
        nid = NationalId("63-123456-a-78")
        assert nid.value == "63-123456-A-78"

    def test_invalid_national_id_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            NationalId("invalid")
        assert exc_info.value.code == "INVALID_NATIONAL_ID_FORMAT"

    def test_district_code_property(self):
        nid = NationalId("63-123456-A-78")
        assert nid.district_code == "63"

    def test_serial_number_property(self):
        nid = NationalId("63-123456-A-78")
        assert nid.serial_number == "123456"


# =============================================================================
# Test EmployeeId
# =============================================================================


class TestEmployeeId:
    """Tests for EmployeeId value object."""

    def test_valid_employee_id(self):
        emp_id = EmployeeId("EMP0001")
        assert emp_id.value == "EMP0001"

    def test_employee_id_uppercase(self):
        emp_id = EmployeeId("emp0001")
        assert emp_id.value == "EMP0001"

    def test_invalid_employee_id_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            EmployeeId("invalid")
        assert exc_info.value.code == "INVALID_EMPLOYEE_ID_FORMAT"

    def test_generate_employee_id(self):
        emp_id = EmployeeId.generate(current_max=5)
        assert emp_id.value == "EMP0006"

    def test_from_number(self):
        emp_id = EmployeeId.from_number(42)
        assert emp_id.value == "EMP0042"

    def test_numeric_part_property(self):
        emp_id = EmployeeId("EMP0042")
        assert emp_id.numeric_part == 42

    def test_next(self):
        emp_id = EmployeeId("EMP0005")
        next_id = emp_id.next()
        assert next_id.value == "EMP0006"

    def test_comparisons(self):
        emp1 = EmployeeId("EMP0001")
        emp2 = EmployeeId("EMP0010")
        assert emp1 < emp2
        assert emp2 > emp1
