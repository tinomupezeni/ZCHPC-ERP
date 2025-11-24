# hr/views.py
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

# Import all necessary models
from ..hr_models import (
    Employees, 
    Department, 
    TrainingProgram, 
    TrainingSession,
    Job,
    JobApplication,
    LeaveRequest
)

# Import all serializers
from ..serializers.employee_serializers import (
    EmployeeSerializer, 
    DepartmentSerializer, 
    TrainingProgramSerializer, 
    TrainingSessionSerializer
)

# Import the new service layer
from ..services import employee_services as hr_service


class HrDashboardView(APIView):
    """
    A view to return all necessary data for the HR dashboard.
    """
    # permission_classes = [IsAuthenticated, IsHRManager] # Add permissions

    def get(self, request):
        today = timezone.now().date()
        
        # Metrics - Now using dynamic queries from your new models
        total_employees = Employees.objects.filter(is_active=True).count()
        total_departments = Department.objects.count()
        # Assuming 'OPEN' is the value for active jobs
        open_positions = Job.objects.filter(status='OPEN').count()
        in_interview_stage = JobApplication.objects.filter(status='Interview').count()
        time_off_requests = LeaveRequest.objects.filter(
            status='Pending', 
            start_date__gte=today
        ).count()
        
        # New Employees (last 5 hired) - Fixed with snake_case and ForeignKeys
        new_employees_data = Employees.objects.filter(is_active=True).order_by('-date_joined')[:5]
        new_employees = [{
            "id": emp.id,
            "name": f"{emp.first_name} {emp.surname}",
            "role": emp.position.title if emp.position else "N/A",
            "department": emp.department.name if emp.department else "N/A",
            "joinDate": emp.date_joined,
            "avatarUrl": f"https://api.dicebear.com/7.x/initials/svg?seed={emp.first_name}%20{emp.surname}"
        } for emp in new_employees_data]

        # Training Programs (upcoming) - Fixed with ForeignKeys and participant count
        upcoming_trainings_data = TrainingSession.objects.filter(date__gte=today).order_by('date')[:3]
        training_programs = [{
            "id": training.id,
            "title": training.program.title, # Correctly uses FK
            "date": training.date,
            "participants": training.enrollments.count(), # Correctly counts participants
        } for training in upcoming_trainings_data]

        # Upcoming Reviews (Placeholder)
        # TODO: Replace with a query to a PerformanceReview model when created
        upcoming_reviews = [
            {"id": 1, "name": "Robert Mapepi", "date": "2025-11-05", "type": "Annual"},
            {"id": 2, "name": "Emily Dangamvura", "date": "2025-11-08", "type": "Quarterly"},
        ]
        
        dashboard_data = {
            "metrics": {
                "totalEmployees": total_employees,
                "totalDepartments": total_departments,
                "openPositions": open_positions,
                "inInterviewStage": in_interview_stage,
                "pendingTimeOff": time_off_requests,
            },
            "newEmployees": new_employees,
            "trainingPrograms": training_programs,
            "upcomingReviews": upcoming_reviews,
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Employees.
    Logic is handled by the service layer.
    """
    queryset = Employees.objects.filter(is_active=True)
    serializer_class = EmployeeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = hr_service.create_employee(serializer.validated_data)
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = hr_service.update_employee(instance, serializer.validated_data)
        return Response(EmployeeSerializer(employee).data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        employee = hr_service.update_employee(instance, serializer.validated_data)
        return Response(EmployeeSerializer(employee).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.deactivate_employee(instance) # Use soft-delete
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Departments.
    Logic is handled by the service layer.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = hr_service.create_department(serializer.validated_data)
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        department = hr_service.update_department(instance, serializer.validated_data)
        return Response(DepartmentSerializer(department).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_department(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingProgramViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Training Programs.
    Logic is handled by the service layer.
    """
    queryset = TrainingProgram.objects.all()
    serializer_class = TrainingProgramSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        program = hr_service.create_training_program(serializer.validated_data)
        return Response(TrainingProgramSerializer(program).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        program = hr_service.update_training_program(instance, serializer.validated_data)
        return Response(TrainingProgramSerializer(program).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_training_program(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingSessionViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Training Sessions.
    Logic is handled by the service layer.
    """
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = hr_service.create_training_session(serializer.validated_data)
        return Response(TrainingSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        session = hr_service.update_training_session(instance, serializer.validated_data)
        return Response(TrainingSessionSerializer(session).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_training_session(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)