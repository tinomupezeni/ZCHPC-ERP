"""
URL patterns for the portal module API.
"""

from django.urls import path

from modules.portal.api import views

app_name = "portal_v2"

urlpatterns = [
    # Authentication
    path(
        "auth/login/",
        views.login,
        name="login"
    ),
    path(
        "auth/logout/",
        views.logout,
        name="logout"
    ),
    path(
        "auth/me/",
        views.me,
        name="me"
    ),

    # Dashboard
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # Attendance
    path(
        "attendance/status/",
        views.attendance_status,
        name="attendance-status"
    ),
    path(
        "attendance/clock/",
        views.attendance_clock,
        name="attendance-clock"
    ),
    path(
        "attendance/qr/token/",
        views.attendance_qr_token,
        name="attendance-qr-token"
    ),
    path(
        "attendance/qr/clock/",
        views.attendance_qr_clock,
        name="attendance-qr-clock"
    ),
    path(
        "attendance/history/",
        views.attendance_history,
        name="attendance-history"
    ),
    path(
        "attendance/summary/",
        views.attendance_summary,
        name="attendance-summary"
    ),

    # Leave
    path(
        "leave/balances/",
        views.leave_balances,
        name="leave-balances"
    ),
    path(
        "leave/requests/",
        views.leave_requests,
        name="leave-requests"
    ),
    path(
        "leave/requests/<int:request_id>/",
        views.leave_request_cancel,
        name="leave-request-cancel"
    ),
    path(
        "leave/summary/",
        views.leave_summary,
        name="leave-summary"
    ),

    # Payslips
    path(
        "payslips/",
        views.payslips,
        name="payslips"
    ),
    path(
        "payslips/<int:payslip_id>/",
        views.payslip_detail,
        name="payslip-detail"
    ),
    path(
        "payslips/summary/",
        views.payslip_summary,
        name="payslip-summary"
    ),

    # Public Careers (no auth required)
    path(
        "public/jobs/",
        views.public_jobs,
        name="public-jobs"
    ),
    path(
        "public/jobs/<int:job_id>/",
        views.public_job_detail,
        name="public-job-detail"
    ),
    path(
        "public/jobs/<int:job_id>/apply/",
        views.public_job_apply,
        name="public-job-apply"
    ),
    path(
        "public/applications/status/",
        views.public_application_status,
        name="public-application-status"
    ),

    # Notifications
    path(
        "notifications/",
        views.notifications,
        name="notifications"
    ),
    path(
        "notifications/unread-count/",
        views.notification_unread_count,
        name="notification-unread-count"
    ),
    path(
        "notifications/<int:notification_id>/read/",
        views.notification_mark_read,
        name="notification-mark-read"
    ),
    path(
        "notifications/mark-all-read/",
        views.notifications_mark_all_read,
        name="notifications-mark-all-read"
    ),
]
