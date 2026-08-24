import re

with open("erp_project/src/modules/hr/api/serializers/employee_serializers.py", "r") as f:
    content = f.read()

fields_to_remove = [
    r'\s*leave_days_entitled = EmptyStringToNullIntegerField\(.*?22\)',
    r'\s*leave_days_entitled = serializers\.IntegerField\(.*?allow_null=True\)',
    r'\s*usd_salary = serializers\.DecimalField\(\n.*?\)',
    r'\s*zig_salary = serializers\.DecimalField\(\n.*?\)',
    r'\s*pay_frequency = serializers\.CharField\(.*?\)',
    r'\s*pay_frequency = serializers\.ChoiceField\(\n.*?\)',
    r'\s*bank_name = serializers\.CharField\(.*?\)',
    r'\s*bank_account = serializers\.CharField\(.*?\)',
    r'\s*nssa_number = serializers\.CharField\(.*?\)',
    r'\s*zimra_number = serializers\.CharField\(.*?\)',
    r'\s*paye_number = serializers\.CharField\(.*?\)',
    r'\s*pays_aids_levy = serializers\.BooleanField\(.*?\)',
    r'\s*pension_fund = serializers\.CharField\(.*?\)',
]

for field in fields_to_remove:
    content = re.sub(field, '', content)

with open("erp_project/src/modules/hr/api/serializers/employee_serializers.py", "w") as f:
    f.write(content)
