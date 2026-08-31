"""
Recruitment API serializers.
"""

from rest_framework import serializers


# =============================================================================
# Request Serializers
# =============================================================================


class CreateJobRequestSerializer(serializers.Serializer):
    """Serializer for creating a job."""

    title = serializers.CharField(max_length=200)
    department_id = serializers.IntegerField()
    position_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    responsibilities = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    qualifications = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    competencies = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    location = serializers.CharField(required=False, default="Harare")
    reports_to = serializers.CharField(required=False, default="ZCHPC Director")
    salary_usd_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_usd_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_zig_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_zig_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    is_internal = serializers.BooleanField(required=False, default=False)
    application_process = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(
        required=False, default="hroffice@zchpc.ac.zw"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=["Draft", "Open", "Closed", "Pending"],
        required=False,
        default="Draft",
    )


class UpdateJobRequestSerializer(serializers.Serializer):
    """Serializer for updating a job."""

    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    responsibilities = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    qualifications = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    competencies = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    location = serializers.CharField(required=False)
    reports_to = serializers.CharField(required=False)
    salary_usd_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_usd_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_zig_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    salary_zig_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    is_internal = serializers.BooleanField(required=False)
    application_process = serializers.CharField(required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class SubmitApplicationRequestSerializer(serializers.Serializer):
    """Serializer for submitting a job application."""

    job_id = serializers.IntegerField()
    # External field name matches CheckApplicationRequestSerializer/
    # ApplicationStatusCheckRequestSerializer (and the frontend); it maps to
    # SubmitApplicationCommand.national_id below.
    id_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    qualifications = serializers.CharField(required=False, allow_blank=True)
    experience = serializers.CharField(required=False, allow_blank=True)
    cover_letter = serializers.CharField(required=False, allow_blank=True)


class UpdateApplicationStatusRequestSerializer(serializers.Serializer):
    """Serializer for updating application status."""

    status = serializers.ChoiceField(
        choices=["Pending", "Shortlisted", "Interview", "Offered", "Hired", "Rejected"]
    )


class CheckApplicationRequestSerializer(serializers.Serializer):
    """Serializer for checking if candidate has applied."""

    id_number = serializers.CharField(max_length=20)
    job_id = serializers.IntegerField()


class ApplicationStatusCheckRequestSerializer(serializers.Serializer):
    """Serializer for checking application status by national ID."""

    id_number = serializers.CharField(max_length=20)


class JobQuerySerializer(serializers.Serializer):
    """Serializer for job query parameters."""

    status = serializers.ChoiceField(
        choices=["Draft", "Open", "Closed", "Pending"],
        required=False,
    )
    department = serializers.IntegerField(required=False)
    internal = serializers.BooleanField(required=False)
    search = serializers.CharField(required=False)


# =============================================================================
# Response Serializers
# =============================================================================


class JobResponseSerializer(serializers.Serializer):
    """Serializer for job responses."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    position_id = serializers.IntegerField(allow_null=True)
    position_title = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    location = serializers.CharField()
    reports_to = serializers.CharField()
    salary_usd_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    salary_usd_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    salary_zig_min = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    salary_zig_max = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )
    is_internal = serializers.BooleanField()
    description = serializers.CharField()
    responsibilities = serializers.ListField(child=serializers.CharField())
    qualifications = serializers.ListField(child=serializers.CharField())
    competencies = serializers.ListField(child=serializers.CharField())
    application_process = serializers.CharField()
    contact_email = serializers.EmailField()
    posted_date = serializers.DateField()
    applicants_count = serializers.IntegerField()


class CandidateResponseSerializer(serializers.Serializer):
    """Serializer for candidate responses."""

    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    national_id = serializers.CharField(allow_null=True)
    phone = serializers.CharField()
    address = serializers.CharField()
    date_of_birth = serializers.DateField(allow_null=True)
    has_resume = serializers.BooleanField()
    qualifications = serializers.CharField()
    experience = serializers.CharField()


class ApplicationResponseSerializer(serializers.Serializer):
    """Serializer for application responses."""

    id = serializers.IntegerField()
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField()
    candidate_email = serializers.EmailField()
    cover_letter = serializers.CharField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ApplicationStatusResponseSerializer(serializers.Serializer):
    """Serializer for application status responses."""

    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()


class CheckApplicationResponseSerializer(serializers.Serializer):
    """Serializer for check application response."""

    candidate_exists = serializers.BooleanField()
    has_applied = serializers.BooleanField()
    candidate_id = serializers.IntegerField(required=False)
    candidate_name = serializers.CharField(required=False)
