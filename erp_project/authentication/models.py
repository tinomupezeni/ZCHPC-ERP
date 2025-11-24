import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ---------------------------------
# Custom User Manager
# ---------------------------------
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
        
        # FIXED: Removed 'role' as it's no longer on this model
        # extra_fields.setdefault('role', 'ADMIN') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

# ---------------------------------
# Custom User Model
# ---------------------------------
class CustomUser(AbstractUser):
    # Use UUIDField for a proper, unique ID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Set 'username' to None to remove it completely.
    username = None 
    
    # 'email' is now the unique login field.
    email = models.EmailField(unique=True)
    
    # Note: 'first_name', 'last_name', 'is_active' are inherited from AbstractUser

    # FIXED: Added REQUIRED_FIELDS, which is necessary when USERNAME_FIELD is changed
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
 
    # Use our custom manager
    objects = CustomUserManager()

    # --- Security fields ---
    failed_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)

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

    def clean(self):
        # FIXED: Removed all logic related to 'role', 'salary', 'department'
        # That validation logic now belongs in the 'Employee' model.
        super().clean() 

    def save(self, *args, **kwargs):
        # FIXED: Removed all 'employee_id' generation logic.
        # That logic now belongs in the 'Employee' model.
        self.full_clean()  
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

# ---------------------------------
# Audit log for login attempts
# ---------------------------------
class AuditLog(models.Model):
    EVENT_CHOICES = [
        ("SUCCESS", "Login Success"),
        ("FAILED", "Login Failed"),
        ("LOCKOUT", "Account Locked"),
        ("FORCE_RESET", "Forced Password Reset"),
    ]

    user = models.ForeignKey("CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False) # Fixed

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Audit logs are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs cannot be deleted.")

    class Meta:
        verbose_name = "Login Audit Log"
        verbose_name_plural = "Login Audit Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.username_attempted} - {self.event_type} at {self.timestamp}"