"""
Django models for the Identity module.

These models handle user authentication and audit logging.
Table names are preserved from the legacy 'authentication' app for backwards compatibility.
"""
import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model with email as the unique identifier."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)

    # Employee profile relationship
    # employee_profile = models.OneToOneField(
    #     'hr.Employee',  # Reference to Employee model in hr module
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='user_account'
    # )

    # Override groups and user_permissions with explicit related_name to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='identity_user_set',
        related_query_name='identity_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='identity_user_permissions_set',
        related_query_name='identity_user_permission',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    # Security fields
    failed_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'authentication_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def is_locked_out(self):
        if self.lockout_until and self.lockout_until > timezone.now():
            return True
        return False

    def register_failed_attempt(self, max_attempts=5, lockout_minutes=15):
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.lockout_until = timezone.now() + timedelta(minutes=lockout_minutes)
            self.failed_attempts = 0
        self.save(update_fields=["failed_attempts", "lockout_until"])

    def reset_failed_attempts(self):
        self.failed_attempts = 0
        self.lockout_until = None
        self.save(update_fields=["failed_attempts", "lockout_until"])

    def __str__(self):
        return self.email


class AuditLog(models.Model):
    """Immutable audit log for login attempts."""

    EVENT_CHOICES = [
        ("SUCCESS", "Login Success"),
        ("FAILED", "Login Failed"),
        ("LOCKOUT", "Account Locked"),
        ("FORCE_RESET", "Forced Password Reset"),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'authentication_auditlog'
        verbose_name = 'Login Audit Log'
        verbose_name_plural = 'Login Audit Logs'
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Audit logs are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs cannot be deleted.")

    def __str__(self):
        return f"{self.username_attempted} - {self.event_type} at {self.timestamp}"