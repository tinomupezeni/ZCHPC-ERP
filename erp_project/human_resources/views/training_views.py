# hr/views/training_views.py
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from ..hr_models import (
    TrainingProgram, 
    TrainingSession, 
    TrainingEnrollment, 
    TrainingCertification
)
from ..serializers.employee_serializers import (
    TrainingProgramSerializer, 
    TrainingSessionSerializer,
    TrainingEnrollmentSerializer,
    TrainingCertificationSerializer
)
from ..services import employee_services as hr_service

class TrainingProgramViewSet(viewsets.ModelViewSet):
    """
    Refactors training_program_list and training_program_detail.
    """
    queryset = TrainingProgram.objects.all()
    serializer_class = TrainingProgramSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'category'] # Handles category filtering

    # Handles 'mandatory' filtering
    def get_queryset(self):
        queryset = super().get_queryset()
        mandatory = self.request.query_params.get('mandatory')
        if mandatory in ['true', 'false']:
            queryset = queryset.filter(mandatory=(mandatory.lower() == 'true'))
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        program = hr_service.create_training_program(serializer.validated_data)
        return Response(TrainingProgramSerializer(program).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        program = hr_service.update_training_program(instance, serializer.validated_data)
        return Response(TrainingProgramSerializer(program).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_training_program(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class TrainingSessionViewSet(viewsets.ModelViewSet):
    """
    Refactors training_session_list and training_session_detail.
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
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        session = hr_service.update_training_session(instance, serializer.validated_data)
        return Response(TrainingSessionSerializer(session).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_training_session(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class TrainingEnrollmentViewSet(viewsets.ModelViewSet):
    """
    Refactors training_enrollment_list and training_enrollment_detail.
    """
    queryset = TrainingEnrollment.objects.all()
    serializer_class = TrainingEnrollmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = hr_service.create_enrollment(serializer.validated_data)
        return Response(TrainingEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        enrollment = hr_service.update_enrollment(instance, serializer.validated_data)
        return Response(TrainingEnrollmentSerializer(enrollment).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_enrollment(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class TrainingCertificationViewSet(viewsets.ModelViewSet):
    """
    Refactors certification_list, certification_detail, and certification_search.
    """
    queryset = TrainingCertification.objects.all()
    serializer_class = TrainingCertificationSerializer
    filter_backends = [filters.SearchFilter]
    # This handles your certification_search view
    search_fields = ['certification_name', 'employee__first_name', 'employee__surname']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cert = hr_service.create_certification(serializer.validated_data)
        return Response(TrainingCertificationSerializer(cert).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        cert = hr_service.update_certification(instance, serializer.validated_data)
        return Response(TrainingCertificationSerializer(cert).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        hr_service.delete_certification(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)