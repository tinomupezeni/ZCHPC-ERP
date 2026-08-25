import uuid
from django.db import models
from django.conf import settings # For AUTH_USER_MODEL

class Address(models.Model):
    # TODO: Add fields for Address model
    pass

class AllowanceType(models.Model):
    name = models.CharField(max_length=100, unique=True, default='')
    description = models.TextField(blank=True, default='')
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_allowancetype'

    def __str__(self):
        return self.name

class DeductionType(models.Model):
    name = models.CharField(max_length=100, unique=True, default='')
    description = models.TextField(blank=True, default='')
    is_percentage = models.BooleanField(default=False)  # If true, amount is percentage
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hr_deductiontype'

    def __str__(self):
        return self.name

class Department(models.Model):
    # TODO: Add fields for Department model
    name = models.CharField(max_length=100, unique=True, default='IT')
    description = models.TextField(blank=True, default='')
    pass

class EmployeeAllowance(models.Model):
    # TODO: Add fields for EmployeeAllowance model
    pass

class EmployeeDeduction(models.Model):
    # TODO: Add fields for EmployeeDeduction model
    pass

class EmployeePayrollConfig(models.Model):
    # TODO: Add fields for EmployeePayrollConfig model
    pass

class Employees(models.Model):
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # Employee Code (EC Number) - human readable, auto-increments: EMP0001, EMP0002, etc.
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    first_name = models.CharField(max_length=100, default='John')
    surname = models.CharField(max_length=100, default='Doe')

    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Auto-generate employee_id in format EMP0001
            last_employee = Employees.objects.order_by('-id').first()
            if last_employee and last_employee.employee_id and last_employee.employee_id.startswith('EMP'):
                try:
                    last_num = int(last_employee.employee_id[3:])
                    self.employee_id = f"EMP{last_num + 1:04d}"
                except ValueError:
                    self.employee_id = "EMP0001"
            else:
                self.employee_id = "EMP0001"
        super().save(*args, **kwargs)
    email = models.EmailField(unique=True, default='placeholder@example.com')
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Personal information
    national_id = models.CharField(max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    # Employment details (department, position, reports_to, dates, employee_type)
    # and emergency contact info now live in EmploymentDetails/EmergencyContact below.

# Phase 1: New Normalized Models for HR
class EmployeeContact(models.Model):
    employee = models.OneToOneField(Employees, on_delete=models.CASCADE, related_name='contact_profile')
    personal_email = models.EmailField(null=True, blank=True)
    work_email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'hr_employeecontact'

class EmergencyContact(models.Model):
    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)

    class Meta:
        db_table = 'hr_emergencycontact'

class EmploymentDetails(models.Model):
    employee = models.OneToOneField(Employees, on_delete=models.CASCADE, related_name='employment_details')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, blank=True)
    reports_to = models.ForeignKey(Employees, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    date_joined = models.DateField(null=True, blank=True)
    contract_from = models.DateField(null=True, blank=True)
    contract_to = models.DateField(null=True, blank=True)
    employee_type = models.CharField(max_length=50, default='Full-time')

    class Meta:
        db_table = 'hr_employmentdetails'

class InsuranceOption(models.Model):
    # TODO: Add fields for InsuranceOption model
    pass

class MedicalAidPlan(models.Model):
    # TODO: Add fields for MedicalAidPlan model
    pass

class PensionFund(models.Model):
    # TODO: Add fields for PensionFund model
    pass

class Position(models.Model):
    # TODO: Add fields for Position model
    title = models.CharField(max_length=100, unique=True, default='IT Manager')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    pass

class Role(models.Model):
    # TODO: Add fields for Role model
    name = models.CharField(max_length=100, unique=True, default='ADMIN')
    display_name = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    permissions = models.JSONField(default=list) # Assuming a JSONField for permissions
    pass

class TrainingCertification(models.Model):
    # TODO: Add fields for TrainingCertification model
    pass

class TrainingEnrollment(models.Model):
    # TODO: Add fields for TrainingEnrollment model
    pass

class TrainingProgram(models.Model):
    # TODO: Add fields for TrainingProgram model
    pass

class TrainingSession(models.Model):
    # TODO: Add fields for TrainingSession model
    pass

class Union(models.Model):
    # TODO: Add fields for Union model
    pass
