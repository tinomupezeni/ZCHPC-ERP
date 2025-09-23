from erp.dependencies import *

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
