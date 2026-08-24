from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from modules.bff.orchestrators.employee_orchestrator import EmployeeOrchestrator
from modules.bff.serializers.unified_employee import UnifiedEmployeeProfileSerializer

class BFFEmployeeDetailView(APIView):
    def get(self, request, uuid):
        profile_data = EmployeeOrchestrator.get_full_profile(uuid)
        
        if not profile_data:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UnifiedEmployeeProfileSerializer(data=profile_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, uuid):
        # We accept partial or full data from the frontend
        updated_profile_data = EmployeeOrchestrator.update_full_profile(uuid, request.data)
        
        if not updated_profile_data:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UnifiedEmployeeProfileSerializer(data=updated_profile_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
