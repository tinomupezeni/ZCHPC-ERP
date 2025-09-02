from datetime import timedelta
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
# In your models.py
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from jsonschema import ValidationError
from datetime import date 

# *******************
# Departments
# *******************
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    department_head = models.ForeignKey(
        'CustomUser',   # must reference CustomUser, not 'Employees'
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['name']

    def __str__(self):
        return self.name
    
# ******************************
# Custom User Model with RBAC
# ******************************
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("HR", "HR"),
        ("ACCOUNTANT", "Accountant"),
        ("PROCUREMENT", "Procurement"),
        ("SALES", "Sales"),
        ("MANAGER", "Manager"),
        ("STAFF", "Staff"),
        ("INTERN", "Intern"),
    ]

    id = models.CharField(default=uuid.uuid4().hex, primary_key=True, editable=False, max_length=32)
    employeeid = models.CharField(max_length=10, unique=True, blank=True)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)

    email = models.EmailField(unique=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contractFrom = models.DateField(null=True, blank=True)
    contractTo = models.DateField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'firstname', 'surname', 'role']
    
    # 🔒 Security fields
    failed_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    # must_change_password = models.BooleanField(default=True)  # ✅ forces reset on first login

    def is_locked_out(self):
        """Check if user is currently locked out."""
        if self.lockout_until and self.lockout_until > timezone.now():
            return True
        return False

    def register_failed_attempt(self, max_attempts=5, lockout_minutes=15):
        """Increase failed login attempts and lock user if needed."""
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.lockout_until = timezone.now() + timedelta(minutes=lockout_minutes)
            self.failed_attempts = 0  # reset counter after lock
        self.save(update_fields=["failed_attempts", "lockout_until"])

    def reset_failed_attempts(self):
        """Clear failed attempts after successful login."""
        self.failed_attempts = 0
        self.lockout_until = None
        self.save(update_fields=["failed_attempts", "lockout_until"])

    def clean(self):
        # Interns → No salary
        if self.role == "INTERN" and self.salary:
            raise ValidationError("Interns cannot have a salary assigned.")

        # Only Admins can belong to the "System" department
        if self.department and self.department.name == "System" and self.role != "ADMIN":
            raise ValidationError("Only Admins can belong to the System department.")

        # Managers must have contracts
        if self.role == "MANAGER" and (not self.contractFrom or not self.contractTo):
            raise ValidationError("Managers must have contract dates defined.")

        # Accountants must have salaries
        # if self.role == "ACCOUNTANT" :
        #     raise ValidationError("Accountants must have a salary defined.")

    def save(self, *args, **kwargs):
        self.full_clean()  # ✅ enforce RBAC rules

        if not self.employeeid:
            last_employee = CustomUser.objects.exclude(employeeid="").order_by("-employeeid").first()
            if last_employee and last_employee.employeeid.startswith("SYS"):
                last_id = int(last_employee.employeeid.replace("SYS", ""))
                new_id = f"SYS{last_id + 1:04d}"
            else:
                new_id = "SYS0001"
            self.employeeid = new_id

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employeeid} - {self.email}"

# *******************************
# Audit log for login attempts
# *******************************
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
    timestamp = models.DateTimeField(default=timezone.now, editable=False)

    def save(self, *args, **kwargs):
        if self.pk:  # prevent updates
            raise Exception("Audit logs are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("Audit logs cannot be deleted.")

    class Meta:
        verbose_name = "Login Audit Log"
        verbose_name_plural = "Login Audit Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.username_attempted} - {self.event_type} at {self.timestamp}"



class AllowanceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Allowance Type"
        verbose_name_plural = "Allowance Types"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.amount})"

class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    class Meta:
        verbose_name = "Deduction Type"
        verbose_name_plural = "Deduction Types"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.amount})"



class Employees(models.Model):
    employeeid = models.CharField(max_length=10, unique=True, blank=True)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    nationalid = models.CharField(max_length=50, unique=True, null=True)
    dateOfBirth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True)
    maritalStatus = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    position = models.CharField(max_length=50)
    department = models.CharField(max_length=50, default='System')
    employee_type = models.CharField(max_length=50, default='Unspecified')
    leave_days = models.IntegerField(default=0)
    contractFrom = models.DateField(null=True, blank=True)
    contractTo = models.DateField(null=True, blank=True)
    usd_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    zig_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Add blank=True to optional fields
    bankName = models.CharField(max_length=100, blank=True, null=True)
    bankAccount = models.CharField(max_length=50, blank=True, null=True)
    frequency = models.CharField(max_length=50, default='monthly')
    bankName = models.CharField(max_length=100, blank=True)
    bankAccount = models.CharField(max_length=50, blank=True)
    pensionFund = models.CharField(max_length=100, blank=True)
    nssaNumber = models.CharField(max_length=50, blank=True)
    zimraTaxNumber = models.CharField(max_length=50, blank=True)
    payeNumber = models.CharField(max_length=50, blank=True)
    aidsLevyNumber = models.BooleanField(default=True)
    isActive = models.BooleanField(default=True)
    emegencyContactName = models.CharField(max_length=100, blank=True)
    emegencyContactNumber = models.CharField(max_length=15, blank=True)
    emegencyContactRelationship = models.CharField(max_length=50, blank=True)

    allowances = models.ManyToManyField(AllowanceType, blank=True, related_name='employees_with_allowance')
    deductions = models.ManyToManyField(DeductionType, blank=True, related_name='employees_with_deduction')


    def save(self, *args, **kwargs):
        if not self.employeeid:
            last_employee = Employees.objects.order_by("-id").first()
            if last_employee and last_employee.employeeid:
                last_id = int(last_employee.employeeid.replace("EMP", ""))
            else:
                last_id = 0  # Start from EMP0001 if no employees exist
            
            # Keep trying new IDs until we find an available one
            while True:
                last_id += 1
                new_id = f"EMP{last_id:04d}"
                if not Employees.objects.filter(employeeid=new_id).exists():
                    self.employeeid = new_id
                    break

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employeeid} - {self.email}"

# *******************************
# Store daily ZiG to USD exchange rates
# *******************************
    
class DailyZiGRateToUSD(models.Model):
    date = models.DateField(unique=True) 
    average = models.DecimalField(max_digits=20, decimal_places=8)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Daily ZiG to USD Rate" 
        verbose_name_plural = "Daily ZiG to USD Rates"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - Avg {self.average}"
    

class TaxBracket(models.Model):
    currency_choices = [
        ('USD', 'USD'),
        ('ZiG', 'ZiG') # Use ZWG for consistency with your code
    ]
    currency = models.CharField(max_length=10, choices=currency_choices)
    min_income = models.DecimalField(max_digits=10, decimal_places=2)
    max_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leave blank for highest bracket")
    rate = models.DecimalField(max_digits=5, decimal_places=3) # e.g., 0.20 for 20%
    deduction = models.DecimalField(max_digits=10, decimal_places=2) # Deductible amount for that bracket
    active_from = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = "Tax Bracket"
        verbose_name_plural = "Tax Brackets"
        # Ensure correct ordering for tax calculation
        ordering = ['currency', 'min_income', '-active_from']

    def __str__(self):
        return f"{self.currency} {self.min_income}-{self.max_income or 'Max'} @ {self.rate*100}%"

    
class Payroll(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Processed', 'Processed'),
        ('Failed', 'Failed'),
        ('Paid', 'Paid'),
    ]
    
    employee = models.ForeignKey(
        Employees,
        on_delete=models.PROTECT,  # Prevent deletion if payroll exists
        related_name='payrolls'
    )
 

    period = models.DateField()  # First day of the pay period month
    base_salary_usd = models.DecimalField(
        max_digits=10,
        default=0,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    net_salary_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    base_salary_zig = models.DecimalField(
        max_digits=10,
        decimal_places=2,
         default=0,
        validators=[MinValueValidator(0)]
    )
    net_salary_zig = models.DecimalField(
        max_digits=10,
        decimal_places=2,
         default=0,
        validators=[MinValueValidator(0)]
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
         default=0,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now,)
    notes = models.TextField(blank=True)
    nssa_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pension_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nssa_zig = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pension_zig = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    
    class Meta:
        unique_together = ['employee', 'period']  # One payroll per employee per period
        ordering = ['-period', 'employee__firstname']
    
    def __str__(self):
        return f"{self.employee} - {self.period.strftime('%B %Y')} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Automatically set period to first day of month if not specified
        if not self.period:
            self.period = timezone.now().replace(day=1)
        super().save(*args, **kwargs)
        
        


class PAYEThreshold(models.Model):
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, choices=[('USD', 'US Dollar'), ('ZWL', 'Zimbabwe Dollar')])
    threshold_from = models.DecimalField(max_digits=12, decimal_places=2)
    threshold_to = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=4)
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = "PAYE Threshold"
        verbose_name_plural = "PAYE Thresholds"


class PAYETaxCredit(models.Model):
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    zwl_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = "PAYE Tax Credit"
        verbose_name_plural = "PAYE Tax Credits"


class NSSACap(models.Model):
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    usd_cap = models.DecimalField(max_digits=10, decimal_places=2)
    zwl_cap = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=4)
    active_from = models.DateField(default=date.today)
    contribution_type = models.CharField(max_length=30, choices=[('employee', 'Employee Only'),
                                                              ('employer', 'Employer Only'),
                                                              ('employee_and_employer', 'Employee and Employer')])
    
    class Meta:
        verbose_name = "NSSA Cap"
        verbose_name_plural = "NSSA Caps"


class MedicalAidProvider(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Medical Aid Provider"
        verbose_name_plural = "Medical Aid Providers"


class MedicalAidPlan(models.Model):
    provider = models.ForeignKey(MedicalAidProvider, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    zwl_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = "Medical Aid Plan"
        verbose_name_plural = "Medical Aid Plans"


class PensionFund(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    employee_rate = models.DecimalField(max_digits=5, decimal_places=4)
    employer_rate = models.DecimalField(max_digits=5, decimal_places=4)
    currency = models.CharField(max_length=10, choices=[('usd', 'USD Only'), ('zwl', 'ZWL Only'), ('both', 'Both')])
    
    class Meta:
        verbose_name = "Pension Fund"
        verbose_name_plural = "Pension Funds"


class InsuranceOption(models.Model):
    INSURANCE_TYPES = [
        ('funeral', 'Funeral Cover'),
        ('life', 'Life Insurance'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPES)
    calculation_type = models.CharField(max_length=30, null=True, blank=True,
                                      choices=[('fixed', 'Fixed Amount'),
                                               ('percentage', 'Percentage of Salary')])
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    zwl_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    min_amount_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_amount_zwl = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_amount_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_amount_zwl = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cover_details = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        verbose_name = "Insurance Option"
        verbose_name_plural = "Insurance Options"


class Union(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    zwl_amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('annual', 'Annual')])
    
    class Meta:
        verbose_name = "Union"
        verbose_name_plural = "Unions"


# Employee-specific deductions
class EmployeeDeductables(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('ZWL', 'Zimbabwe Dollar'),
    ]
    
    employee = models.ForeignKey('Employees', on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    
    # Medical Aid
    medical_aid = models.ForeignKey(MedicalAidPlan, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pension
    pension_fund = models.ForeignKey(PensionFund, on_delete=models.SET_NULL, null=True, blank=True)
    pension_employee_contribution = models.BooleanField(default=True)
    
    # Insurance
    funeral_cover = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='funeral_cover', limit_choices_to={'insurance_type': 'funeral'})
    life_insurance = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='life_insurance', limit_choices_to={'insurance_type': 'life'})
    
    # Union
    union = models.ForeignKey(Union, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Benefits (for withholding tax)
    school_fees_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    housing_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Other fields
    active = models.BooleanField(default=True)
    effective_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employee Deductable"
        verbose_name_plural = "Employee Deductables"
        unique_together = ('employee', 'effective_date')
    
    def __str__(self):
        return f"Deductions for {self.employee} ({self.currency})"

class PayrollPeriod(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Monthly, Bi-Weekly, Weekly")
    frequency_in_days = models.IntegerField(help_text="Number of days in the period (approximate for monthly, exact for others)")
    # For a monthly period, this could be 30, for weekly 7, bi-weekly 14, semi-monthly 15
    # Actual start/end dates will be set per instance of a specific period.

    # Example: 'Monthly'
    # 'Bi-Weekly'
    # 'Weekly'
    # 'Semi-Monthly'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Payroll Period Type"
        verbose_name_plural = "Payroll Period Types"
        ordering = ['name']
        
class TrainingProgram(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    mandatory = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title


class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]
    
    program = models.CharField(max_length=200)
    trainer = models.CharField(max_length=200)
    date = models.DateField()
    venue = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.program} - {self.date}"
    
    
class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ('Enrolled', 'Enrolled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    
    employee = models.CharField(max_length=200)
    program = models.CharField(max_length=200)
    session_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Enrolled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee} - {self.program}"
    
    class Meta:
        ordering = ['-created_at']
    
class TrainingCertification(models.Model):
    STATUS_CHOICES = [
        ('Valid', 'Valid'),
        ('Expired', 'Expired'),
        ('Pending', 'Pending'),
    ]
    
    employee = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Valid')
    
    def __str__(self):
        return f"{self.employee} - {self.program}"
    

class Job(models.Model):
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=100, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    posted_on = models.DateTimeField(auto_now_add=True)
    applicants_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title


class AttendanceRecord(models.Model):
    employee = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    job_number = models.CharField(max_length=50, blank=True)  # If you need a job number field
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee__first_name']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}"

