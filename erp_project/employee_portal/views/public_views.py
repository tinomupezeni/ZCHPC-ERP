"""
Public views for job applications - no authentication required.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone

from human_resources.hr_models import Job, Candidate, JobApplication


class PublicJobListView(APIView):
    """
    List all open jobs for public viewing.

    GET /api/portal/public/jobs/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        jobs = Job.objects.filter(
            status='Open'
        ).select_related('department', 'position').order_by('-created_at')

        jobs_data = []
        for job in jobs:
            # Format qualifications list as string for requirements field
            requirements = ''
            if job.qualifications:
                if isinstance(job.qualifications, list):
                    requirements = '\n'.join(f"• {q}" for q in job.qualifications)
                else:
                    requirements = str(job.qualifications)

            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'department': job.department.name if job.department else None,
                'location': job.location,
                'employment_type': 'Full-time',  # Default value
                'description': job.description,
                'requirements': requirements,
                'salary_min': float(job.salary_usd_min) if job.salary_usd_min else None,
                'salary_max': float(job.salary_usd_max) if job.salary_usd_max else None,
                'closing_date': None,  # Field doesn't exist in model
                'posted_date': job.posted_date,
                'is_internal': job.is_internal,
            })

        return Response({
            'jobs': jobs_data,
            'total': len(jobs_data)
        })


class PublicJobDetailView(APIView):
    """
    Get details of a specific job.

    GET /api/portal/public/jobs/{id}/
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            job = Job.objects.select_related('department', 'position').get(
                pk=pk,
                status='Open'
            )
        except Job.DoesNotExist:
            return Response(
                {'detail': 'Job not found or no longer open.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Format qualifications list as string for requirements field
        requirements = ''
        if job.qualifications:
            if isinstance(job.qualifications, list):
                requirements = '\n'.join(f"• {q}" for q in job.qualifications)
            else:
                requirements = str(job.qualifications)

        # Format responsibilities list as string
        responsibilities = ''
        if job.responsibilities:
            if isinstance(job.responsibilities, list):
                responsibilities = '\n'.join(f"• {r}" for r in job.responsibilities)
            else:
                responsibilities = str(job.responsibilities)

        return Response({
            'id': job.id,
            'title': job.title,
            'department': job.department.name if job.department else None,
            'position': job.position.title if job.position else None,
            'location': job.location,
            'employment_type': 'Full-time',  # Default value
            'description': job.description,
            'requirements': requirements,
            'responsibilities': responsibilities,
            'salary_min': float(job.salary_usd_min) if job.salary_usd_min else None,
            'salary_max': float(job.salary_usd_max) if job.salary_usd_max else None,
            'closing_date': None,  # Field doesn't exist in model
            'posted_date': job.posted_date,
            'is_internal': job.is_internal,
            'application_count': job.applications.count(),
        })


class CheckApplicationView(APIView):
    """
    Check if a candidate has already applied for a job using their ID number.

    POST /api/portal/public/jobs/check-application/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_number = request.data.get('id_number')
        job_id = request.data.get('job_id')

        if not id_number or not job_id:
            return Response(
                {'detail': 'ID number and job ID are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if candidate exists with this ID number
        try:
            candidate = Candidate.objects.get(id_number=id_number)
            # Check if they've already applied for this job
            has_applied = JobApplication.objects.filter(
                candidate=candidate,
                job_id=job_id
            ).exists()

            return Response({
                'has_applied': has_applied,
                'candidate_exists': True,
                'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            })
        except Candidate.DoesNotExist:
            return Response({
                'has_applied': False,
                'candidate_exists': False,
            })


class SubmitApplicationView(APIView):
    """
    Submit a job application.

    POST /api/portal/public/jobs/apply/
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        # Required fields
        job_id = request.data.get('job_id')
        id_number = request.data.get('id_number')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone = request.data.get('phone', '')

        # Optional fields
        address = request.data.get('address', '')
        date_of_birth = request.data.get('date_of_birth')
        qualifications = request.data.get('qualifications', '')
        experience = request.data.get('experience', '')
        cover_letter = request.data.get('cover_letter', '')
        resume = request.FILES.get('resume')

        # Validate required fields
        if not all([job_id, id_number, first_name, last_name, email]):
            return Response(
                {'detail': 'Job ID, ID number, first name, last name, and email are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if job exists and is open
        try:
            job = Job.objects.get(pk=job_id, status='Open')
        except Job.DoesNotExist:
            return Response(
                {'detail': 'Job not found or no longer accepting applications.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get or create candidate
        candidate, created = Candidate.objects.get_or_create(
            id_number=id_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'address': address,
                'qualifications': qualifications,
                'experience': experience,
            }
        )

        # If candidate exists, check for duplicate application
        if not created:
            if JobApplication.objects.filter(candidate=candidate, job=job).exists():
                return Response(
                    {'detail': 'You have already applied for this position.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update candidate info if they're applying again
            candidate.first_name = first_name
            candidate.last_name = last_name
            candidate.email = email
            candidate.phone = phone
            if address:
                candidate.address = address
            if qualifications:
                candidate.qualifications = qualifications
            if experience:
                candidate.experience = experience

        # Handle date of birth
        if date_of_birth:
            try:
                from datetime import datetime
                if isinstance(date_of_birth, str):
                    candidate.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                else:
                    candidate.date_of_birth = date_of_birth
            except ValueError:
                pass

        # Handle resume upload
        if resume:
            candidate.resume = resume

        candidate.save()

        # Create job application
        application = JobApplication.objects.create(
            job=job,
            candidate=candidate,
            cover_letter=cover_letter,
            status='Pending'
        )

        return Response({
            'detail': 'Application submitted successfully.',
            'application_id': application.id,
            'job_title': job.title,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
        }, status=status.HTTP_201_CREATED)


class ApplicationStatusView(APIView):
    """
    Check application status using ID number.

    POST /api/portal/public/applications/status/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_number = request.data.get('id_number')

        if not id_number:
            return Response(
                {'detail': 'ID number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            candidate = Candidate.objects.get(id_number=id_number)
        except Candidate.DoesNotExist:
            return Response(
                {'detail': 'No applications found for this ID number.'},
                status=status.HTTP_404_NOT_FOUND
            )

        applications = JobApplication.objects.filter(
            candidate=candidate
        ).select_related('job').order_by('-applied_on')

        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'job_title': app.job.title,
                'job_department': app.job.department.name if app.job.department else None,
                'applied_on': app.applied_on,
                'status': app.status,
            })

        return Response({
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'applications': applications_data,
            'total': len(applications_data)
        })
