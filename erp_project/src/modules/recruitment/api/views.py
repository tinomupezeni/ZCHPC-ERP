"""
Recruitment API views.
"""
from rest_framework.parsers import MultiPartParser, FormParser
from modules.recruitment.api.validators import validate_resume_file
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.domain.exceptions import DomainException

from modules.recruitment.api.actors import recruitment_actor_from_request
from modules.recruitment.api.errors import error_response
from modules.recruitment.api.serializers import (
    ApplicationResponseSerializer,
    ApplicationStatusCheckRequestSerializer,
    ApplicationStatusResponseSerializer,
    CheckApplicationRequestSerializer,
    CheckApplicationResponseSerializer,
    CreateJobRequestSerializer,
    JobQuerySerializer,
    JobResponseSerializer,
    PublicApplicationReceiptSerializer,
    PublicJobResponseSerializer,
    SubmitApplicationRequestSerializer,
    UpdateApplicationStatusRequestSerializer,
    UpdateJobRequestSerializer,
)
from modules.recruitment.api.throttles import (
    RecruitmentApplyThrottle,
    RecruitmentCheckThrottle,
    RecruitmentStatusThrottle,
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
from modules.recruitment.infrastructure.storage.resume_storage import DjangoResumeStorage


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
        resume_storage=DjangoResumeStorage(),
    )


# Authorization (REM-04) is enforced in the recruitment application services,
# which take the RecruitmentActor built here. Views only translate HTTP; every
# service call catches DomainException through error_response *before* any
# broader handler, so an AuthorizationError is never reported as a 400/404.


# =============================================================================
# Job Views (Admin)
# =============================================================================


class JobListView(APIView):
    """List and create jobs."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all jobs with optional filters."""
        # .dict() (a plain dict) rather than the QueryDict itself: DRF's
        # BooleanField treats a QueryDict specially (HTML checkbox semantics)
        # and silently defaults a missing 'internal' key to False instead of
        # "not provided", which would filter out every internal job whenever
        # the caller doesn't pass ?internal= at all.
        query_serializer = JobQuerySerializer(data=request.query_params.dict())
        query_serializer.is_valid(raise_exception=True)

        service = get_job_service()
        actor = recruitment_actor_from_request(request)

        try:
            search = query_serializer.validated_data.get("search")
            if search:
                jobs = service.search_jobs(
                    query=search,
                    status=query_serializer.validated_data.get("status"),
                    actor=actor,
                )
            else:
                jobs = service.get_all_jobs(
                    status=query_serializer.validated_data.get("status"),
                    department_id=query_serializer.validated_data.get("department"),
                    is_internal=query_serializer.validated_data.get("internal"),
                    actor=actor,
                )
        except DomainException as e:
            return error_response(e)

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
            job = service.create_job(command, recruitment_actor_from_request(request))
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_201_CREATED,
            )
        except DomainException as e:
            return error_response(e)
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
            job = service.get_job(job_id, recruitment_actor_from_request(request))
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e, default_status=status.HTTP_404_NOT_FOUND)
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
            job = service.update_job(command, recruitment_actor_from_request(request))
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, job_id: int):
        """Delete a job."""
        service = get_job_service()
        try:
            service.delete_job(job_id, recruitment_actor_from_request(request))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainException as e:
            return error_response(e)
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
            job = service.publish_job(job_id, recruitment_actor_from_request(request))
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
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
            job = service.close_job(job_id, recruitment_actor_from_request(request))
            return Response(
                JobResponseSerializer(job).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
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
                actor=recruitment_actor_from_request(request),
            )
            return Response(
                [ApplicationResponseSerializer(a).data for a in applications],
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =============================================================================
# Public Jobs Views
# =============================================================================
#
# The public careers surface (REM-04): open jobs (internal ones included, by
# product decision) through the PublicJobResponseSerializer allowlist,
# anonymous application, and status lookup. The three anonymous write/lookup
# endpoints are rate limited.


class PublicJobListView(APIView):
    """Public job listings."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Get all open jobs, internal and external."""
        service = get_job_service()
        jobs = service.get_public_jobs()
        return Response(
            [PublicJobResponseSerializer(j).data for j in jobs],
            status=status.HTTP_200_OK,
        )


class PublicJobDetailView(APIView):
    """Public job detail."""

    permission_classes = [AllowAny]

    def get(self, request, job_id: int):
        """Get a specific open job (public view)."""
        service = get_job_service()
        try:
            job = service.get_public_job(job_id)
        except DomainException:
            # Draft, Pending, Closed and missing jobs are indistinguishable.
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            PublicJobResponseSerializer(job).data,
            status=status.HTTP_200_OK,
        )


class PublicApplyView(APIView):
    """Public job application."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [RecruitmentApplyThrottle]

    def post(self, request):
        """
        Submit a job application, including a resume upload. Resubmitting for
        the same job updates the existing application.
        """
        serializer = SubmitApplicationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_file = request.FILES.get("resume")
        validate_resume_file(resume_file)

        service = get_application_service()
        try:
            date_of_birth = serializer.validated_data.get("date_of_birth")
            dob_str = str(date_of_birth) if date_of_birth else None

            command = SubmitApplicationCommand(
                job_id=serializer.validated_data["job_id"],
                national_id=serializer.validated_data.get("id_number"),
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
                email=serializer.validated_data["email"],
                phone=serializer.validated_data.get("phone", ""),
                address=serializer.validated_data.get("address", ""),
                date_of_birth=dob_str,
                qualifications=serializer.validated_data.get("qualifications", ""),
                experience=serializer.validated_data.get("experience", ""),
                cover_letter=serializer.validated_data.get("cover_letter", ""),
                resume_file=resume_file,
            )
            result = service.submit_application(command)
            return Response(
                {
                    "success": True,
                    "message": (
                        "Application submitted successfully"
                        if result.created
                        else "Application updated successfully"
                    ),
                    "application": PublicApplicationReceiptSerializer(result.application).data,
                },
                status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CheckApplicationView(APIView):
    """Check if an applicant has applied to a job."""

    permission_classes = [AllowAny]
    throttle_classes = [RecruitmentCheckThrottle]

    def post(self, request):
        """Check if the holder of a national ID has applied to a job."""
        serializer = CheckApplicationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_application_service()
        has_applied = service.has_applied(
            national_id=serializer.validated_data["id_number"],
            job_id=serializer.validated_data["job_id"],
        )
        return Response(
            CheckApplicationResponseSerializer({"has_applied": has_applied}).data,
            status=status.HTTP_200_OK,
        )


class ApplicationStatusView(APIView):
    """Check application status by national ID."""

    permission_classes = [AllowAny]
    throttle_classes = [RecruitmentStatusThrottle]

    def post(self, request):
        """
        Get all applications for a national ID. An unknown ID returns the same
        empty list as an ID with no applications.
        """
        serializer = ApplicationStatusCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = get_application_service()
        applications = service.lookup_application_status(
            serializer.validated_data["id_number"]
        )

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
            application = service.get_application(
                application_id, recruitment_actor_from_request(request)
            )
            return Response(
                ApplicationResponseSerializer(application).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e, default_status=status.HTTP_404_NOT_FOUND)
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
            application = service.update_status(
                command, recruitment_actor_from_request(request)
            )
            return Response(
                ApplicationResponseSerializer(application).data,
                status=status.HTTP_200_OK,
            )
        except DomainException as e:
            return error_response(e)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
