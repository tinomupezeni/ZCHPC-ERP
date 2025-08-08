from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db.models import Count, Q
from django.utils import timezone
from ..models import Employees, Department, TrainingProgram, TrainingSession
from ..serializers.hr_dashboard_serializer import (
    EmployeeSerializer, DepartmentSerializer, TrainingProgramSerializer,
    TrainingSessionSerializer
)

class HrDashboardView(APIView):
    """
    A view to return all necessary data for the HR dashboard.
    """
    def get(self, request):
        today = timezone.now().date()
        
        # Metrics
        total_employees = Employees.objects.filter(isActive=True).count()
        total_departments = Department.objects.count()
        open_positions = 8 # Placeholder - you'll need a JobPosition model to make this dynamic
        in_interview_stage = 4 # Placeholder - linked to a Recruitment model
        time_off_requests = 6 # Placeholder - linked to a LeaveRequest model
        pending_time_off = 3 # Placeholder - linked to a LeaveRequest model

        # New Employees (last 5 hired)
        new_employees_data = Employees.objects.filter(isActive=True).order_by('-contractFrom')[:5]
        new_employees = [{
            "id": emp.id,
            "name": f"{emp.firstname} {emp.surname}",
            "role": emp.position,
            "department": emp.department,
            "joinDate": emp.contractFrom,
            "avatarUrl": f"https://api.dicebear.com/7.x/initials/svg?seed={emp.firstname}%20{emp.surname}"
        } for emp in new_employees_data]

        # Training Programs (upcoming)
        upcoming_trainings_data = TrainingSession.objects.filter(date__gte=today).order_by('date')[:3]
        training_programs = [{
            "id": training.id,
            "title": training.program,
            "date": training.date,
            "participants": 10, # Placeholder - needs to be calculated from TrainingEnrollment
        } for training in upcoming_trainings_data]

        # Upcoming Reviews (last 3 reviews)
        # You'll need a PerformanceReview model to make this dynamic
        upcoming_reviews = [
            {"id": 1, "name": "Robert Mapepi", "date": "2025-11-05", "type": "Annual"},
            {"id": 2, "name": "Emily Dangamvura", "date": "2025-11-08", "type": "Quarterly"},
            {"id": 3, "name": "James Marawa", "date": "2025-11-12", "type": "Project"},
        ]
        
        dashboard_data = {
            "metrics": {
                "totalEmployees": total_employees,
                "totalDepartments": total_departments,
                "openPositions": open_positions,
                "inInterviewStage": in_interview_stage,
                "timeOffRequests": time_off_requests,
                "pendingTimeOff": pending_time_off,
            },
            "newEmployees": new_employees,
            "trainingPrograms": training_programs,
            "upcomingReviews": upcoming_reviews,
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employees.objects.all()
    serializer_class = EmployeeSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class TrainingProgramViewSet(viewsets.ModelViewSet):
    queryset = TrainingProgram.objects.all()
    serializer_class = TrainingProgramSerializer

class TrainingSessionViewSet(viewsets.ModelViewSet):
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer