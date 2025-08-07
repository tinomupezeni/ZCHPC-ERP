from rest_framework import serializers
from ..models import TrainingCertification, TrainingEnrollment, TrainingProgram, TrainingSession
from django.utils.timezone import now
from django.utils import timezone


class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = '__all__'
        read_only_fields = ('id',)  # ID is auto-generated and read-only

    def validate_title(self, value):
        """Validate that title is not empty and unique"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_duration(self, value):
        """Validate duration format (e.g., '8 Hours', '2 Days')"""
        if value and not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Duration must include a numeric value")
        return value
    
class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = ['id', 'program', 'trainer', 'date', 'venue', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date(self, value):
        # Validate that session date is not in the past
        if value < timezone.now().date():
            raise serializers.ValidationError("Session date cannot be in the past")
        return value
    
class TrainingEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEnrollment
        fields = ['id', 'employee', 'program', 'session_date', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_session_date(self, value):
       # Validate that session date is not in the past
        if value < timezone.now().date():
            raise serializers.ValidationError("Session date cannot be in the past")
        return value
    
class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingCertification
        fields = ['id', 'employee', 'program', 'issue_date', 'expiry_date', 'status']