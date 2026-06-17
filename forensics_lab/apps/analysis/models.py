from django.db import models
from apps.accounts.models import User
from apps.cases.models import Case
from apps.evidence.models import Evidence


class AnalysisTask(models.Model):
    """
    Represents a single forensic analysis job run on a piece of evidence.
    These run in the background via Celery so the user doesn't have to wait.
    """

    class TaskType(models.TextChoices):
        YARA_SCAN = "yara_scan", "YARA Malware Scan"
        FILE_TYPE = "file_type", "File Type Detection"
        METADATA = "metadata", "Metadata Extraction"
        STRING_EXTRACT = "string_extract", "String Extraction"
        HASH_VERIFY = "hash_verify", "Hash Verification"
        TIMELINE = "timeline", "Timeline Analysis"
        FULL = "full", "Full Analysis"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE,
                                 related_name="analysis_tasks")
    case = models.ForeignKey(Case, on_delete=models.CASCADE,
                             related_name="analysis_tasks")
    task_type = models.CharField(max_length=30, choices=TaskType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    celery_task_id = models.CharField(max_length=255, blank=True)

    # Results stored as JSON
    result_summary = models.TextField(blank=True)
    result_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    # Threat intel
    is_suspicious = models.BooleanField(default=False)
    threat_score = models.IntegerField(default=0)   # 0-100
    yara_matches = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "analysis_task"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_type} on {self.evidence.original_filename} [{self.status}]"


class TimelineEvent(models.Model):
    """
    A single event extracted from evidence — builds the attack timeline.
    When was each file created? Accessed? Modified? Deleted?
    """

    class EventType(models.TextChoices):
        FILE_CREATED = "file_created", "File Created"
        FILE_MODIFIED = "file_modified", "File Modified"
        FILE_ACCESSED = "file_accessed", "File Accessed"
        FILE_DELETED = "file_deleted", "File Deleted"
        NETWORK_CONNECTION = "network_connection", "Network Connection"
        PROCESS_EXECUTION = "process_execution", "Process Executed"
        LOGIN_EVENT = "login_event", "Login Event"
        USB_CONNECTED = "usb_connected", "USB Device Connected"
        MALWARE_DETECTED = "malware_detected", "Malware Detected"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="timeline_events")
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE,
                                 related_name="timeline_events", null=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    event_time = models.DateTimeField()
    description = models.TextField()
    artifact = models.CharField(max_length=500, blank=True)   # file path, IP, etc.
    is_suspicious = models.BooleanField(default=False)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analysis_timeline_event"
        ordering = ["event_time"]

    def __str__(self):
        return f"{self.event_type} at {self.event_time} — {self.artifact}"
