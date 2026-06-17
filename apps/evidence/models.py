import hashlib
import os
from django.db import models
from apps.accounts.models import User
from apps.cases.models import Case


def evidence_upload_path(instance, filename):
    """Store evidence files in organized folders: evidence/CASE-2024-0001/filename"""
    return f"evidence/{instance.case.case_number}/{filename}"


class Evidence(models.Model):
    """
    A single piece of digital evidence tied to a case.
    When a file is uploaded, we automatically:
      1. Calculate its MD5 and SHA256 hash (fingerprint)
      2. Record who uploaded it and when
      3. Detect what type of file it is
      4. Start the chain of custody log
    """

    class EvidenceType(models.TextChoices):
        DISK_IMAGE = "disk_image", "Disk Image"
        MEMORY_DUMP = "memory_dump", "Memory Dump"
        LOG_FILE = "log_file", "Log File"
        DOCUMENT = "document", "Document"
        IMAGE = "image", "Image / Photo"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        NETWORK_CAPTURE = "network_capture", "Network Capture (PCAP)"
        EXECUTABLE = "executable", "Executable / Binary"
        ARCHIVE = "archive", "Archive (ZIP, RAR)"
        DATABASE = "database", "Database File"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Analysis"
        ANALYSING = "analysing", "Analysing"
        ANALYSED = "analysed", "Analysis Complete"
        FLAGGED = "flagged", "Flagged — Suspicious"
        CLEAN = "clean", "Clean"

    # Relationship
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="evidence_set")

    # File info
    file = models.FileField(upload_to=evidence_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)          # bytes
    file_type = models.CharField(max_length=100, blank=True)  # MIME type from python-magic
    evidence_type = models.CharField(max_length=30, choices=EvidenceType.choices,
                                     default=EvidenceType.OTHER)

    # Cryptographic hashes — these are the proof of integrity
    md5_hash = models.CharField(max_length=32, blank=True)
    sha256_hash = models.CharField(max_length=64, blank=True)
    ssdeep_hash = models.TextField(blank=True)  # Fuzzy hash for similarity matching

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)  # comma-separated tags

    # Who and when
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name="uploaded_evidence")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Source info
    source_device = models.CharField(max_length=255, blank=True)
    source_location = models.CharField(max_length=255, blank=True)
    acquisition_tool = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "evidence_evidence"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.case.case_number})"

    @property
    def file_size_human(self):
        """Returns human-readable file size: 1.2 MB"""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def compute_hashes(self):
        """
        Read the file and compute MD5 + SHA256 hashes.
        Called automatically after upload.
        These hashes prove the file hasn't been tampered with.
        """
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()

        self.file.seek(0)
        for chunk in iter(lambda: self.file.read(8192), b""):
            md5.update(chunk)
            sha256.update(chunk)
        self.file.seek(0)

        self.md5_hash = md5.hexdigest()
        self.sha256_hash = sha256.hexdigest()

    def get_tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class ChainOfCustody(models.Model):
    """
    Every action on a piece of evidence is logged here.
    Who touched it, what they did, when.
    This is what makes evidence admissible in court.
    """

    class Action(models.TextChoices):
        ACQUIRED = "acquired", "Evidence Acquired"
        UPLOADED = "uploaded", "Uploaded to Lab"
        HASHED = "hashed", "Integrity Hash Computed"
        ANALYSED = "analysed", "Analysis Performed"
        EXPORTED = "exported", "Exported / Downloaded"
        TRANSFERRED = "transferred", "Transferred"
        VERIFIED = "verified", "Hash Verified"
        FLAGGED = "flagged", "Flagged as Suspicious"
        NOTE_ADDED = "note_added", "Note Added"

    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE,
                                 related_name="custody_chain")
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    hash_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "evidence_chain_of_custody"
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.evidence.original_filename} — {self.action} — {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Chain of custody records are immutable.")
        super().save(*args, **kwargs)
