from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Employees)
admin.site.register(TrainingProgram)
admin.site.register(Job)


@admin.register(AuditLog)
class LoginAuditLogAdmin(admin.ModelAdmin):
    list_display = ("username_attempted", "event_type", "ip_address", "timestamp")
    list_filter = ("event_type", "timestamp")
    search_fields = ("username_attempted", "ip_address", "user_agent")

    def has_add_permission(self, request):
        return False  # No manual creation

    def has_change_permission(self, request, obj=None):
        return False  # No editing

    def has_delete_permission(self, request, obj=None):
        return False  # No deletion
