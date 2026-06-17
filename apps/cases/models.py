from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class Case(models.Model):
    """
    A forensic investigation case.
    Think of this as the main folder that everything else belongs to.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On Hold"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class CaseType(models.TextChoices):
        DATA_BREACH = "data_breach", "Data Breach"
        RANSOMWARE = "ransomware", "Ransomware Attack"
        INSIDER_THREAT = "insider_threat", "Insider Threat"
        PHISHING = "phishing", "Phishing / Social Engineering"
        MALWARE = "malware", "Malware Infection"
        NETWORK_INTRUSION = "network_intrusion", "Network Intrusion"
        FRAUD = "fraud", "Digital Fraud"
        OTHER = "other", "Other"

    # Core fields
    case_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    case_type = models.CharField(max_length=30, choices=CaseType.choices, default=CaseType.OTHER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    # People
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name="created_cases")
    assigned_to = models.ManyToManyField(User, blank=True, related_name="assigned_cases")

    # Incident details
    incident_date = models.DateTimeField(null=True, blank=True)
    incident_location = models.CharField(max_length=255, blank=True)
    suspect_name = models.CharField(max_length=255, blank=True)
    victim_name = models.CharField(max_length=255, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cases_case"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case_number} — {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate case number on first save: CASE-2024-0001
        if not self.case_number:
            year = timezone.now().year
            last = Case.objects.filter(case_number__startswith=f"CASE-{year}-").count()
            self.case_number = f"CASE-{year}-{str(last + 1).zfill(4)}"
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def evidence_count(self):
        return self.evidence_set.count()

    @property
    def open_tasks_count(self):
        return self.analysis_tasks.filter(status="pending").count()

    def get_priority_color(self):
        colors = {
            "low": "green", "medium": "amber",
            "high": "coral", "critical": "red"
        }
        return colors.get(self.priority, "gray")


class CaseNote(models.Model):
    """
    Investigators can add notes to a case during the investigation.
    These are part of the official record and cannot be deleted.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    is_private = models.BooleanField(default=False)  # Private = only author + admin can see
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cases_note"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.case.case_number} by {self.author}"
