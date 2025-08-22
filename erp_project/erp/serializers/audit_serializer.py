from rest_framework import serializers
from ..models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "username_attempted",
            "event_type",
            "ip_address",
            "user_agent",
            "timestamp",
        ]
