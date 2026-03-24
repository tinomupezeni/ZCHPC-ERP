"""
Tests for Attendance module value objects.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest

from modules.attendance.domain.value_objects import (
    AttendanceStatus,
    AttendanceSummary,
    ClockTime,
    TokenExpiry,
    TokenValue,
    WorkDuration,
)


# =============================================================================
# Test AttendanceStatus
# =============================================================================


class TestAttendanceStatus:
    """Tests for AttendanceStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert AttendanceStatus.PRESENT.value == "Present"
        assert AttendanceStatus.ABSENT.value == "Absent"
        assert AttendanceStatus.LATE.value == "Late"
        assert AttendanceStatus.HALF_DAY.value == "Half Day"

    def test_from_string(self):
        """Test creating from string."""
        assert AttendanceStatus.from_string("Present") == AttendanceStatus.PRESENT
        assert AttendanceStatus.from_string("present") == AttendanceStatus.PRESENT
        assert AttendanceStatus.from_string("Late") == AttendanceStatus.LATE
        assert AttendanceStatus.from_string("Half Day") == AttendanceStatus.HALF_DAY
        assert AttendanceStatus.from_string("half_day") == AttendanceStatus.HALF_DAY

    def test_from_string_invalid_raises_error(self):
        """Test invalid string raises error."""
        with pytest.raises(ValueError):
            AttendanceStatus.from_string("invalid")


# =============================================================================
# Test ClockTime
# =============================================================================


class TestClockTime:
    """Tests for ClockTime value object."""

    def test_create_clock_time(self):
        """Test creating a clock time."""
        clock = ClockTime(hour=8, minute=30, second=0)

        assert clock.hour == 8
        assert clock.minute == 30
        assert clock.second == 0

    def test_from_time(self):
        """Test creating from Python time."""
        t = time(9, 15, 30)
        clock = ClockTime.from_time(t)

        assert clock.hour == 9
        assert clock.minute == 15
        assert clock.second == 30

    def test_from_string_hh_mm(self):
        """Test creating from HH:MM string."""
        clock = ClockTime.from_string("08:30")

        assert clock.hour == 8
        assert clock.minute == 30
        assert clock.second == 0

    def test_from_string_hh_mm_ss(self):
        """Test creating from HH:MM:SS string."""
        clock = ClockTime.from_string("08:30:45")

        assert clock.hour == 8
        assert clock.minute == 30
        assert clock.second == 45

    def test_to_time(self):
        """Test converting to Python time."""
        clock = ClockTime(hour=14, minute=30, second=15)
        t = clock.to_time()

        assert t == time(14, 30, 15)

    def test_to_minutes(self):
        """Test converting to minutes from midnight."""
        clock = ClockTime(hour=8, minute=30)
        assert clock.to_minutes() == 510  # 8 * 60 + 30

    def test_invalid_hour_raises_error(self):
        """Test invalid hour raises error."""
        with pytest.raises(ValueError):
            ClockTime(hour=24, minute=0)

    def test_invalid_minute_raises_error(self):
        """Test invalid minute raises error."""
        with pytest.raises(ValueError):
            ClockTime(hour=8, minute=60)

    def test_str_representation(self):
        """Test string representation."""
        clock = ClockTime(hour=8, minute=5)
        assert str(clock) == "08:05"


# =============================================================================
# Test WorkDuration
# =============================================================================


class TestWorkDuration:
    """Tests for WorkDuration value object."""

    def test_create_work_duration(self):
        """Test creating a work duration."""
        duration = WorkDuration(hours=8, minutes=30)

        assert duration.hours == 8
        assert duration.minutes == 30

    def test_from_clock_times(self):
        """Test calculating duration between clock times."""
        time_in = ClockTime(hour=8, minute=0)
        time_out = ClockTime(hour=17, minute=30)

        duration = WorkDuration.from_clock_times(time_in, time_out)

        assert duration.hours == 9
        assert duration.minutes == 30

    def test_from_clock_times_overnight(self):
        """Test overnight shift duration calculation."""
        time_in = ClockTime(hour=22, minute=0)
        time_out = ClockTime(hour=6, minute=0)

        duration = WorkDuration.from_clock_times(time_in, time_out)

        assert duration.hours == 8
        assert duration.minutes == 0

    def test_zero_duration(self):
        """Test zero duration."""
        duration = WorkDuration.zero()

        assert duration.hours == 0
        assert duration.minutes == 0

    def test_total_minutes(self):
        """Test total minutes calculation."""
        duration = WorkDuration(hours=2, minutes=30)
        assert duration.total_minutes == 150

    def test_total_hours(self):
        """Test total hours calculation."""
        duration = WorkDuration(hours=2, minutes=30)
        assert duration.total_hours == Decimal("2.5")

    def test_add_durations(self):
        """Test adding two durations."""
        d1 = WorkDuration(hours=2, minutes=30)
        d2 = WorkDuration(hours=1, minutes=45)

        result = d1 + d2

        assert result.hours == 4
        assert result.minutes == 15

    def test_str_representation(self):
        """Test string representation."""
        duration = WorkDuration(hours=8, minutes=30)
        assert str(duration) == "8h 30m"


# =============================================================================
# Test AttendanceSummary
# =============================================================================


class TestAttendanceSummary:
    """Tests for AttendanceSummary value object."""

    def test_create_summary(self):
        """Test creating an attendance summary."""
        summary = AttendanceSummary(
            days_present=18,
            days_absent=2,
            days_late=3,
            days_half_day=1,
            days_on_leave=1,
            total_hours_worked=Decimal("160.5"),
            average_hours_per_day=Decimal("8.025"),
        )

        assert summary.days_present == 18
        assert summary.days_absent == 2
        assert summary.total_hours_worked == Decimal("160.5")

    def test_total_working_days(self):
        """Test total working days calculation."""
        summary = AttendanceSummary(
            days_present=15,
            days_absent=3,
            days_late=2,
            days_half_day=1,
            days_on_leave=1,
            total_hours_worked=Decimal("150"),
            average_hours_per_day=Decimal("8"),
        )

        assert summary.total_working_days == 22

    def test_attendance_rate(self):
        """Test attendance rate calculation."""
        summary = AttendanceSummary(
            days_present=18,
            days_absent=2,
            days_late=0,
            days_half_day=0,
            days_on_leave=0,
            total_hours_worked=Decimal("144"),
            average_hours_per_day=Decimal("8"),
        )

        assert summary.attendance_rate == Decimal("90")


# =============================================================================
# Test TokenValue
# =============================================================================


class TestTokenValue:
    """Tests for TokenValue value object."""

    def test_create_token_value(self):
        """Test creating a token value."""
        token = TokenValue(value="abcdefgh12345678")

        assert token.value == "abcdefgh12345678"

    def test_generate_token(self):
        """Test generating a random token."""
        token = TokenValue.generate(length=32)

        assert len(token.value) == 32

    def test_generate_different_tokens(self):
        """Test that generated tokens are different."""
        token1 = TokenValue.generate()
        token2 = TokenValue.generate()

        assert token1.value != token2.value

    def test_masked_property(self):
        """Test masked property."""
        token = TokenValue(value="abcdefghijklmnop1234567890123456")

        assert token.masked == "abcdefgh..."

    def test_empty_token_raises_error(self):
        """Test that empty token raises error."""
        with pytest.raises(ValueError):
            TokenValue(value="")

    def test_short_token_raises_error(self):
        """Test that short token raises error."""
        with pytest.raises(ValueError):
            TokenValue(value="abc")

    def test_str_representation_is_masked(self):
        """Test string representation is masked."""
        token = TokenValue(value="abcdefghijklmnop1234567890123456")

        assert str(token) == "abcdefgh..."


# =============================================================================
# Test TokenExpiry
# =============================================================================


class TestTokenExpiry:
    """Tests for TokenExpiry value object."""

    def test_create_token_expiry(self):
        """Test creating token expiry."""
        now = datetime.utcnow()
        expiry = TokenExpiry.create(validity_seconds=30, created_at=now)

        assert expiry.created_at == now
        assert expiry.expires_at == now + timedelta(seconds=30)

    def test_validity_seconds(self):
        """Test validity seconds property."""
        expiry = TokenExpiry.create(validity_seconds=60)

        assert expiry.validity_seconds == 60

    def test_is_valid_when_not_expired(self):
        """Test is_valid when token not expired."""
        now = datetime.utcnow()
        expiry = TokenExpiry.create(validity_seconds=30, created_at=now)

        assert expiry.is_valid(at_time=now + timedelta(seconds=15))

    def test_is_valid_when_expired(self):
        """Test is_valid when token expired."""
        now = datetime.utcnow()
        expiry = TokenExpiry.create(validity_seconds=30, created_at=now)

        assert not expiry.is_valid(at_time=now + timedelta(seconds=60))

    def test_invalid_expiry_before_creation(self):
        """Test that expiry before creation raises error."""
        now = datetime.utcnow()
        with pytest.raises(ValueError):
            TokenExpiry(created_at=now, expires_at=now - timedelta(seconds=10))

    def test_zero_validity_raises_error(self):
        """Test that zero validity raises error."""
        with pytest.raises(ValueError):
            TokenExpiry.create(validity_seconds=0)

    def test_excessive_validity_raises_error(self):
        """Test that excessive validity raises error."""
        with pytest.raises(ValueError):
            TokenExpiry.create(validity_seconds=7200)
