from django.contrib import admin
from .models import Case, CaseNote


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ["case_number", "title", "status", "priority", "created_by", "created_at"]
    list_filter = ["status", "priority", "case_type"]
    search_fields = ["case_number", "title", "description"]
    readonly_fields = ["case_number", "created_at", "updated_at", "closed_at"]

@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ["case", "author", "is_private", "created_at"]
    list_filter = ["is_private"]
