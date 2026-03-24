"""
Tests for recruitment entities.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from modules.recruitment.domain.entities import Application, Candidate, Job
from modules.recruitment.domain.value_objects import ApplicationStatus, JobStatus, SalaryRange


class TestJob:
    """Tests for Job entity."""

    def test_create_job(self):
        """Test creating a job."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
        )
        assert job.id == 1
        assert job.title == "Software Engineer"
        assert job.department_id == 1
        assert job.status == JobStatus.DRAFT

    def test_create_job_with_details(self):
        """Test creating a job with full details."""
        salary = SalaryRange(
            usd_min=Decimal("50000"),
            usd_max=Decimal("70000"),
        )
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            position_id=5,
            status=JobStatus.OPEN,
            location="Harare",
            salary_range=salary,
            is_internal=False,
            description="Build software",
            responsibilities=["Code", "Test"],
            qualifications=["BSc CS"],
        )
        assert job.position_id == 5
        assert job.status == JobStatus.OPEN
        assert job.salary_range.usd_min == Decimal("50000")
        assert len(job.responsibilities) == 2

    def test_publish_job(self):
        """Test publishing a draft job."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.DRAFT,
        )
        job.publish()
        assert job.status == JobStatus.OPEN

    def test_close_job(self):
        """Test closing an open job."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.OPEN,
        )
        job.close()
        assert job.status == JobStatus.CLOSED

    def test_reopen_job(self):
        """Test reopening a closed job."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.CLOSED,
        )
        job.reopen()
        assert job.status == JobStatus.OPEN

    def test_cannot_publish_closed_job(self):
        """Test that closed job cannot be published."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.CLOSED,
        )
        with pytest.raises(ValueError):
            job.publish()

    def test_is_public(self):
        """Test is_public property."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.OPEN,
            is_internal=False,
        )
        assert job.is_public is True

    def test_is_not_public_internal(self):
        """Test is_public for internal job."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
            status=JobStatus.OPEN,
            is_internal=True,
        )
        assert job.is_public is False

    def test_update_details(self):
        """Test updating job details."""
        job = Job(
            id=1,
            title="Software Engineer",
            department_id=1,
        )
        job.update_details(
            title="Senior Software Engineer",
            description="Lead development",
        )
        assert job.title == "Senior Software Engineer"
        assert job.description == "Lead development"


class TestCandidate:
    """Tests for Candidate entity."""

    def test_create_candidate(self):
        """Test creating a candidate."""
        candidate = Candidate(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert candidate.id == 1
        assert candidate.first_name == "John"
        assert candidate.last_name == "Doe"
        assert candidate.email == "john@example.com"

    def test_full_name(self):
        """Test full name property."""
        candidate = Candidate(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert candidate.full_name == "John Doe"

    def test_has_resume_false(self):
        """Test has_resume when no resume."""
        candidate = Candidate(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert candidate.has_resume is False

    def test_has_resume_true(self):
        """Test has_resume when resume exists."""
        candidate = Candidate(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            resume_path="resumes/john_doe.pdf",
        )
        assert candidate.has_resume is True

    def test_update_contact(self):
        """Test updating contact info."""
        candidate = Candidate(
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        candidate.update_contact(
            email="john.doe@example.com",
            phone="+263771234567",
        )
        assert candidate.email == "john.doe@example.com"
        assert candidate.phone == "+263771234567"

    def test_invalid_email_raises_error(self):
        """Test that invalid email raises error."""
        with pytest.raises(ValueError):
            Candidate(
                id=1,
                first_name="John",
                last_name="Doe",
                email="invalid-email",
            )


class TestApplication:
    """Tests for Application entity."""

    def test_create_application(self):
        """Test creating an application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        assert application.id == 1
        assert application.job_id == 1
        assert application.candidate_id == 1
        assert application.status == ApplicationStatus.PENDING

    def test_is_active_pending(self):
        """Test is_active for pending application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        assert application.is_active is True

    def test_is_active_hired(self):
        """Test is_active for hired application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
            status=ApplicationStatus.HIRED,
        )
        assert application.is_active is False

    def test_shortlist(self):
        """Test shortlisting an application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        application.shortlist()
        assert application.status == ApplicationStatus.SHORTLISTED

    def test_schedule_interview(self):
        """Test scheduling interview."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        application.schedule_interview()
        assert application.status == ApplicationStatus.INTERVIEW

    def test_make_offer(self):
        """Test making an offer."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
            status=ApplicationStatus.INTERVIEW,
        )
        application.make_offer()
        assert application.status == ApplicationStatus.OFFERED

    def test_hire(self):
        """Test hiring."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
            status=ApplicationStatus.OFFERED,
        )
        application.hire()
        assert application.status == ApplicationStatus.HIRED
        assert application.is_hired is True

    def test_reject(self):
        """Test rejecting."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        application.reject()
        assert application.status == ApplicationStatus.REJECTED
        assert application.is_rejected is True

    def test_cannot_hire_rejected(self):
        """Test cannot hire rejected application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
            status=ApplicationStatus.REJECTED,
        )
        with pytest.raises(ValueError):
            application.hire()

    def test_cannot_reject_hired(self):
        """Test cannot reject hired application."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
            status=ApplicationStatus.HIRED,
        )
        with pytest.raises(ValueError):
            application.reject()

    def test_change_status_valid(self):
        """Test valid status change."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        application.change_status(ApplicationStatus.SHORTLISTED)
        assert application.status == ApplicationStatus.SHORTLISTED

    def test_change_status_invalid(self):
        """Test invalid status change."""
        application = Application(
            id=1,
            job_id=1,
            candidate_id=1,
        )
        with pytest.raises(ValueError):
            # Cannot jump from Pending to Offered
            application.change_status(ApplicationStatus.OFFERED)
