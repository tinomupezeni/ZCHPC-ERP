import re

with open("erp_project/src/modules/hr/domain/entities/employee.py", "r") as f:
    content = f.read()

# Remove initializers
content = re.sub(r'\s*self\.salary = salary\n', '\n', content)
content = re.sub(r'\s*self\.pay_frequency = pay_frequency\n', '\n', content)
content = re.sub(r'\s*self\.bank_account = bank_account or BankAccount\.empty\(\)\n', '\n', content)
content = re.sub(r'\s*self\.statutory_info = statutory_info or StatutoryInfo\.empty\(\)\n', '\n', content)
content = re.sub(r'\s*self\.pension_fund = pension_fund\n', '\n', content)
content = re.sub(r'\s*self\.leave_days_entitled = leave_days_entitled\n', '\n', content)

# Remove update methods
content = re.sub(r'    def update_salary\(.*?return old_salary\n', '', content, flags=re.DOTALL)
content = re.sub(r'    def update_bank_account\(.*?self\.updated_at = datetime\.utcnow\(\)\n', '', content, flags=re.DOTALL)
content = re.sub(r'    def update_statutory_info\(.*?self\.updated_at = datetime\.utcnow\(\)\n', '', content, flags=re.DOTALL)

with open("erp_project/src/modules/hr/domain/entities/employee.py", "w") as f:
    f.write(content)
