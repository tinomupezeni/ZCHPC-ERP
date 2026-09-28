"""
User API serializers.
"""

from rest_framework import serializers

# Platform-level flags only operator bootstrap may set (REM-08). Kept as
# declared fields so a request carrying them is refused with a 400 rather
# than silently ignored.
PRIVILEGED_FLAGS = ("is_staff", "is_superuser")
PRIVILEGED_FLAG_ERROR = (
    "Staff and superuser status cannot be set through this API; "
    "they are granted only by operator bootstrap."
)


def _reject_privileged_flags(attrs):
    errors = {flag: PRIVILEGED_FLAG_ERROR for flag in PRIVILEGED_FLAGS if flag in attrs}
    if errors:
        raise serializers.ValidationError(errors)
    return attrs


class UserResponseSerializer(serializers.Serializer):
    """Serializer for user response data."""

    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)


class CreateUserRequestSerializer(serializers.Serializer):
    """Serializer for user creation requests."""

    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(
        required=False,
        min_length=8,
        write_only=True,
        help_text="If not provided, a temporary password will be generated",
    )
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    # Optional fields for creating employee profile
    role = serializers.IntegerField(required=False, allow_null=True)
    department = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        # An explicit false is harmless and kept working for existing clients.
        for flag in PRIVILEGED_FLAGS:
            if attrs.get(flag) is False:
                attrs.pop(flag)
        return _reject_privileged_flags(attrs)


class CreateUserResponseSerializer(serializers.Serializer):
    """Serializer for user creation response - flat structure for frontend."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Temporary password if none was provided",
    )


class UpdateUserRequestSerializer(serializers.Serializer):
    """Serializer for user update requests."""

    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)

    def validate(self, attrs):
        return _reject_privileged_flags(attrs)


class ChangePasswordRequestSerializer(serializers.Serializer):
    """Serializer for password change requests."""

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="The caller's current (or temporary) password",
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
    )

    def validate_new_password(self, value):
        """Validate new password strength."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters"
            )
        return value
