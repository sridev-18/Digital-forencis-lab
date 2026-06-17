from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with forensics-specific roles.
    Every person who logs into the lab is one of these roles.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"                        # Full access, manages users
        INVESTIGATOR = "investigator", "Investigator"  # Creates and manages cases
        ANALYST = "analyst", "Analyst"                 # Runs analysis, reads cases
        VIEWER = "viewer", "Viewer"                    # Read-only access

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)
    badge_number = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def full_name(self):
        return self.get_full_name() or self.email

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_investigator(self):
        return self.role in [self.Role.ADMIN, self.Role.INVESTIGATOR]

    def is_analyst(self):
        return self.role in [self.Role.ADMIN, self.Role.INVESTIGATOR, self.Role.ANALYST]


class AuditLog(models.Model):
    """
    Every single action by every user is recorded here.
    This is your chain of custody proof — legally admissible.
    Cannot be updated or deleted — append-only.
    """

    class Action(models.TextChoices):
        LOGIN = "login", "User Login"
        LOGOUT = "logout", "User Logout"
        CREATE = "create", "Created"
        READ = "read", "Viewed"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"
        UPLOAD = "upload", "Uploaded Evidence"
        DOWNLOAD = "download", "Downloaded Evidence"
        ANALYSE = "analyse", "Ran Analysis"
        EXPORT = "export", "Exported Report"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    resource_type = models.CharField(max_length=50)   # e.g. "Case", "Evidence"
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.timestamp}"

    def save(self, *args, **kwargs):
        # Prevent any updates — audit logs are immutable
        if self.pk:
            raise PermissionError("Audit logs cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs cannot be deleted.")
