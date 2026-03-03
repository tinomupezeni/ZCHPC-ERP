from rest_framework import serializers
from human_resources.hr_models import Employees


class EmployeeProfileReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading employee profile data.
    Returns all viewable fields for the employee.
    """
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    position_title = serializers.CharField(source='position.title', read_only=True, default=None)
    role_name = serializers.CharField(source='role.name', read_only=True, default=None)
    role_display_name = serializers.CharField(source='role.display_name', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()
    reports_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Employees
        fields = [
            # Identity
            'id',
            'employee_id',
            'first_name',
            'surname',
            'full_name',

            # Personal
            'email',
            'phone',
            'gender',
            'date_of_birth',
            'marital_status',
            'national_id',

            # Employment
            'department_name',
            'position_title',
            'role_name',
            'role_display_name',
            'employee_type',
            'date_joined',
            'contract_from',
            'contract_to',
            'reports_to_name',
            'is_active',

            # Leave
            'leave_days_entitled',

            # Bank (partially hidden for security)
            'bank_name',

            # Emergency contact
            'emergency_contact_name',
            'emergency_contact_number',
            'emergency_contact_relationship',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.surname}"

    def get_reports_to_name(self, obj):
        if obj.reports_to:
            return f"{obj.reports_to.first_name} {obj.reports_to.surname}"
        return None


class EmployeeProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating employee profile.
    Only certain fields are editable by the employee.
    """

    class Meta:
        model = Employees
        fields = [
            # Contact info (editable)
            'phone',

            # Emergency contact (editable)
            'emergency_contact_name',
            'emergency_contact_number',
            'emergency_contact_relationship',
        ]

    def validate_phone(self, value):
        # Basic phone validation
        if value and len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value


class ProfilePhotoSerializer(serializers.Serializer):
    """Serializer for profile photo upload."""
    photo = serializers.ImageField()

    def validate_photo(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Invalid image type. Allowed types: JPEG, PNG, GIF"
            )

        return value
