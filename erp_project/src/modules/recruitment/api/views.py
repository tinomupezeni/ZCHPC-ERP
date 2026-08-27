"""
Recruitment API views.
"""
from rest_framework.parsers import MultiPartParser, FormParser
from modules.recruitment.api.validators import validate_resume_file
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.recruitment.api.serializers import (
    ApplicationResponseSerializer,
    ApplicationStatusCheckRequestSerializer,
    ApplicationStatusResponseSerializer,
    CheckApplicationRequestSerializer,
    CheckApplicationResponseSerializer,
    CreateJobRequestSerializer,
    JobQuerySerializer,
    JobResponseSerializer,
    SubmitApplicationRequestSerializer,
    UpdateApplicationStatusRequestSerializer,
    UpdateJobRequestSerializer,
)
from modules.recruitment.application.services import (
    ApplicationService,
    CreateJobCommand,
    JobService,
    SubmitApplicationCommand,
    UpdateApplicationStatusCommand,
    UpdateJobCommand,
)
from modules.recruitment.infrastructure.persistence.django_application_repository import DjangoApplicationRepository
from modules.recruitment.infrastructure.persistence.django_candidate_repository import DjangoCandidateRepository
from modules.recruitment.infrastructure.persistence.django_job_repository import DjangoJobRepository


def get_job_service() -> JobService:
    """Factory for JobService."""
    return JobService(
        job_repository=DjangoJobRepository(),
        application_repository=DjangoApplicationRepository(),
    )


def get_application_service() -> ApplicationService:
    """Factory for ApplicationService."""
    return ApplicationService(
        application_repository=DjangoApplicationRepository(),
        candidate_repository=DjangoCandidateRepository(),
        job_repository=DjangoJobRepository(),
    )


# =============================================================================
# Job Views (Admin)
# =============================================================================


class JobListView(APIView):
    """List and create jobs."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all jobs with optional filters."""
        query_serializer = JobQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        service = get_job_service()

        search = query_serializer.validated_data.get("search")
        if search:
            jobs = service.search_jobs(
                query=search,
                status=query_serializer.validated_data.get("status"),
            )
        else:
            jobs = service.get_all_jobs(
                status=query_serializer.validated_data.get("status"),
                department_id=query_serializer.validated_data.get("department"),
                is_internal=query_serializer.validated_data.get("internal"),
            )

        return Response(
            [JobResponseSerializer(j).data for j in jobs],
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new job."""
        serializer = CreateJobRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_job_service()
        try:
            command = CreateJobCommand(**serializer.validated_data)
            job = service.create_job(command)
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobDetailView(APIView):
    """Retrieve, update, and delete jobs."""

    permission_classes = [IsAuthenticated]

    def get(self, request, job_id: int):
        """Get a specific job."""
        service = get_job_service()
        try:
            job = service.get_job(job_id)
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, job_id: int):
        """Update a job."""
        serializer = UpdateJobRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_job_service()
        try:
            command = UpdateJobCommand(
                job_id=job_id,
                **serializer.validated_data,
            )
            job = service.update_job(command)
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, job_id: int):
        """Delete a job."""
        service = get_job_service()
        try:
            service.delete_job(job_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobPublishView(APIView):
    """Publish a job."""

    permission_classes = [IsAuthenticated]

    def post(self, request, job_id: int):
        """Publish (open) a job."""
        service = get_job_service()
        try:
            job = service.publish_job(job_id)
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobCloseView(APIView):
    """Close a job."""

    permission_classes = [IsAuthenticated]

    def post(self, request, job_id: int):
        """Close a job."""
        service = get_job_service()
        try:
            job = service.close_job(job_id)
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class JobApplicationsView(APIView):
    """Get applications for a job."""

    permission_classes = [IsAuthenticated]

    def get(self, request, job_id: int):
        """Get all applications for a job."""
        status_filter = request.query_params.get("status")

        service = get_application_service()
        try:
            applications = service.get_applications_for_job(
                job_id=job_id,
                status=status_filter,
            )
            return Response(
                [ApplicationResponseSerializer(a).data for a in applications],
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# Public Jobs Views
# =============================================================================


class PublicJobListView(APIView):
    """Public job listings."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get all public (open, non-internal) jobs."""
        service = get_job_service()
        jobs = service.get_public_jobs()
        return Response(
            [JobResponseSerializer(j).data for j in jobs],
            status=status.HTTP_200_OK,
        )


class PublicJobDetailView(APIView):
    """Public job detail."""

    permission_classes = [AllowAny]

    def get(self, request, job_id: int):
        """Get a specific job (public view)."""
        service = get_job_service()
        try:
            job = service.get_job(job_id)
            # Only return if job is open and not internal
            if job.status != "Open" or job.is_internal:
                return Response(
                    {"error": "Job not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class PublicApplyView(APIView):
    """Public job application."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Submit a job application, including a resume upload."""
        serializer = SubmitApplicationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_file = request.FILES.get("resume")
        validate_resume_file(resume_file)

        # Save the file and get a path back for the domain layer.
        from django.core.files.storage import default_storage
        saved_path = default_storage.save(
            f"recruitment/resumes/{resume_file.name}", resume_file
        )

        service = get_application_service()
        try:
            date_of_birth = serializer.validated_data.get("date_of_birth")
            dob_str = str(date_of_birth) if date_of_birth else None

            command = SubmitApplicationCommand(
                job_id=serializer.validated_data["job_id"],
                national_id=serializer.validated_data.get("national_id"),
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
                email=serializer.validated_data["email"],
                phone=serializer.validated_data.get("phone", ""),
                address=serializer.validated_data.get("address", ""),
                date_of_birth=dob_str,
                qualifications=serializer.validated_data.get("qualifications", ""),
                experience=serializer.validated_data.get("experience", ""),
                cover_letter=serializer.validated_data.get("cover_letter", ""),
                resume_path=saved_path,
            )
            application = service.submit_application(command)
            return Response(
                {
                    "success": True,
                    "message": "Application submitted successfully",
                    "application": ApplicationResponseSerializer(application).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CheckApplicationView(APIView):
    """Check if candidate has applied."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Check if candidate has applied to a job."""
        serializer = CheckApplicationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_application_service()
        result = service.check_application_by_national_id(
            national_id=serializer.validated_data["id_number"],
            job_id=serializer.validated_data["job_id"],
        )
        return Response(
            CheckApplicationResponseSerializer(result).data,
            status=status.HTTP_200_OK,
        )


class ApplicationStatusView(APIView):
    """Check application status by national ID."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Get all applications for a candidate by national ID."""
        serializer = ApplicationStatusCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate_repo = DjangoCandidateRepository()
        candidate = candidate_repo.get_by_national_id(
            serializer.validated_data["id_number"]
        )

        if not candidate:
            return Response(
                {"error": "No applications found for this ID number"},
                status=status.HTTP_404_NOT_FOUND,
            )

        service = get_application_service()
        applications = service.get_candidate_applications(candidate.id)

        return Response(
            [ApplicationStatusResponseSerializer(a).data for a in applications],
            status=status.HTTP_200_OK,
        )


# =============================================================================
# Application Management Views (Admin)
# =============================================================================


class ApplicationDetailView(APIView):
    """Application detail view."""

    permission_classes = [IsAuthenticated]

    def get(self, request, application_id: int):
        """Get a specific application."""
        service = get_application_service()
        try:
            application = service.get_application(application_id)
            return Response(
                ApplicationResponseSerializer(application).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )


class ApplicationStatusUpdateView(APIView):
    """Update application status."""

    permission_classes = [IsAuthenticated]

    def post(self, request, application_id: int):
        """Update application status."""
        serializer = UpdateApplicationStatusRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_application_service()
        try:
            command = UpdateApplicationStatusCommand(
                application_id=application_id,
                new_status=serializer.validated_data["status"],
            )
            application = service.update_status(command)
            return Response(
                ApplicationResponseSerializer(application).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )