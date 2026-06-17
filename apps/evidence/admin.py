from django.contrib import admin
from .models import Evidence, ChainOfCustody


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "case", "evidence_type", "status",
                    "file_size_human", "md5_hash", "uploaded_by", "uploaded_at"]
    list_filter = ["status", "evidence_type"]
    readonly_fields = ["md5_hash", "sha256_hash", "ssdeep_hash", "uploaded_at", "updated_at"]


@admin.register(ChainOfCustody)
class ChainOfCustodyAdmin(admin.ModelAdmin):
    list_display = ["evidence", "action", "performed_by", "hash_verified", "timestamp"]
    readonly_fields = ["evidence", "action", "performed_by", "timestamp", "notes", "hash_verified"]

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
