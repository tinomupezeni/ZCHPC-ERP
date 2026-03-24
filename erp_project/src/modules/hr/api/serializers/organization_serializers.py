"""
Organization API serializers (Department, Position).
"""

from rest_framework import serializers


class DepartmentResponseSerializer(serializers.Serializer):
    """Serializer for department response data."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)
    employee_count = serializers.IntegerField(read_only=True)


class CreateDepartmentRequestSerializer(serializers.Serializer):
    """Serializer for creating a department."""

    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateDepartmentRequestSerializer(serializers.Serializer):
    """Serializer for updating a department."""

    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class PositionResponseSerializer(serializers.Serializer):
    """Serializer for position response data."""

    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    department_id = serializers.IntegerField(read_only=True)
    department_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True)


class CreatePositionRequestSerializer(serializers.Serializer):
    """Serializer for creating a position."""

    title = serializers.CharField(max_length=100)
    department_id = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True, default="")


class UpdatePositionRequestSerializer(serializers.Serializer):
    """Serializer for updating a position."""

    title = serializers.CharField(max_length=100, required=False)
    department_id = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
