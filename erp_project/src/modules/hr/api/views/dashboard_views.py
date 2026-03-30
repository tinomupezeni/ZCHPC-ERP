"""
HR Dashboard API views.
"""
from datetime import date, timedelta

from django.db.models import Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class HRDashboardView(APIView):
    """
    API endpoint for HR dashboard aggregated data.

    GET /api/v2/hr/dashboard/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return aggregated HR dashboard data.

        Response:
        {
            "metrics": {
                "totalEmployees": int,
                "totalDepartments": int,
                "openPositions": int,
                "inInterviewStage": int,
                "timeOffRequests": int,
                "pendingTimeOff": int
            },
            "newEmployees": [...],
            "trainingPrograms": [...],
            "upcomingReviews": [...]
        }
        """
        from modules.hr.infrastructure.persistence.models import (
            Employees, Department, Position
        )

        # Metrics
        total_employees = Employees.objects.filter(is_active=True).count()
        total_departments = Department.objects.count()

        # Open positions (placeholder - can be extended with Job model)
        open_positions = 0
        in_interview_stage = 0

        # Try to get recruitment data if available
        try:
            from modules.recruitment.infrastructure.persistence.models import Job, Application
            open_positions = Job.objects.filter(status='open').count()
            in_interview_stage = Application.objects.filter(status='interview').count()
        except Exception:
            pass

        # Time off requests (placeholder - can be extended with Leave model)
        time_off_requests = 0
        pending_time_off = 0

        try:
            from modules.leave.infrastructure.persistence.models import LeaveRequest
            time_off_requests = LeaveRequest.objects.filter(
                created_at__gte=date.today() - timedelta(days=30)
            ).count()
            pending_time_off = LeaveRequest.objects.filter(status='pending').count()
        except Exception:
            pass

        # New employees (joined in last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        new_employees_qs = Employees.objects.filter(
            is_active=True,
            date_joined__gte=thirty_days_ago
        ).select_related('department', 'position', 'role').order_by('-date_joined')[:5]

        new_employees = [
            {
                'id': emp.id,
                'name': f"{emp.first_name} {emp.surname}",
                'role': emp.role.display_name if emp.role else 'N/A',
                'department': emp.department.name if emp.department else 'N/A',
                'joinDate': emp.date_joined.isoformat() if emp.date_joined else None,
                'avatarUrl': None,
            }
            for emp in new_employees_qs
        ]

        # Training programs (placeholder)
        training_programs = []
        try:
            from modules.hr.infrastructure.persistence.models import TrainingProgram
            # If model has fields, fetch them
            training_programs = []
        except Exception:
            pass

        # Upcoming reviews (placeholder)
        upcoming_reviews = []

        return Response({
            'metrics': {
                'totalEmployees': total_employees,
                'totalDepartments': total_departments,
                'openPositions': open_positions,
                'inInterviewStage': in_interview_stage,
                'timeOffRequests': time_off_requests,
                'pendingTimeOff': pending_time_off,
            },
            'newEmployees': new_employees,
            'trainingPrograms': training_programs,
            'upcomingReviews': upcoming_reviews,
        }, status=status.HTTP_200_OK)
