
from ..models import Department
from ..serializers.department_serializer import DepartmentSerializer
from rest_framework.views import APIView
class DepartmentViewSet(APIView):
    """
    A simple ViewSet for viewing and editing departments.
    This provides all CRUD operations: list, create, retrieve, update, and destroy.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer