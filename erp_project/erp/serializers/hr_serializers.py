from erp.dependencies import *


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
        

class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Basic serializer matching the model fields."""
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employee', 'date', 'time_in', 'time_out', 'job_number']

class AttendanceRecordAPISerializer(serializers.ModelSerializer):
    """
    API-facing serializer that matches the frontend's expected keys.
    - employeeName -> employee.get_full_name()
    - employeeId -> job_number
    - loginTime -> time_in
    - logoutTime -> time_out
    """
    employeeName = serializers.SerializerMethodField()
    employeeId = serializers.SerializerMethodField()
    loginTime = serializers.TimeField(source='time_in', allow_null=True)
    logoutTime = serializers.TimeField(source='time_out', allow_null=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employeeName', 'employeeId', 'date', 'loginTime', 'logoutTime']

    def get_employeeName(self, obj):
        try:
            full_name = obj.employee.get_full_name()
            return full_name if full_name else getattr(obj.employee, 'username', str(obj.employee_id))
        except Exception:
            return str(obj.employee_id)

    def get_employeeId(self, obj):
        # Frontend displays Job No under this key
        return obj.job_number or ''

