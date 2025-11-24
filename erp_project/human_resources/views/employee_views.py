# hr/views/employee_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..hr_models import Employee
from ..serializers.employee_serializers import EmployeeSerializer
from ..services import employee_services as hr_service
# from ..permissions import RolePermission # Import your custom permission

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Employees.
    - create: Registers a new employee.
    - list: Retrieves all employees.
    - retrieve: Retrieves a single employee.
    - update: Updates an employee.
    - destroy: Deactivates an employee (soft delete).
    """
    queryset = Employee.objects.all().order_by('surname', 'first_name')
    serializer_class = EmployeeSerializer
    # permission_classes = [RolePermission(["HR"])] # Apply permissions to the whole viewset

    def get_queryset(self):
        # By default, only show active employees in lists
        return Employee.objects.filter(is_active=True).order_by('surname', 'first_name')

    def create(self, request, *args, **kwargs):
        """
        Refactored register_employee.
        The data cleaning logic is now in the service.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Call the service
        employee = hr_service.create_employee(serializer.validated_data)
        
        data = EmployeeSerializer(employee).data
        data['message'] = "Employee created successfully!"
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
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
        """
        Performs a soft-delete by deactivating the employee.
        """
        instance = self.get_object()
        hr_service.deactivate_employee(instance) # Use soft-delete
        return Response(status=status.HTTP_204_NO_CONTENT)