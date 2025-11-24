# hr/views/attendance_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from ..hr_models import AttendanceRecord
from ..serializers.employee_serializers import AttendanceRecordSerializer
from ..services import employee_services as hr_service

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    Refactors attendance_list and attendance_delete.
    Includes a custom action for bulk_upload.
    """
    queryset = AttendanceRecord.objects.all().order_by('-date')
    serializer_class = AttendanceRecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = hr_service.create_attendance_record(serializer.validated_data)
        return Response(AttendanceRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_attendance_record(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # We disable PUT/PATCH on the main endpoint
    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def partial_update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False, 
        methods=['POST'], 
        parser_classes=[MultiPartParser, FormParser]
    )
    def bulk_upload(self, request):
        """
        Refactored attendance_bulk_upload.
        The logic is now in the service layer.
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'detail': 'No file provided under "file" key.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            summary = hr_service.process_attendance_upload(file_obj)
            return Response(
                {'message': 'Upload processed', **summary}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)