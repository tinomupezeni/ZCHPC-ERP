"""
Django models for the HR module.

These models handle employees, departments, positions, and payroll configuration.
Table names are preserved from the legacy 'human_resources' app.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Department(models.Model):
    """Organizational department."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'human_resources_department'
        ordering = ['name']

    def __str__(self):
        return self.name


class Role(models.Model):
    """User role for permissions."""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'human_resources_role'

    def __str__(self):
        return self.display_name


class Position(models.Model):
    """Job position within a department."""
    title = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'human_resources_position'
        ordering = ['department', 'title']

    def __str__(self):
        return f"{self.title} ({self.department.name})"


class Address(models.Model):
    """Generic address model."""
    label = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    class Meta:
        db_table = 'human_resources_address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.street}, {self.city}"


class Employees(models.Model):
    """Core employee model."""
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'), ('Married', 'Married'),
        ('Divorced', 'Divorced'), ('Widowed', 'Widowed')
    ]
    EMPLOYEE_TYPE_CHOICES = [
        ('Full-time', 'Full-time'), ('Part-time', 'Part-time'),
        ('Contract', 'Contract'), ('Intern', 'Intern')
    ]
    PAY_FREQUENCY_CHOICES = [
        ('Monthly', 'Monthly'), ('Weekly', 'Weekly'), ('Bi-Weekly', 'Bi-Weekly')
    ]

    # User & Organizational Info
    user = models.OneToOneField(
        'identity.CustomUser',  # Reference the CustomUser model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile'  # This creates the reverse relationship
    )
    employee_id = models.CharField(max_length=10, unique=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    employee_type = models.CharField(max_length=50, choices=EMPLOYEE_TYPE_CHOICES, default='Full-time')
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='employees')

    # Personal Info
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, blank=True)

    # Contact Info
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)

    # Contract & Status
    date_joined = models.DateField(default=timezone.localdate)
    contract_from = models.DateField(null=True, blank=True)
    contract_to = models.DateField(null=True, blank=True)
    leave_days_entitled = models.IntegerField(default=22)
    is_active = models.BooleanField(default=True)

    # Salary Info
    usd_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    zig_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    pay_frequency = models.CharField(max_length=50, choices=PAY_FREQUENCY_CHOICES, default='Monthly')

    # Bank & Statutory Info
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    pension_fund = models.CharField(max_length=100, blank=True)
    nssa_number = models.CharField(max_length=50, blank=True)
    zimra_tax_number = models.CharField(max_length=50, blank=True)
    paye_number = models.CharField(max_length=50, blank=True)
    pays_aids_levy = models.BooleanField(default=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'human_resources_employees'
        ordering = ['surname', 'first_name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = Employees.objects.all().order_by("-id").first()
            last_id = 0
            if last_employee and last_employee.employee_id:
                try:
                    last_id = int(last_employee.employee_id.replace("EMP", ""))
                except ValueError:
                    pass
            while True:
                last_id += 1
                new_id = f"EMP{last_id:04d}"
                if not Employees.objects.filter(employee_id=new_id).exists():
                    self.employee_id = new_id
                    break

        if not self.role_id:
            try:
                default_role = Role.objects.get(name="STAFF")
                self.role = default_role
            except Role.DoesNotExist:
                first_role = Role.objects.first()
                if first_role:
                    self.role = first_role
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.surname} ({self.employee_id})"


# Payroll Definition Models
class AllowanceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'human_resources_allowancetype'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.amount})"


class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'human_resources_deductiontype'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.amount})"


class MedicalAidPlan(models.Model):
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    company_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'human_resources_medicalaidplan'

    def __str__(self):
        return f"{self.provider} - {self.plan_name}"


class PensionFund(models.Model):
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    employee_contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    company_contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)

    class Meta:
        db_table = 'human_resources_pensionfund'

    def __str__(self):
        return f"{self.provider} - {self.plan_name}"


class InsuranceOption(models.Model):
    INSURANCE_TYPES = [('funeral', 'Funeral'), ('life', 'Life')]
    provider = models.CharField(max_length=100)
    plan_name = models.CharField(max_length=100)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPES)
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    company_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'human_resources_insuranceoption'

    def __str__(self):
        return f"{self.provider} - {self.plan_name}"


class Union(models.Model):
    name = models.CharField(max_length=100, unique=True)
    dues_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'human_resources_union'

    def __str__(self):
        return self.name


class EmployeeAllowance(models.Model):
    CURRENCY_CHOICES = [('USD', 'US Dollar'), ('ZIG', 'Zimbabwean Gold')]
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='allowances')
    allowance_type = models.ForeignKey(AllowanceType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    class Meta:
        db_table = 'human_resources_employeeallowance'
        unique_together = ('employee', 'allowance_type')

    def __str__(self):
        return f"{self.employee} - {self.allowance_type.name}: {self.currency} {self.amount}"


class EmployeeDeduction(models.Model):
    CURRENCY_CHOICES = [('USD', 'US Dollar'), ('ZIG', 'Zimbabwean Gold')]
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='deductions')
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    class Meta:
        db_table = 'human_resources_employeededuction'
        unique_together = ('employee', 'deduction_type')

    def __str__(self):
        return f"{self.employee} - {self.deduction_type.name}: {self.currency} {self.amount}"


class EmployeePayrollConfig(models.Model):
    CURRENCY_CHOICES = [('USD', 'US Dollar'), ('ZIG', 'Zimbabwean Gold')]
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='payroll_config')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    medical_aid_plan = models.ForeignKey(MedicalAidPlan, on_delete=models.SET_NULL, null=True, blank=True)
    pension_fund_plan = models.ForeignKey(PensionFund, on_delete=models.SET_NULL, null=True, blank=True)
    funeral_cover_plan = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='funeral_covers')
    life_insurance_plan = models.ForeignKey(InsuranceOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='life_insurances')
    union = models.ForeignKey(Union, on_delete=models.SET_NULL, null=True, blank=True)
    school_fees_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    housing_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_benefit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    effective_date = models.DateField(default=timezone.now)

    class Meta:
        db_table = 'human_resources_employeepayrollconfig'
        unique_together = ('employee', 'effective_date')

    def __str__(self):
        return f"Payroll Config for {self.employee}"


# Training Models
class TrainingProgram(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    mandatory = models.BooleanField(default=False)

    class Meta:
        db_table = 'human_resources_trainingprogram'

    def __str__(self):
        return self.title


class TrainingSession(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'), ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'), ('Cancelled', 'Cancelled')
    ]
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.CharField(max_length=200)
    date = models.DateField()
    venue = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')

    class Meta:
        db_table = 'human_resources_trainingsession'

    def __str__(self):
        return f"{self.program.title} - {self.date}"


class TrainingEnrollment(models.Model):
    STATUS_CHOICES = [
        ('Enrolled', 'Enrolled'), ('In Progress', 'In Progress'),
        ('Completed', 'Completed'), ('Dropped', 'Dropped')
    ]
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='training_enrollments')
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Enrolled')

    class Meta:
        db_table = 'human_resources_trainingenrollment'
        unique_together = ('employee', 'session')

    def __str__(self):
        return f"{self.employee} - {self.session.program.title}"


class TrainingCertification(models.Model):
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='certifications')
    program = models.ForeignKey(TrainingProgram, on_delete=models.SET_NULL, null=True, blank=True)
    certification_name = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'human_resources_trainingcertification'

    @property
    def status(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return 'Expired'
        return 'Valid'

    def __str__(self):
        return f"{self.employee} - {self.certification_name}"
