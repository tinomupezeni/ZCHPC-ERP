
from erp.dependencies import *

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing departments.
    This provides all CRUD operations: list, create, retrieve, update, and destroy.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer