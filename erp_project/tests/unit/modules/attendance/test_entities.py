"""
Tests for Attendance module entities.
"""

from datetime import date, datetime, timedelta

import pytest

from shared.domain.exceptions import ValidationError

from modules.attendance.domain.entities import AttendanceRecord, QRToken
from modules.attendance.domain.value_objects import (
    AttendanceStatus,
    ClockTime,
    TokenExpiry,
    TokenValue,
    WorkDuration,
)


# =============================================================================
# Test AttendanceRecord
# =============================================================================


class TestAttendanceRecord:
    """Tests for AttendanceRecord aggregate root."""

    def test_create_attendance_record(self):
        """Test creating an attendance record."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date(2026, 3, 3),
            time_in=ClockTime(hour=8, minute=0),
        )

        assert record.id == 1
        assert record.employee_id == 100
        assert record.record_date == date(2026, 3, 3)
        assert record.time_in.hour == 8
        assert record.time_out is None

    def test_create_for_clock_in(self):
        """Test factory method for clock-in."""
        record = AttendanceRecord.create_for_clock_in(
            id=1,
            employee_id=100,
            record_date=date.today(),
            clock_in_time=ClockTime(hour=8, minute=30),
        )

        assert record.is_clocked_in
        assert not record.is_complete

    def test_clock_in(self):
        """Test clock-in operation."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
        )

        record.clock_in(ClockTime(hour=8, minute=0))

        assert record.time_in is not None
        assert record.is_clocked_in

    def test_clock_in_twice_raises_error(self):
        """Test that clocking in twice raises error."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        with pytest.raises(ValidationError) as exc_info:
            record.clock_in(ClockTime(hour=9, minute=0))

        assert exc_info.value.code == "ALREADY_CLOCKED_IN"

    def test_clock_out(self):
        """Test clock-out operation."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        duration = record.clock_out(ClockTime(hour=17, minute=0))

        assert record.time_out is not None
        assert record.is_complete
        assert duration.hours == 9

    def test_clock_out_without_in_raises_error(self):
        """Test clock-out without clock-in raises error."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
        )

        with pytest.raises(ValidationError) as exc_info:
            record.clock_out(ClockTime(hour=17, minute=0))

        assert exc_info.value.code == "NOT_CLOCKED_IN"

    def test_clock_out_twice_raises_error(self):
        """Test clocking out twice raises error."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
            time_out=ClockTime(hour=17, minute=0),
        )

        with pytest.raises(ValidationError) as exc_info:
            record.clock_out(ClockTime(hour=18, minute=0))

        assert exc_info.value.code == "ALREADY_CLOCKED_OUT"

    def test_work_duration_calculation(self):
        """Test work duration calculation."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
            time_out=ClockTime(hour=17, minute=30),
        )

        assert record.work_duration.hours == 9
        assert record.work_duration.minutes == 30

    def test_work_duration_when_incomplete(self):
        """Test work duration when record incomplete."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        assert record.work_duration.hours == 0
        assert record.work_duration.minutes == 0

    def test_status_absent(self):
        """Test absent status."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
        )

        assert record.status == AttendanceStatus.ABSENT

    def test_status_present(self):
        """Test present status."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        assert record.status == AttendanceStatus.PRESENT

    def test_status_late(self):
        """Test late status (more than 15 minutes after 8:00)."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=30),  # 30 minutes late
        )

        assert record.status == AttendanceStatus.LATE
        assert record.is_late

    def test_is_clocked_in_property(self):
        """Test is_clocked_in property."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        assert record.is_clocked_in

        record.clock_out(ClockTime(hour=17, minute=0))

        assert not record.is_clocked_in

    def test_update_times(self):
        """Test updating times (admin function)."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        record.update_times(
            time_in=ClockTime(hour=7, minute=45),
            time_out=ClockTime(hour=17, minute=0),
        )

        assert record.time_in.hour == 7
        assert record.time_in.minute == 45
        assert record.time_out is not None

    def test_missing_employee_id_raises_error(self):
        """Test missing employee ID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AttendanceRecord(
                id=1,
                employee_id=0,
                record_date=date.today(),
            )

        assert exc_info.value.code == "MISSING_EMPLOYEE_ID"

    def test_str_representation(self):
        """Test string representation."""
        record = AttendanceRecord(
            id=1,
            employee_id=100,
            record_date=date.today(),
            time_in=ClockTime(hour=8, minute=0),
        )

        assert "100" in str(record)
        assert "In Progress" in str(record)


# =============================================================================
# Test QRToken
# =============================================================================


class TestQRToken:
    """Tests for QRToken aggregate root."""

    def test_create_qr_token(self):
        """Test creating a QR token."""
        now = datetime.utcnow()
        token = QRToken.create(id=1, validity_seconds=30, created_at=now)

        assert token.id == 1
        assert len(token.token_value) == 32
        assert token.is_active
        assert token.used_count == 0

    def test_token_is_valid_when_not_expired(self):
        """Test token is valid when not expired."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert token.is_valid()

    def test_token_is_invalid_when_deactivated(self):
        """Test token is invalid when deactivated."""
        token = QRToken.create(id=1, validity_seconds=30)
        token.deactivate()

        assert not token.is_valid()

    def test_verify_correct_token(self):
        """Test verifying correct token string."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert token.verify(token.token_value)

    def test_verify_incorrect_token(self):
        """Test verifying incorrect token string."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert not token.verify("incorrect_token_string")

    def test_increment_usage(self):
        """Test incrementing usage counter."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert token.used_count == 0

        token.increment_usage()
        assert token.used_count == 1

        token.increment_usage()
        assert token.used_count == 2

    def test_deactivate(self):
        """Test deactivating token."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert token.is_active

        token.deactivate()

        assert not token.is_active

    def test_seconds_remaining(self):
        """Test seconds remaining property."""
        token = QRToken.create(id=1, validity_seconds=30)

        # Should have some seconds remaining
        assert 0 < token.seconds_remaining <= 30

    def test_expires_at_property(self):
        """Test expires_at property."""
        now = datetime.utcnow()
        token = QRToken.create(id=1, validity_seconds=30, created_at=now)

        expected = now + timedelta(seconds=30)
        assert abs((token.expires_at - expected).total_seconds()) < 1

    def test_str_representation(self):
        """Test string representation."""
        token = QRToken.create(id=1, validity_seconds=30)

        assert "QRToken" in str(token)
        assert "Active" in str(token)
