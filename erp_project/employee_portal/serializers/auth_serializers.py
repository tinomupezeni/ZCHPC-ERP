from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from human_resources.hr_models import Employees


class EmployeeLoginSerializer(serializers.Serializer):
    """
    Serializer for employee portal login using EC number (employee_id) + password.
    """
    ec_number = serializers.CharField(
        max_length=20,
        help_text="Employee ID (e.g., EMP0001)"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        ec_number = attrs.get('ec_number', '').strip().upper()
        password = attrs.get('password', '')

        if not ec_number or not password:
            raise serializers.ValidationError("EC number and password are required.")

        # Find employee by EC number
        try:
            employee = Employees.objects.select_related('user', 'role', 'department', 'position').get(
                employee_id=ec_number
            )
        except Employees.DoesNotExist:
            raise serializers.ValidationError("Invalid EC number or password.")

        # Check if employee has a linked user account
        if not employee.user:
            raise serializers.ValidationError(
                "No user account linked to this employee. Please contact HR."
            )

        user = employee.user

        # Check if account is active
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive. Please contact HR.")

        # Check if employee is active
        if not employee.is_active:
            raise serializers.ValidationError("Employee record is inactive. Please contact HR.")

        # Check lockout
        if user.is_locked_out():
            raise serializers.ValidationError(
                "Account is temporarily locked due to multiple failed login attempts. "
                "Please try again later."
            )

        # Validate password
        if not user.check_password(password):
            user.register_failed_attempt()
            raise serializers.ValidationError("Invalid EC number or password.")

        # Reset failed attempts on successful login
        user.reset_failed_attempts()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        attrs['user'] = user
        attrs['employee'] = employee
        attrs['tokens'] = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

        return attrs


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for employee profile data returned after login.
    """
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    position_title = serializers.CharField(source='position.title', read_only=True, default=None)
    role_name = serializers.CharField(source='role.name', read_only=True, default=None)
    role_display_name = serializers.CharField(source='role.display_name', read_only=True, default=None)
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = Employees
        fields = [
            'id',
            'employee_id',
            'first_name',
            'surname',
            'full_name',
            'email',
            'phone',
            'gender',
            'date_of_birth',
            'date_joined',
            'department_name',
            'position_title',
            'role_name',
            'role_display_name',
            'employee_type',
            'is_active',
            'leave_days_entitled',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.surname}"


class EmployeeLoginResponseSerializer(serializers.Serializer):
    """
    Serializer for the login response structure.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    employee = EmployeeProfileSerializer()


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for refreshing JWT tokens.
    """
    refresh = serializers.CharField()

    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            refresh = RefreshToken(attrs['refresh'])
            attrs['access'] = str(refresh.access_token)
        except TokenError as e:
            raise serializers.ValidationError(str(e))

        return attrs
