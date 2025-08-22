from rest_framework import generics, permissions, filters
from ..models import AuditLog
from ..serializers.audit_serializer import AuditLogSerializer

class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]  # restrict to admins
    queryset = AuditLog.objects.all().order_by("-timestamp")

    # Optional filters (search by username or event type)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username_attempted", "event_type", "ip_address"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]
