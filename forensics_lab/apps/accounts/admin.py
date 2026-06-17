from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "role", "badge_number", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name", "badge_number"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Forensics Info", {"fields": ("role", "badge_number", "department", "phone")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "resource_type", "resource_id", "ip_address", "timestamp"]
    list_filter = ["action", "resource_type"]
    search_fields = ["user__email", "description"]
    readonly_fields = ["user", "action", "resource_type", "resource_id",
                       "description", "ip_address", "user_agent", "timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
