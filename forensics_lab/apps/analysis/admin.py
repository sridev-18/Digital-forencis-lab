from django.contrib import admin
from .models import AnalysisTask, TimelineEvent

@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ["evidence", "task_type", "status", "is_suspicious", "threat_score", "created_at"]
    list_filter = ["status", "task_type", "is_suspicious"]

@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ["case", "event_type", "event_time", "artifact", "is_suspicious"]
    list_filter = ["event_type", "is_suspicious"]
