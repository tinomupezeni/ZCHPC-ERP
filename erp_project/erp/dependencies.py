# =====================
# Python Standard Library
# =====================
import uuid
import csv
import calendar
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# =====================
# Django Core
# =====================
from django.urls import path, include
from django.db import models, transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import admin
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import AbstractUser

# =====================
# Django REST Framework
# =====================
from rest_framework import (
    serializers,
    viewsets,
    generics,
    permissions,
    filters,
    status
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.routers import DefaultRouter
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

# =====================
# JWT
# =====================
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# =====================
# JSON validation
# =====================
from jsonschema import ValidationError

# =====================
# Local App Imports
# =====================
from .models import *
from .serializers import *
from .serializers.payroll_serializer import *
from .serializers.department_serializer import *
from .serializers.employee_serializers import *
from .serializers.hr_serializers import *
from .serializers.jobs_serializer import JobSerializer
from .serializers.tax_tables_serializers import *
from .serializers.auth_serializer import *
from .serializers.user_serializer import CustomUserSerializer
from .services.payroll_processor import *
from .permissions import *
from .serializers.audit_serializer import AuditLogSerializer
from .serializers import employee_serializers
from modules.payroll.repositories.payroll_repository import *

from .view.hr_dashboard_view import HrDashboardView
from . import views
from .view.payroll_view import *
from .view import hr_view, payroll_view
from .view.system_user_view import *
from .view.registeruser import *
from .view.admin_view import *
from .view.department_view import DepartmentViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .view.jobs_view import JobListCreate, JobDetail, JobToggleStatus
from .view.auth_view import CustomTokenObtainPairView