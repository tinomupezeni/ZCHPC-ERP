"""
Authentication API serializers.
"""

from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    """Serializer for login requests."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for successful login response."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = serializers.DictField(read_only=True)


class TokenRefreshRequestSerializer(serializers.Serializer):
    """Serializer for token refresh requests."""

    refresh = serializers.CharField(required=True)


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Serializer for token refresh response."""

    access = serializers.CharField(read_only=True)


class AuditLogSerializer(serializers.Serializer):
    """Serializer for audit log entries."""

    id = serializers.IntegerField(read_only=True)
    user_id = serializers.UUIDField(read_only=True, allow_null=True)
    username_attempted = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)


class RoleSerializer(serializers.Serializer):
    """Serializer for role data."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    permissions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )
    is_admin = serializers.BooleanField(read_only=True)
