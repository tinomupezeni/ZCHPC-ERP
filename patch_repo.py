import re

with open("erp_project/src/modules/hr/infrastructure/persistence/employee_repository.py", "r") as f:
    content = f.read()

# Remove add/update field assignments
fields_to_remove = [
    r'\s*leave_days_entitled=employee\.leave_days_entitled,',
    r'\s*usd_salary=employee\.salary\.usd_amount if employee\.salary else None,',
    r'\s*zig_salary=employee\.salary\.zig_amount if employee\.salary else None,',
    r'\s*pay_frequency=employee\.pay_frequency\.value,',
    r'\s*bank_name=employee\.bank_account\.bank_name,',
    r'\s*bank_account=employee\.bank_account\.account_number,',
    r'\s*pension_fund=employee\.pension_fund,',
    r'\s*nssa_number=employee\.statutory_info\.nssa_number,',
    r'\s*zimra_tax_number=employee\.statutory_info\.zimra_number,',
    r'\s*paye_number=employee\.statutory_info\.paye_number,',
    r'\s*pays_aids_levy=employee\.statutory_info\.pays_aids_levy,'
]

for field in fields_to_remove:
    content = re.sub(field, '', content)

# Remove salary, bank_account, etc from _to_entity
content = re.sub(r'\s*# Build salary\n.*?# Build value objects', '\n        # Build value objects', content, flags=re.DOTALL)
content = re.sub(r'\s*leave_days_entitled=db_employee\.leave_days_entitled,', '', content)
content = re.sub(r'\s*salary=salary,', '', content)
content = re.sub(r'\s*pay_frequency=PayFrequency\.from_string\(db_employee\.pay_frequency\),', '', content)
content = re.sub(r'\s*bank_account=BankAccount\(\n.*?\),', '', content, flags=re.DOTALL)
content = re.sub(r'\s*statutory_info=StatutoryInfo\(\n.*?\),', '', content, flags=re.DOTALL)
content = re.sub(r'\s*pension_fund=db_employee\.pension_fund or "",', '', content)

with open("erp_project/src/modules/hr/infrastructure/persistence/employee_repository.py", "w") as f:
    f.write(content)
