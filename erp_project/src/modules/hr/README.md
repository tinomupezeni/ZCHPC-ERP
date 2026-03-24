# HR Core Module

Employee and organizational management.

## Domain

### Aggregates

**Employee** (root):
- Personal: first_name, surname, national_id, dob, gender, marital_status
- Contact: email, phone
- Employment: department_id, position_id, role_id, employee_type, date_joined
- Contract: contract_from, contract_to, is_active
- Compensation: usd_salary, zig_salary, pay_frequency
- Banking: bank_name, bank_account
- Statutory: nssa_number, paye_number, zimra_number
- Emergency: contact_name, contact_phone, contact_relationship

**Department** (root): id, name, description

**Position** (root): id, title, department_id, description

### Value Objects

- `EmploymentType`: FullTime, PartTime, Contract, Intern
- `Salary`: usd_amount, zig_amount
- `BankAccount`: bank_name, account_number

### Domain Services

- `EmployeeIdGenerator`: Generate next EMP number
- `EmployeeValidator`: Business rule validation

### Events

- `EmployeeHired`
- `EmployeeTerminated`
- `EmployeeUpdated`
- `SalaryChanged`
- `DepartmentChanged`

## Interfaces Exposed

```python
class IEmployeeProvider(Protocol):
    def get_employee(self, id: int) -> EmployeeDTO: ...
    def get_employee_by_employee_id(self, employee_id: str) -> EmployeeDTO: ...
    def get_active_employees(self) -> list[EmployeeDTO]: ...
    def get_employees_by_department(self, dept_id: int) -> list[EmployeeDTO]: ...
    def get_employee_salary(self, id: int) -> SalaryDTO: ...

class IDepartmentProvider(Protocol):
    def get_department(self, id: int) -> DepartmentDTO: ...
    def get_all_departments(self) -> list[DepartmentDTO]: ...
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/hr/employees/` | List employees |
| POST | `/api/hr/employees/` | Create employee |
| GET | `/api/hr/employees/{id}/` | Get employee |
| PUT | `/api/hr/employees/{id}/` | Update employee |
| GET | `/api/hr/departments/` | List departments |
| GET | `/api/hr/positions/` | List positions |

## Dependencies

- Identity Module (ICurrentUserProvider)
