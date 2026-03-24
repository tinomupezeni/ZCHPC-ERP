"""
Attendance API URL configuration.
"""

from django.urls import path

from modules.attendance.api.views import (
    AttendanceHistoryView,
    AttendanceStatusView,
    AttendanceSummaryView,
    ClockInView,
    ClockOutView,
    QRClockInView,
    QRTokenView,
)

app_name = "attendance"

urlpatterns = [
    # Manual clock in/out
    path("clock-in/", ClockInView.as_view(), name="clock_in"),
    path("clock-out/", ClockOutView.as_view(), name="clock_out"),
    # Status and history
    path("status/", AttendanceStatusView.as_view(), name="status"),
    path("history/", AttendanceHistoryView.as_view(), name="history"),
    path("summary/", AttendanceSummaryView.as_view(), name="summary"),
    # QR-based clock in
    path("qr/token/", QRTokenView.as_view(), name="qr_token"),
    path("qr/clock-in/", QRClockInView.as_view(), name="qr_clock_in"),
]
