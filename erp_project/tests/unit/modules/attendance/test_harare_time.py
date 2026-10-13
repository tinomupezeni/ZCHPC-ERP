"""
Attendance lateness is judged in Harare time.

Clock times are stored as UTC wall time (settings.TIME_ZONE stays UTC). Before
this, 08:00 + 15 min grace was compared with the UTC time, so nobody was late
until 10:15 Harare. Now the stored time is converted to Africa/Harare (UTC+2)
before comparing. The record keeps its UTC date: a clock-in between 00:00 and
02:00 Harare is filed under the previous day (known limitation).
"""

from datetime import date

import pytest

from modules.attendance.domain.entities import AttendanceRecord
from modules.attendance.domain.services import LateArrivalDetector
from modules.attendance.domain.value_objects import AttendanceStatus, ClockTime

DAY = date(2026, 10, 13)


def utc(hour, minute=0):
    return ClockTime(hour=hour, minute=minute)


class TestInAttendanceZone:
    def test_adds_two_hours(self):
        assert utc(6, 20).in_attendance_zone(DAY) == ClockTime(hour=8, minute=20)

    def test_wraps_past_midnight(self):
        assert utc(23, 30).in_attendance_zone(DAY) == ClockTime(hour=1, minute=30)


class TestLateArrivalDetector:
    @pytest.mark.parametrize(
        "stored, late, minutes",
        [
            (utc(5, 55), False, 0),   # 07:55 Harare
            (utc(6, 15), False, 0),   # 08:15, last minute of the grace period
            (utc(6, 16), True, 1),    # 08:16
            (utc(8, 0), True, 105),   # 10:00 Harare; was "on time" when compared as UTC
        ],
    )
    def test_compares_harare_time(self, stored, late, minutes):
        detector = LateArrivalDetector()
        assert detector.is_late(stored, DAY) is late
        assert detector.minutes_late(stored, DAY) == minutes


class TestRecordStatus:
    def make(self, stored):
        return AttendanceRecord(id=1, employee_id=100, record_date=DAY, time_in=stored)

    def test_on_time_in_harare(self):
        assert self.make(utc(6, 10)).status == AttendanceStatus.PRESENT

    def test_late_in_harare(self):
        record = self.make(utc(6, 30))
        assert record.status == AttendanceStatus.LATE
        assert record.is_late

    def test_stored_0800_utc_is_late(self):
        assert self.make(utc(8, 0)).is_late
