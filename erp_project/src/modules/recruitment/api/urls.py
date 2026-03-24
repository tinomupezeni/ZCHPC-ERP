"""
Recruitment API URL configuration.
"""

from django.urls import path

from modules.recruitment.api.views import (
    ApplicationDetailView,
    ApplicationStatusUpdateView,
    ApplicationStatusView,
    CheckApplicationView,
    JobApplicationsView,
    JobCloseView,
    JobDetailView,
    JobListView,
    JobPublishView,
    PublicApplyView,
    PublicJobDetailView,
    PublicJobListView,
)

app_name = "recruitment"

urlpatterns = [
    # Jobs (Admin)
    path("jobs/", JobListView.as_view(), name="job-list"),
    path("jobs/<int:job_id>/", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<int:job_id>/publish/", JobPublishView.as_view(), name="job-publish"),
    path("jobs/<int:job_id>/close/", JobCloseView.as_view(), name="job-close"),
    path("jobs/<int:job_id>/applications/", JobApplicationsView.as_view(), name="job-applications"),

    # Public Jobs
    path("public/jobs/", PublicJobListView.as_view(), name="public-job-list"),
    path("public/jobs/<int:job_id>/", PublicJobDetailView.as_view(), name="public-job-detail"),
    path("public/jobs/apply/", PublicApplyView.as_view(), name="public-apply"),
    path("public/jobs/check-application/", CheckApplicationView.as_view(), name="check-application"),
    path("public/applications/status/", ApplicationStatusView.as_view(), name="application-status"),

    # Applications (Admin)
    path("applications/<int:application_id>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("applications/<int:application_id>/status/", ApplicationStatusUpdateView.as_view(), name="application-status-update"),
]
