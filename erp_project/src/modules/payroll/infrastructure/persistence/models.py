"""
Django models for the Payroll module.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Payroll(models.Model):
    """Employee payroll record."""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Processed', 'Processed'),
        ('Failed', 'Failed'),
        ('Paid', 'Paid'),
    ]

    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.PROTECT,
        related_name='payrolls'
    )
    period = models.DateField()
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
    updated_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    paye_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paye_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aids_levy_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aids_levy_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssa_employee_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssa_employer_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssa_employee_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssa_employer_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions_zig = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'payroll_payroll'
        unique_together = ['employee', 'period']
        ordering = ['-period', 'employee__first_name']

    def __str__(self):
        return f"{self.employee} - {self.period.strftime('%B %Y')} - {self.get_status_display()}"

    @property
    def gross_usd(self):
        return (self.base_salary_usd or 0) + (self.total_allowances_usd or 0)

    @property
    def gross_zig(self):
        return (self.base_salary_zig or 0) + (self.total_allowances_zig or 0)

    def save(self, *args, **kwargs):
        if not self.period:
            self.period = timezone.now().replace(day=1)
        super().save(*args, **kwargs)


class DailyZiGRateToUSD(models.Model):
    """Daily exchange rate from ZiG to USD."""
    date = models.DateField(unique=True)
    average = models.DecimalField(max_digits=20, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_dailyzigrateto_usd'
        verbose_name = "Daily ZiG to USD Rate"
        verbose_name_plural = "Daily ZiG to USD Rates"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - Avg {self.average}"


class TaxBracket(models.Model):
    """Tax bracket for PAYE calculation."""
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('ZiG', 'ZiG'),
    ]

    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    min_income = models.DecimalField(max_digits=10, decimal_places=2)
    max_income = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank for highest bracket"
    )
    rate = models.DecimalField(max_digits=5, decimal_places=3)
    deduction = models.DecimalField(max_digits=10, decimal_places=2)
    active_from = models.DateField(default=timezone.now)
    provider = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'payroll_taxbracket'
        verbose_name = "Tax Bracket"
        verbose_name_plural = "Tax Brackets"
        ordering = ['currency', 'min_income', '-active_from']

    def __str__(self):
        return f"{self.currency} {self.min_income}-{self.max_income or 'Max'} @ {self.rate*100}%"


class PayrollPeriod(models.Model):
    """Payroll period configuration."""
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Processing', 'Processing'),
        ('Closed', 'Closed'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="e.g., Monthly, Bi-Weekly, Weekly"
    )
    frequency_in_days = models.IntegerField(
        help_text="Number of days in the period"
    )
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=20, default='Open', choices=STATUS_CHOICES)

    class Meta:
        db_table = 'payroll_payrollperiod'
        verbose_name = "Payroll Period Type"
        verbose_name_plural = "Payroll Period Types"
        ordering = ['name']

    def __str__(self):
        return self.name

# Phase 1: New Normalized Models for Payroll
class PayrollProfile(models.Model):
    employee = models.OneToOneField('hr.Employees', on_delete=models.CASCADE, related_name='payroll_profile')
    usd_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    zig_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pay_frequency = models.CharField(max_length=20, default='monthly')

    class Meta:
        db_table = 'payroll_payrollprofile'

class EmployeeBankAccount(models.Model):
    employee = models.ForeignKey('hr.Employees', on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    branch_code = models.CharField(max_length=50, null=True, blank=True)
    account_number = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, default='USD')
    is_primary = models.BooleanField(default=True)

    class Meta:
        db_table = 'payroll_employeebankaccount'

class StatutoryProfile(models.Model):
    employee = models.OneToOneField('hr.Employees', on_delete=models.CASCADE, related_name='statutory_profile')
    nssa_number = models.CharField(max_length=50, null=True, blank=True)
    zimra_tax_number = models.CharField(max_length=50, null=True, blank=True)
    paye_number = models.CharField(max_length=50, null=True, blank=True)
    pays_aids_levy = models.BooleanField(default=True)
    pension_fund = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'payroll_statutoryprofile'


class PayrollBatch(models.Model):
    """
    A payroll "run" for a period - tracks processing status and summary
    totals across all payslips generated for that period. Distinct from
    `Payroll` above, which (despite the name) is the per-employee payslip
    table; nothing previously backed the domain Payroll aggregate.
    """
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Processing', 'Processing'),
        ('Closed', 'Closed'),
    ]

    period = models.DateField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.UUIDField(null=True, blank=True)  # CustomUser.id is a UUID, not an int
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    total_employees = models.IntegerField(default=0)
    total_gross_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_gross_zig = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net_zig = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_paye_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_paye_zig = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_nssa_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_nssa_zig = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        # NOT payroll_payrollbatch - that name was already taken on the
        # production DB by an unrelated, undocumented table (no model or
        # migration for it anywhere in this repo) with a completely
        # different schema, linked via a dead payroll_payroll.batch_id FK
        # that no current code reads. Renamed to avoid colliding with it.
        db_table = 'payroll_processing_batch'
        ordering = ['-period']

    def __str__(self):
        return f"Payroll batch {self.period.strftime('%B %Y')} - {self.status}"
