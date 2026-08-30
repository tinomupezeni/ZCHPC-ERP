import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_root.settings')
os.environ['USE_SQLITE'] = '1'
django.setup()

from modules.bff.orchestrators.employee_orchestrator import EmployeeOrchestrator
from modules.hr.infrastructure.persistence.models import Employees

def test_bff():
    # 1. Create a dummy employee
    emp = Employees.objects.create(
        first_name="Test",
        surname="User",
        email="test.user@example.com",
        phone="1234567890"
    )
    
    # 2. Update via BFF (this will create related models)
    data = {
        "usd_salary": 5000.00,
        "zig_salary": 2000.00,
        "bank_name": "Test Bank",
        "bank_account": "ACC123456",
        "nssa_number": "NSSA-999"
    }
    updated_data = EmployeeOrchestrator.update_full_profile(emp.uuid, data)
    
    print("--- UPDATE RESULT ---")
    print(updated_data)
    
    # 3. Read via BFF
    read_data = EmployeeOrchestrator.get_full_profile(emp.uuid)
    print("\n--- READ RESULT ---")
    print(read_data)
    
    # Verify
    assert read_data["usd_salary"] == 5000.00
    assert read_data["bank_name"] == "Test Bank"
    assert read_data["nssa_number"] == "NSSA-999"
    assert read_data["first_name"] == "Test"
    print("\nSUCCESS: All fields correctly routed and saved across multiple tables!")

    # Cleanup
    emp.delete()

if __name__ == '__main__':
    test_bff()
