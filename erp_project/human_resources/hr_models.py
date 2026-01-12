# hr/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


# ---------------------------------
# 1. CORE ORGANIZATIONAL MODELS
# ---------------------------------

class Department(models.Model):
    """
    Defines an organizational department (e.g., HR, Engineering, Sales).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., "ADMIN", "HR"
    display_name = models.CharField(max_length=100) # e.g., "System Administrator"
    description = models.TextField(blank=True)
    
    permissions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.display_name

class Position(models.Model):
    """
    Defines a specific job title or position within a department.
    (e.g., Software Engineer, HR Manager)
    """
    title = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['department', 'title']
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class Address(models.Model):
    """
    Generic address model. Can be linked to an Employees, Department, etc.
    if needed, though here it is standalone as you had it.
    """
    label = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'Headquarters', 'Warehouse'")
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, verbose_name="State/Province")
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        
    def __str__(self):
        if self.label:
            return f"{self.label} ({self.street}, {self.city})"
        return f"{self.street}, {self.city}"

# ---------------------------------
# 2. CORE EMPLOYEE MODEL
# ---------------------------------

class Employees(models.Model):
    """
    The central model for an employee, containing all personal
    and organizational information.
    """
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]
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
    EMPLOYEE_TYPE_CHOICES = [
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Intern', 'Intern'),
    ]
    PAY_FREQUENCY_CHOICES = [
        ('Monthly', 'Monthly'),
        ('Weekly', 'Weekly'),
        ('Bi-Weekly', 'Bi-Weekly'),
    ]

    # --- User & Organizational Info ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='employee_profile'
    )
    employee_id = models.CharField(max_length=10, unique=True, blank=True, help_text="Auto-generated (e.g., EMP0001)")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee_type = models.CharField(max_length=50, choices=EMPLOYEE_TYPE_CHOICES, default='Full-time')
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')

    # --- Personal Info ---
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="National ID")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, blank=True)
    
    # --- Contact Info ---
    email = models.EmailField(unique=True, help_text="Work or personal email")
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="STAFF")

    # --- Contract & Status ---
    date_joined = models.DateField(default=timezone.localdate)
    contract_from = models.DateField(null=True, blank=True)
    contract_to = models.DateField(null=True, blank=True)
    leave_days_entitled = models.IntegerField(default=22, verbose_name="Annual Leave Days Entitled")
    is_active = models.BooleanField(default=True)

    # --- Basic Salary Info ---
    usd_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    zig_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    pay_frequency = models.CharField(max_length=50, choices=PAY_FREQUENCY_CHOICES, default='Monthly')

    # --- Bank & Statutory Info ---
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    pension_fund = models.CharField(max_length=100, blank=True)
    nssa_number = models.CharField(max_length=50, blank=True, verbose_name="NSSA Number")
    zimra_tax_number = models.CharField(max_length=50, blank=True, verbose_name="ZIMRA Tax Number")
    paye_number = models.CharField(max_length=50, blank=True, verbose_name="PAYE Number")
    pays_aids_levy = models.BooleanField(default=True, verbose_name="Pays AIDS Levy")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='employees')
    # --- Emergency Contact ---
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['surname', 'first_name']
        verbose_name = "Employees"
        verbose_name_plural = "Employees"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employees.objects.all().order_by("-id").first()
            last_id = 0
            if last_employee and last_employee.employee_id:
                try:
                    last_id = int(last_employee.employee_id.replace("EMP", ""))
                except ValueError:
                    pass  # Handle cases where ID is not in the expected format
            
            while True:
                last_id += 1
                new_id = f"EMP{last_id:04d}"
                if not Employees.objects.filter(employee_id=new_id).exists():
                    self.employee_id = new_id
                    break
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.surname} ({self.employee_id})"


# ---------------------------------
# 3. PAYROLL DEFINITION MODELS
# ---------------------------------

class AllowanceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class MedicalAidPlan(models.Model):
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    company_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.provider} - {self.plan_name}"

class PensionFund(models.Model):
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    employee_contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Percentage (e.g., 5.0 for 5%)")
    company_contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0, help_text="Percentage (e.g., 5.0 for 5%)")

    def __str__(self):
        return f"{self.provider} - {self.plan_name}"

class InsuranceOption(models.Model):
    INSURANCE_TYPES = [('funeral', 'Funeral'), ('life', 'Life')]
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPES)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    company_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.provider} - {self.plan_name} ({self.get_insurance_type_display()})"

class Union(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dues_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return self.name

# ---------------------------------
# 4. EMPLOYEE-SPECIFIC PAYROLL
# ---------------------------------

class EmployeeAllowance(models.Model):
    """
    Links a specific employee to an allowance type with a specific amount.
    """
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='allowances')
    allowance_type = models.ForeignKey(AllowanceType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('employee', 'allowance_type')
    def __str__(self):
        return f"{self.employee} - {self.allowance_type.name}: ${self.amount}"

class EmployeeDeduction(models.Model):
    """
    Links a specific employee to a deduction type with a specific amount.
    """
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='deductions')
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('employee', 'deduction_type')
    def __str__(self):
        return f"{self.employee} - {self.deduction_type.name}: ${self.amount}"

class EmployeePayrollConfig(models.Model):
    """
    Stores employee-specific choices for payroll deductions and benefits.
    Replaces your 'EmployeeDeductables' model.
    """
    CURRENCY_CHOICES = [('USD', 'US Dollar'), ('ZIG', 'Zimbabwean Gold')]
    
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name="payroll_config")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    
    # Linked Plans
    medical_aid_plan = models.ForeignKey(MedicalAidPlan, on_delete=models.SET_NULL, null=True, blank=True)
    pension_fund_plan = models.ForeignKey(PensionFund, on_delete=models.SET_NULL, null=True, blank=True)
    funeral_cover_plan = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='funeral_covers', limit_choices_to={'insurance_type': 'funeral'})
    life_insurance_plan = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='life_insurances', limit_choices_to={'insurance_type': 'life'})
    union = models.ForeignKey(Union, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Taxable Benefits (amounts per pay period)
    school_fees_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    housing_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    effective_date = models.DateField(default=timezone.now)
    
    class Meta:
        verbose_name = "Employees Payroll Config"
        verbose_name_plural = "Employees Payroll Configs"
        unique_together = ('employee', 'effective_date')
    
    def __str__(self):
        return f"Payroll Config for {self.employee} ({self.currency})"

# ---------------------------------
# 5. RECRUITMENT MODELS
# ---------------------------------
class Job(models.Model):
    """
    A job posting for recruitment.
    """
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
    ]

    # Derived from Position usually, but editable
    title = models.CharField(max_length=200)
    
    # Link to Department
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Job Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    location = models.CharField(max_length=100, default="Harare")
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    
    # Rich Text / Lists (Using JSONField to store arrays ["Item 1", "Item 2"])
    description = models.TextField(blank=True, help_text="General summary")
    responsibilities = models.JSONField(default=list, blank=True)
    qualifications = models.JSONField(default=list, blank=True)
    
    # Application Info
    application_process = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(default="hroffice@zchpc.ac.zw")
    notes = models.TextField(blank=True, null=True)
    
    posted_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"
    
    @property
    def applicants_count(self):
        return self.applications.count()
    
    
class Candidate(models.Model):
    """
    A person who has applied or is being considered for a job.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class JobApplication(models.Model):
    """
    Links a Candidate to a Job posting.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview', 'Interview'),
        ('Offered', 'Offered'),
        ('Hired', 'Hired'),
        ('Rejected', 'Rejected'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    applied_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['-applied_on']
    
    def __str__(self):
        return f"{self.candidate} for {self.job.title}"

# ---------------------------------
# 6. TRAINING & DEVELOPMENT
# ---------------------------------

class TrainingProgram(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., '3 Days', '2 Hours'")
    mandatory = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.CharField(max_length=200)
    date = models.DateField()
    venue = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    
    def __str__(self):
        return f"{self.program.title} - {self.date}"

class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ('Enrolled', 'Enrolled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Dropped', 'Dropped'),
    ]
    
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='training_enrollments')
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Enrolled')
    
    class Meta:
        unique_together = ('employee', 'session')
    
    def __str__(self):
        return f"{self.employee} - {self.session.program.title}"

class TrainingCertification(models.Model):
    STATUS_CHOICES = [('Valid', 'Valid'), ('Expired', 'Expired'), ('Pending', 'Pending')]
    
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='certifications')
    program = models.ForeignKey(TrainingProgram, on_delete=models.SET_NULL, null=True, blank=True)
    certification_name = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    @property
    def status(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return 'Expired'
        return 'Valid'
    
    def __str__(self):
        return f"{self.employee} - {self.certification_name}"

# ---------------------------------
# 7. ATTENDANCE & LEAVE
# ---------------------------------

class AttendanceRecord(models.Model):
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee__first_name']
    
    def __str__(self):
        return f"{self.employee} - {self.date}"

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    default_days_allowed = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    """
    Tracks the remaining leave days for each employee and leave type.
    This should be populated annually by a script or signal.
    """
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField(default=timezone.now().year)
    days_remaining = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
    
    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.year}): {self.days_remaining} days"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    requested_on = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(Employees, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    review_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_on']
    
    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    @property
    def number_of_days(self):
        # Basic calculation, can be refined to exclude weekends/holidays
        return (self.end_date - self.start_date).days + 1