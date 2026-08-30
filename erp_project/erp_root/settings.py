"""
Django settings for ZCHPC ERP project.

Architecture:
    This project follows a modular monolith architecture with clean architecture
    principles. All API endpoints are at /api/v2/*

    Modules (src/modules/):
        - identity: CustomUser, AuditLog, JWT authentication
        - hr: Employee, Department, Position, Role
        - attendance: AttendanceRecord
        - leave: LeaveType, LeaveBalance, LeaveRequest, CompanyEvent
        - recruitment: Job, Candidate, JobApplication
        - payroll: Payroll, TaxBracket, ExchangeRate
        - accounts: Currency, AccountChart, Journal, AccountMove
        - procurement: Vendor, PurchaseRequest, PurchaseOrder
        - portal: ExpenseClaim, SupportTicket, Document, Notification

    Each module follows clean architecture layers:
        - api/: Views, serializers, URL routing
        - application/: Use cases, services, commands, queries
        - domain/: Entities, value objects, events, business rules
        - infrastructure/: Repositories, external adapters, Django models

Module Structure:
    src/
    ├── shared/           # Shared kernel (base classes, value objects)
    └── modules/          # Feature modules

For more details, see docs/ARCHITECTURE.md
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Add src directory to Python path for clean imports
# This enables: from modules.hr.domain.entities import Employee
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- Core Settings (from environment variables for Docker) ---
# SECURITY FIX: Removed hardcoded fallback. App will fail to start if not set.
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required.")

# SECURITY FIX: Default to False. Developers must explicitly set DEBUG=True in .env
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Production domains: zchpcerp.zchpc.ac.zw (main ERP), employees.zchpc.ac.zw (portal)
DEFAULT_ALLOWED_HOSTS = ",".join(
    [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "api",
        "nginx",
        "zchpcerp.zchpc.ac.zw",
        "employees.zchpc.ac.zw",
        ".zchpc.ac.zw",  # Wildcard for all subdomains
    ]
)
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS).split(",")

# --- Application definition ---

INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # =========================================================================
    # New Modular Architecture Apps (src/modules/)
    # =========================================================================
    # Each module contains its own models, views, serializers, and business logic.
    # Models are in infrastructure/persistence/models.py with db_table set
    # to match existing tables for backwards compatibility.
    # =========================================================================
    'modules.identity.apps.IdentityConfig',       # CustomUser, AuditLog
    'modules.hr.apps.HrConfig',                   # Employee, Department, Position
    'modules.attendance.apps.AttendanceConfig',   # AttendanceRecord
    'modules.leave.apps.LeaveConfig',             # LeaveType, LeaveBalance, LeaveRequest
    'modules.recruitment.apps.RecruitmentConfig',
    'modules.bff.apps.BffConfig',
    'modules.payroll.apps.PayrollConfig',         # Payroll, TaxBracket, ExchangeRate
    'modules.accounts.apps.AccountsConfig',       # Account, Journal, JournalEntry
    'modules.procurement.apps.ProcurementConfig', # Vendor, PurchaseRequest, PurchaseOrder
    'modules.portal.apps.PortalConfig',           # ExpenseClaim, SupportTicket, Document

    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_browser_reload",
]

INTERNAL_IPS = ["127.0.0.1"]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'modules.identity.infrastructure.middleware.JWTAuthenticationMiddleware',  # JWT Auth
    'modules.identity.infrastructure.middleware.ModuleAccessMiddleware', # Module Access Control
    'modules.identity.infrastructure.middleware.RBACMiddleware',  # Role-based access control
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = "erp_root.urls"

# SECURITY FIX: Added DEFAULT_PERMISSION_CLASSES to fail-closed (IsAuthenticated).
# Any endpoint that should be public MUST explicitly set permission_classes = [AllowAny]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "erp_root/templates",
            BASE_DIR
            / "src/modules/identity/templates/registration",  # New modular location
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "erp_root.wsgi.application"

# --- Database ---
# Uses environment variables for Docker deployment
if os.environ.get('USE_SQLITE', 'False').lower() in ('true', '1', 'yes'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'erp_db'),
            'USER': os.environ.get('DB_USER', 'erp_user'),
            # SECURITY FIX: Removed hardcoded password fallback.
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
    }

# --- CORS ---
# SECURITY FIX: Default to False. Wildcard CORS is dangerous in production.
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False").lower() in (
    "true",
    "1",
    "yes",
)

# Production CORS origins (used when CORS_ALLOW_ALL_ORIGINS=False)
DEFAULT_CORS_ORIGINS = ",".join(
    [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "https://zchpcerp.zchpc.ac.zw",
        "https://employees.zchpc.ac.zw",
        "http://zchpcerp.zchpc.ac.zw",
        "http://employees.zchpc.ac.zw",
    ]
)
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ORIGINS
).split(",")

# SECURITY FIX: Default to False. Only enable if cross-origin cookies/sessions are explicitly required.
# Since the frontend uses JWT in Authorization headers, this is likely not needed.
CORS_ALLOW_CREDENTIALS = os.environ.get("CORS_ALLOW_CREDENTIALS", "False").lower() in (
    "true",
    "1",
    "yes",
)

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]


# --- Authentication ---
AUTH_USER_MODEL = "identity.CustomUser"  # New modular location

AUTHENTICATION_BACKENDS = [
    "modules.identity.infrastructure.authentication.EmailBackend",  # New modular location
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Note: These settings are for 'django-allauth', which is not in INSTALLED_APPS.
# They are not having any effect right now.
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False

# --- JWT ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
}

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static & Media Files ---
STATIC_URL = os.environ.get("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "mediafiles"

# --- CSRF Trusted Origins (for Docker/production) ---
DEFAULT_CSRF_ORIGINS = ",".join(
    [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "https://zchpcerp.zchpc.ac.zw",
        "https://employees.zchpc.ac.zw",
        "http://zchpcerp.zchpc.ac.zw",
        "http://employees.zchpc.ac.zw",
    ]
)
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", DEFAULT_CSRF_ORIGINS
).split(",")

# --- AutoField ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Email ---
# Defaults to the console backend (prints emails to the terminal) for local
# development/testing. In production, set EMAIL_BACKEND to the SMTP backend
# via environment variable and configure EMAIL_HOST/PORT/USER/PASSWORD.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', 'ZCHPC ERP <noreply@zchpc.ac.zw>'
)
