import re

with open("erp_project/src/modules/hr/infrastructure/persistence/models.py", "r") as f:
    content = f.read()

# Fields to remove
fields_to_remove = [
    r'\s*# Salary information\n',
    r'\s*usd_salary = models\.DecimalField\(max_digits=12, decimal_places=2, null=True, blank=True\)\n',
    r'\s*zig_salary = models\.DecimalField\(max_digits=12, decimal_places=2, null=True, blank=True\)\n',
    r'\s*pay_frequency = models\.CharField\(max_length=20, default=\'monthly\'\)\n',
    r'\s*# Banking information\n',
    r'\s*bank_name = models\.CharField\(max_length=100, null=True, blank=True\)\n',
    r'\s*bank_account = models\.CharField\(max_length=50, null=True, blank=True\)\n',
    r'\s*# Statutory information\n',
    r'\s*nssa_number = models\.CharField\(max_length=50, null=True, blank=True\)\n',
    r'\s*zimra_tax_number = models\.CharField\(max_length=50, null=True, blank=True\)\n',
    r'\s*paye_number = models\.CharField\(max_length=50, null=True, blank=True\)\n',
    r'\s*pays_aids_levy = models\.BooleanField\(default=True\)\n',
    r'\s*# Pension fund\n',
    r'\s*pension_fund = models\.CharField\(max_length=100, null=True, blank=True\)\n',
    r'\s*leave_days_entitled = models\.IntegerField\(default=20\)\n',
]

for field in fields_to_remove:
    content = re.sub(field, '', content)

with open("erp_project/src/modules/hr/infrastructure/persistence/models.py", "w") as f:
    f.write(content)
