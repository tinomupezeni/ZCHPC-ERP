"""
Django settings for erp_root project.
"""

from pathlib import Path
from datetime import timedelta  # <-- Moved to the top

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-!7q@p68fnw2-4_s%b_mk2qojko=p40^w131l#%2%v2jy4ghmv='
DEBUG = True
ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1', '192.168.80.92']

# --- Application definition ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "human_resources",
    
    'authentication',
    "payroll",
    "procurement",
    "administration",
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_browser_reload',
]

INTERNAL_IPS = ["127.0.0.1"]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # <-- Moved high up, before CommonMiddleware
    'django.middleware.common.CommonMiddleware', # <-- Kept only one
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.RBACMiddleware',  # Custom RBAC Middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_browser_reload.middleware.BrowserReloadMiddleware", # <-- Kept only one
]

# Set to True for development, but remove CORS_ALLOWED_ORIGINS
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'erp_root.urls'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'erp_root/templates',
            BASE_DIR / 'authentication/templates/registration', # Correct path
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp_root.wsgi.application'

# --- Database ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'erp_db',
        'USER': 'erp_user',
        'PASSWORD': 'erp@1234',
        'HOST': 'localhost',      # Or the IP address of your DB server
        'PORT': '5432',           # Default PostgreSQL port
    }
}

# --- CORS ---
# This list is ignored because CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [ ... ]

CORS_ALLOW_METHODS = [ 'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', ]
CORS_ALLOW_HEADERS = [ 'accept', 'authorization', 'content-type', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with', ]
CORS_EXPOSE_HEADERS = [ 'Content-Type', 'X-CSRFToken', ]


# --- Authentication ---
AUTH_USER_MODEL = 'authentication.CustomUser'

AUTHENTICATION_BACKENDS = [
    'authentication.authentication.EmailBackend',  # Corrected path
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Note: These settings are for 'django-allauth', which is not in INSTALLED_APPS.
# They are not having any effect right now.
ACCOUNT_AUTHENTICATION_METHOD = 'email'
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static & AutoField ---
STATIC_URL = '/static/' # Kept the single, correct definition
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'