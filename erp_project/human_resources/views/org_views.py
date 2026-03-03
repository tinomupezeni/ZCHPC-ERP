from rest_framework import viewsets, serializers
from ..hr_models import AllowanceType, DeductionType, Department, Position
from ..serializers.reports_serializers import DeductionTypeSerializer, DepartmentSerializer, PositionSerializer


class AllowanceTypeSerializer(serializers.ModelSerializer):
    """Serializer for AllowanceType model"""
    class Meta:
        model = AllowanceType
        fields = ['id', 'name', 'description', 'amount']


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

    def get_queryset(self):
        """
        Optionally filter positions by department.
        Usage: /api/positions/?department_id=1
        """
        queryset = Position.objects.all()
        dept_id = self.request.query_params.get('department_id')
        if dept_id:
            queryset = queryset.filter(department_id=dept_id)
        return queryset


class AllowanceTypeViewSet(viewsets.ModelViewSet):
    """
    Manage Allowance Types (e.g., Housing, Transport, Lunch)
    """
    queryset = AllowanceType.objects.all()
    serializer_class = AllowanceTypeSerializer


class DeductionTypeViewSet(viewsets.ModelViewSet):
    """
    Manage Tax and Deduction Categories (e.g., NSSA, PAYE, Medical Aid)
    """
    queryset = DeductionType.objects.all()
    serializer_class = DeductionTypeSerializer


