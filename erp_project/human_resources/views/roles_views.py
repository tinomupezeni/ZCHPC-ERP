from rest_framework import viewsets
from ..hr_models import Role, Department
from ..serializers.department_serializer import RoleSerializer, DepartmentSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer