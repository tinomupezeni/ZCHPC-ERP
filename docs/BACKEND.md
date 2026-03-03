# Backend Architecture Documentation

This document provides a comprehensive overview of the Django backend for the ZCHPC ERP system.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Django Apps Overview](#django-apps-overview)
3. [Authentication System](#authentication-system)
4. [Human Resources Module](#human-resources-module)
5. [Payroll Module](#payroll-module)
6. [Accounts Module](#accounts-module)
7. [Employee Portal Module](#employee-portal-module)
8. [Service & Repository Pattern](#service--repository-pattern)
9. [Middleware Chain](#middleware-chain)

---

## Project Structure

```
erp_project/
├── erp_root/                       # Project settings
│   ├── settings.py                 # Django settings
│   ├── urls.py                     # Root URL configuration
│   └── wsgi.py                     # WSGI entry point
│
├── authentication/                 # Authentication & authorization
│   ├── models.py                   # CustomUser, AuditLog
│   ├── views/
│   │   ├── auth_view.py           # Login, token refresh
│   │   ├── user_views.py          # User CRUD
│   │   └── audit_view.py          # Audit logs
│   ├── serializers/
│   ├── middleware.py               # JWT & RBAC middleware
│   ├── permissions.py              # Role-based permissions
│   └── authentication.py           # Email backend
│
├── human_resources/                # HR module
│   ├── hr_models.py               # All HR models
│   ├── views/
│   │   ├── employee_views.py
│   │   ├── recruitment_views.py
│   │   ├── attendance_views.py
│   │   ├── leave_views.py
│   │   ├── training_views.py
│   │   └── report_views.py
│   ├── serializers/
│   ├── services/
│   └── hr_urls.py
│
├── payroll/                        # Payroll module
│   ├── payroll_models.py          # Payroll, TaxBracket, etc.
│   ├── payroll_views.py           # Payroll processing
│   ├── services/
│   │   └── payroll_services.py    # Tax calculations
│   ├── repositories/
│   │   └── payroll_repository.py  # Database operations
│   └── payroll_urls.py
│
├── accounts/                       # Accounting module
│   ├── accounts_models.py         # Chart of accounts, journals
│   ├── accounts_views.py
│   ├── serializers/
│   └── accounts_urls.py
│
├── procurement/                    # Procurement module
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── employee_portal/                # Employee self-service
│   ├── models.py                  # Portal-specific models
│   ├── views/
│   │   ├── auth_views.py          # Portal authentication
│   │   ├── attendance_views.py    # QR clock-in
│   │   ├── leave_views.py
│   │   ├── payslip_views.py
│   │   └── public_views.py        # Public job listings
│   ├── serializers/
│   └── urls.py
│
└── administration/                 # Admin dashboard
    ├── views.py
    └── urls.py
```

---

## Django Apps Overview

| App | Purpose | Key Models |
|-----|---------|------------|
| `authentication` | User auth, RBAC, audit logging | CustomUser, AuditLog |
| `human_resources` | Employee management, recruitment, training | Employees, Job, LeaveRequest |
| `payroll` | Salary processing, tax calculation | Payroll, TaxBracket |
| `accounts` | Financial accounting | AccountChart, AccountMove |
| `procurement` | Purchase management | PurchaseRequest |
| `employee_portal` | Self-service API | ExpenseClaim, SupportTicket |
| `administration` | Admin dashboard | - |

---

## Authentication System

### CustomUser Model

Located at `authentication/models.py`

```python
class CustomUser(AbstractUser):
    id = UUIDField(primary_key=True)      # UUID instead of integer
    email = EmailField(unique=True)        # Email-based login
    failed_attempts = IntegerField()       # Lockout tracking
    lockout_until = DateTimeField()        # Account lockout time
```

**Key Methods:**
- `is_locked_out()` - Check if account is locked
- `register_failed_attempt()` - Track failed logins (locks after 5 attempts for 15 minutes)
- `reset_failed_attempts()` - Clear on successful login

### Authentication Flow

1. **Login Request** → `POST /api/auth/token/`
2. **CustomTokenObtainPairView** validates credentials
3. **EmailBackend** authenticates using email
4. **AuditLog** records the attempt
5. **JWT tokens** returned (access: 24h, refresh: 30d)

### JWT Configuration

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

### Role-Based Access Control (RBAC)

Defined in `authentication/permissions.py`:

| Role | Permissions |
|------|-------------|
| ADMIN / SYSTEM_ADMINISTRATOR | `["*"]` - Full access |
| HR / HUMAN_RESOURCES | `["hr.*", "human_resources.*", "payroll.*", "employees.*"]` |
| ACCOUNTANT | `["payroll.*", "accounts.*"]` |
| PROCUREMENT_OFFICER | `["procurement.*"]` |
| MANAGER | `["hr.*", "payroll.*", "reports.*"]` |
| STAFF | `["authentication.*", "self.*"]` |
| INTERN | `["authentication.*", "self.*"]` |

### AuditLog Model

```python
class AuditLog(models.Model):
    user = ForeignKey(CustomUser, null=True)
    username_attempted = CharField()
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    event_type = CharField()  # SUCCESS, FAILED, LOCKOUT, FORCE_RESET
    timestamp = DateTimeField(auto_now_add=True)
```

**Note:** Audit logs are immutable - cannot be updated or deleted after creation.

---

## Human Resources Module

### Core Models

#### Employees (Primary Model)

```python
class Employees(models.Model):
    # User Link
    user = OneToOneField(CustomUser, null=True)

    # Identification
    employee_id = CharField(unique=True)      # EMP0001, EMP0002...
    national_id = CharField(unique=True)

    # Personal Info
    first_name = CharField()
    surname = CharField()
    date_of_birth = DateField()
    gender = CharField()                       # Male, Female, Other
    marital_status = CharField()               # Single, Married, etc.

    # Contact
    email = EmailField(unique=True)
    phone = CharField()

    # Organizational
    position = ForeignKey(Position)
    department = ForeignKey(Department)
    role = ForeignKey(Role)
    reports_to = ForeignKey('self', null=True)
    employee_type = CharField()                # Full-time, Part-time, Contract

    # Employment
    date_joined = DateField()
    contract_from = DateField()
    contract_to = DateField()
    is_active = BooleanField()
    leave_days_entitled = IntegerField(default=22)

    # Compensation (Multi-Currency)
    usd_salary = DecimalField()
    zig_salary = DecimalField()
    pay_frequency = CharField()                # Monthly, Weekly, Bi-Weekly

    # Bank & Statutory
    bank_name = CharField()
    bank_account = CharField()
    nssa_number = CharField()                  # Social security
    zimra_tax_number = CharField()             # Tax ID
    paye_number = CharField()
    pays_aids_levy = BooleanField(default=True)

    # Emergency Contact
    emergency_contact_name = CharField()
    emergency_contact_number = CharField()
    emergency_contact_relationship = CharField()
```

**Auto-Generated Employee ID:**
```python
def save(self, *args, **kwargs):
    if not self.employee_id:
        # Generates: EMP0001, EMP0002, etc.
        last_emp = Employees.objects.order_by('-employee_id').first()
        # ... sequence logic
```

#### Organizational Models

```python
class Department(models.Model):
    name = CharField(unique=True)
    description = TextField()

class Position(models.Model):
    title = CharField(unique=True)
    department = ForeignKey(Department)
    description = TextField()

class Role(models.Model):
    name = CharField(unique=True)         # ADMIN, HR, ACCOUNTANT, etc.
    display_name = CharField()            # Human-readable name
    permissions = JSONField()             # List of permission strings
```

### Recruitment Models

```python
class Job(models.Model):
    title = CharField()
    department = ForeignKey(Department)
    position = ForeignKey(Position)
    status = CharField()                  # Open, Closed, Draft, Pending
    location = CharField(default="Harare")

    # Multi-Currency Salary
    salary_usd_min = DecimalField()
    salary_usd_max = DecimalField()
    salary_zig_min = DecimalField()
    salary_zig_max = DecimalField()

    # Content (JSONFields for lists)
    description = TextField()
    responsibilities = JSONField()        # List of strings
    qualifications = JSONField()
    competencies = JSONField()

    is_internal = BooleanField()          # Internal vs public posting
    posted_date = DateField()

class Candidate(models.Model):
    id_number = CharField(unique=True)    # National ID
    first_name = CharField()
    last_name = CharField()
    email = EmailField(unique=True)
    resume = FileField(upload_to='resumes/')
    qualifications = TextField()
    experience = TextField()

class JobApplication(models.Model):
    job = ForeignKey(Job)
    candidate = ForeignKey(Candidate)
    cover_letter = TextField()
    applied_on = DateTimeField()
    status = CharField()                  # Pending, Shortlisted, Interview, Offered, Hired, Rejected

    class Meta:
        unique_together = ['job', 'candidate']
```

### Attendance & Leave Models

```python
class AttendanceRecord(models.Model):
    employee = ForeignKey(Employees)
    date = DateField()
    time_in = TimeField()
    time_out = TimeField(null=True)

    class Meta:
        unique_together = ['employee', 'date']

class LeaveType(models.Model):
    name = CharField(unique=True)         # Annual, Sick, Maternity, etc.
    default_days_allowed = IntegerField()

class LeaveBalance(models.Model):
    employee = ForeignKey(Employees)
    leave_type = ForeignKey(LeaveType)
    year = IntegerField()
    days_remaining = DecimalField()

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']

class LeaveRequest(models.Model):
    employee = ForeignKey(Employees)
    leave_type = ForeignKey(LeaveType)
    start_date = DateField()
    end_date = DateField()
    reason = TextField()
    status = CharField()                  # Pending, Approved, Rejected, Cancelled
    reviewed_by = ForeignKey(Employees, null=True)
    review_date = DateTimeField(null=True)

    @property
    def number_of_days(self):
        # Calculated from date range
        return (self.end_date - self.start_date).days + 1
```

### Training Models

```python
class TrainingProgram(models.Model):
    title = CharField()
    category = CharField()
    duration = CharField()
    mandatory = BooleanField()

class TrainingSession(models.Model):
    program = ForeignKey(TrainingProgram)
    trainer = CharField()
    date = DateField()
    venue = CharField()
    status = CharField()                  # Scheduled, Ongoing, Completed, Cancelled

class TrainingEnrollment(models.Model):
    employee = ForeignKey(Employees)
    session = ForeignKey(TrainingSession)
    status = CharField()                  # Enrolled, In Progress, Completed, Dropped

class TrainingCertification(models.Model):
    employee = ForeignKey(Employees)
    program = ForeignKey(TrainingProgram)
    certification_name = CharField()
    issue_date = DateField()
    expiry_date = DateField(null=True)
```

---

## Payroll Module

### Payroll Model

```python
class Payroll(models.Model):
    employee = ForeignKey(Employees)
    period = DateField()                  # First day of pay period month

    # Base Salary (Multi-Currency)
    base_salary_usd = DecimalField()
    base_salary_zig = DecimalField()

    # Net Salary
    net_salary_usd = DecimalField()
    net_salary_zig = DecimalField()

    # Exchange Rate
    exchange_rate = DecimalField(max_digits=12, decimal_places=4)

    # Tax & Statutory
    paye_usd = DecimalField()
    paye_zig = DecimalField()
    aids_levy_usd = DecimalField()
    aids_levy_zig = DecimalField()
    nssa_employee_usd = DecimalField()
    nssa_employee_zig = DecimalField()
    nssa_employer_usd = DecimalField()
    nssa_employer_zig = DecimalField()

    # Totals
    total_allowances_usd = DecimalField()
    total_allowances_zig = DecimalField()
    total_deductions_usd = DecimalField()
    total_deductions_zig = DecimalField()

    status = CharField()                  # Draft, Pending, Processed, Failed, Paid
    notes = TextField()

    class Meta:
        unique_together = ['employee', 'period']
```

### Tax Configuration

```python
class TaxBracket(models.Model):
    currency = CharField()                # USD, ZiG
    min_income = DecimalField()
    max_income = DecimalField(null=True)  # null for highest bracket
    rate = DecimalField()                 # e.g., 0.20 for 20%
    deduction = DecimalField()            # Deductible amount
    active_from = DateField()

    class Meta:
        ordering = ['currency', 'min_income', '-active_from']
```

### PayrollService

Located at `payroll/services/payroll_services.py`:

```python
class PayrollService:
    @staticmethod
    def calculate_tax(salary, brackets):
        """
        Find matching tax bracket and calculate PAYE.
        Formula: (salary * rate) - deduction
        AIDS levy = 3% of PAYE
        """
        for bracket in brackets:
            if bracket.min_income <= salary <= (bracket.max_income or float('inf')):
                paye = (salary * bracket.rate) - bracket.deduction
                aids_levy = paye * Decimal('0.03')
                return paye, aids_levy
        return Decimal('0'), Decimal('0')

    @staticmethod
    def calculate_nssa(salary):
        """
        NSSA contribution: 4.5% employee, 4.5% employer
        """
        rate = Decimal('0.045')
        employee_contribution = salary * rate
        employer_contribution = salary * rate
        return employee_contribution, employer_contribution

    @staticmethod
    def process_payroll_for_period(period):
        """
        Main payroll processing engine.
        1. Fetch all active employees
        2. Get tax brackets and exchange rates
        3. Calculate all components for each employee
        4. Create Payroll records
        """
        # Implementation details...
```

### Exchange Rates

```python
class DailyZiGRateToUSD(models.Model):
    date = DateField(unique=True)
    average = DecimalField(max_digits=16, decimal_places=8)
```

---

## Accounts Module

### Chart of Accounts

```python
class AccountChart(models.Model):
    code = CharField(unique=True)         # Account code
    name = CharField()
    parent = ForeignKey('self', null=True)  # Hierarchical structure
    account_type = CharField()            # view, regular, consolidation
    reconcile = BooleanField()
    currency = ForeignKey(Currency)

class Journal(models.Model):
    name = CharField()
    code = CharField(unique=True)
    journal_type = CharField()            # sale, purchase, cash, bank, general
    default_debit_account = ForeignKey(AccountChart)
    default_credit_account = ForeignKey(AccountChart)
    currency = ForeignKey(Currency)

class AccountMove(models.Model):
    """Journal Entry Header"""
    journal = ForeignKey(Journal)
    date = DateField()
    ref = CharField()
    narration = TextField()
    posted = BooleanField()

class AccountMoveLine(models.Model):
    """Journal Entry Detail Line"""
    move = ForeignKey(AccountMove)
    account = ForeignKey(AccountChart)
    partner = ForeignKey(Partner, null=True)
    debit = DecimalField()
    credit = DecimalField()
    currency = ForeignKey(Currency)
    amount_currency = DecimalField()
    analytic_account = ForeignKey(AnalyticAccount, null=True)
    date = DateField()
```

### Supporting Models

```python
class Currency(models.Model):
    name = CharField()
    code = CharField()
    symbol = CharField()
    rate_to_base = DecimalField()

class Partner(models.Model):
    """Customer, Supplier, or Employee"""
    name = CharField()
    partner_type = CharField()            # customer, supplier, employee
    vat_number = CharField(null=True)
    currency = ForeignKey(Currency)

class AnalyticAccount(models.Model):
    """Cost Centers / Projects"""
    name = CharField()
    code = CharField()
    parent = ForeignKey('self', null=True)
```

---

## Employee Portal Module

### Portal-Specific Models

```python
class AttendanceQRToken(models.Model):
    """Dynamic QR tokens for attendance (rotates every 30 seconds)"""
    token = CharField(unique=True, max_length=64)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    is_active = BooleanField(default=True)
    used_count = PositiveIntegerField(default=0)

    @classmethod
    def generate_token(cls):
        """Generate cryptographically secure 32-char token"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

    @classmethod
    def get_or_create_current_token(cls, validity_seconds=30):
        """Get valid token or create new one"""
        # Deactivates old tokens, creates new one

    @classmethod
    def verify_token(cls, token_string):
        """Verify token is valid and not expired"""

class ExpenseClaim(models.Model):
    employee = ForeignKey(Employees)
    category = ForeignKey(ExpenseCategory)
    title = CharField()
    amount = DecimalField()
    currency = CharField()                # USD, ZiG
    date_incurred = DateField()
    receipt = FileField()
    status = CharField()                  # Draft, Submitted, Under Review, Approved, Rejected, Paid

class SupportTicket(models.Model):
    employee = ForeignKey(Employees)
    ticket_number = CharField(unique=True)  # Auto-generated: TKT-YYYYMMDD-XXXX
    category = CharField()                # IT, HR, Facilities, Finance, Other
    priority = CharField()                # Low, Medium, High, Urgent
    subject = CharField()
    description = TextField()
    status = CharField()                  # Open, In Progress, Waiting, Resolved, Closed
    assigned_to = ForeignKey(Employees, null=True)

class Notification(models.Model):
    employee = ForeignKey(Employees)
    notification_type = CharField()       # leave_approved, expense_approved, etc.
    title = CharField()
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField()

class Document(models.Model):
    category = ForeignKey(DocumentCategory)
    title = CharField()
    file = FileField()
    visibility = CharField()              # all, department, specific
    departments = ManyToManyField(Department)
    allowed_employees = ManyToManyField(Employees)
    version = CharField()
    requires_acknowledgement = BooleanField()
```

---

## Service & Repository Pattern

The codebase follows a service/repository pattern for complex business logic:

### Repository Layer

Handles database operations:

```python
# payroll/repositories/payroll_repository.py
class PayrollRepository:
    @staticmethod
    def get_by_employee_and_period(employee, period):
        return Payroll.objects.filter(employee=employee, period=period).first()

    @staticmethod
    def create_payroll(**kwargs):
        return Payroll.objects.create(**kwargs)

    @staticmethod
    def list_employees():
        return Employees.objects.filter(is_active=True)

class ExchangeRateRepository:
    @staticmethod
    def get_latest(date):
        return DailyZiGRateToUSD.objects.filter(date__lte=date).order_by('-date').first()

class TaxRepository:
    @staticmethod
    def get_brackets(currency, period):
        return TaxBracket.objects.filter(
            currency=currency,
            active_from__lte=period
        ).order_by('min_income')
```

### Service Layer

Handles business logic:

```python
# payroll/services/payroll_services.py
class PayrollService:
    @staticmethod
    def calculate_tax(salary, brackets):
        # Tax calculation logic

    @staticmethod
    def calculate_nssa(salary):
        # NSSA calculation logic

    @staticmethod
    def process_payroll_for_period(period):
        # Main processing orchestration
```

---

## Middleware Chain

Order of middleware execution (`erp_root/settings.py`):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',           # CORS handling
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.JWTAuthenticationMiddleware',  # JWT extraction
    'authentication.middleware.RBACMiddleware',               # Permission checking
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### JWTAuthenticationMiddleware

```python
class JWTAuthenticationMiddleware:
    def __call__(self, request):
        # Extract JWT from Authorization header
        # Validate token
        # Set request.user
        return self.get_response(request)
```

### RBACMiddleware

```python
class RBACMiddleware:
    EXEMPT_PATHS = ['/api/auth/', '/api/portal/auth/', '/admin/']

    def __call__(self, request):
        # Check if path is exempt
        # Get user's role permissions
        # Convert URL to permission string
        # Check permission against user's role
        # Return 403 if not authorized
        return self.get_response(request)
```

---

## Key Configuration

### Database

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'erp_db',
        'USER': 'erp_user',
        'PASSWORD': '...',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Authentication

```python
AUTH_USER_MODEL = 'authentication.CustomUser'

AUTHENTICATION_BACKENDS = [
    'authentication.authentication.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### File Uploads

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Upload directories:
# - resumes/
# - expense_receipts/
# - ticket_attachments/
# - portal_documents/
```

---

## Adding New Features

### Creating a New Model

1. Add model class to appropriate `*_models.py` file
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`
4. Create serializer in `serializers/` directory
5. Create view in `views/` directory
6. Add URL in `*_urls.py` file

### Creating a New API Endpoint

1. Define the view class/function
2. Add URL pattern
3. Update permissions if needed
4. Test with Postman or frontend
5. Document the endpoint

### Creating a New Django App

```bash
python manage.py startapp new_app
```

Then:
1. Add to `INSTALLED_APPS` in settings.py
2. Create models, views, serializers
3. Include URLs in main `urls.py`
4. Update RBAC permissions if needed
