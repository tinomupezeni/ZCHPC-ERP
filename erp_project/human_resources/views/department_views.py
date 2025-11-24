from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers.department_serializer import DepartmentSerializer
from ..services.department_services import DepartmentService

class DepartmentListCreateView(APIView):
    def get(self, request):
        departments = DepartmentService.get_all_departments()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            dept = DepartmentService.create_department(serializer.validated_data)
            return Response(DepartmentSerializer(dept).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentDetailView(APIView):
    def get(self, request, dept_id):
        dept = DepartmentService.get_department(dept_id)
        serializer = DepartmentSerializer(dept)
        return Response(serializer.data)

    def put(self, request, dept_id):
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            dept = DepartmentService.update_department(dept_id, serializer.validated_data)
            return Response(DepartmentSerializer(dept).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, dept_id):
        DepartmentService.delete_department(dept_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
