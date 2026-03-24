# Payroll Module

Salary processing, tax calculation, and payslips.

## Domain

### Aggregates

**TaxTable** (root):
- id, currency
- brackets (list of TaxBracket)
- effective_from

**Payroll** (root):
- id, period (year, month)
- status (Open, Processing, Closed)
- processed_at, processed_by

**Payslip** (root):
- id, payroll_id, employee_id
- period
- base_salary_usd/zig, allowances_usd/zig, gross_usd/zig
- paye_usd/zig, aids_levy_usd/zig
- nssa_employee_usd/zig, nssa_employer_usd/zig
- other_deductions_usd/zig, total_deductions_usd/zig
- net_salary_usd/zig
- exchange_rate, status

**ExchangeRate** (root):
- id, date, zig_to_usd_rate

**AllowanceType** / **DeductionType**:
- id, name, description
- default_amount, currency

### Value Objects

- `TaxBracket`: min, max, rate, deduction
- `PayrollPeriod`: year, month
- `PayslipStatus`: Draft, Processed, Paid
- `Earnings`: breakdown
- `Deductions`: breakdown

### Domain Services

- `TaxCalculator`: PAYE calculation using brackets
- `NSSACalculator`: 4.5% employee, 4.5% employer
- `AIDSLevyCalculator`: 3% of PAYE
- `AllowanceCalculator`: Sum employee allowances
- `DeductionCalculator`: Sum employee deductions
- `GrossPayCalculator`: Base + allowances
- `NetPayCalculator`: Gross - all deductions
- `PayslipGenerator`: Orchestrate full calculation

### Events

- `PayrollOpened`
- `PayrollProcessed`
- `PayrollClosed`
- `PayslipGenerated`
- `PayslipPaid`

## Interfaces Exposed

```python
class IPayrollProvider(Protocol):
    def get_payslip(self, employee_id: int, period: Period) -> PayslipDTO: ...
    def get_payroll_summary(self, period: Period) -> PayrollSummaryDTO: ...
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payroll/` | List payrolls |
| POST | `/api/payroll/process/` | Process payroll |
| GET | `/api/payroll/payslips/` | List payslips |
| GET | `/api/payroll/payslips/{id}/` | Get payslip |
| GET | `/api/payroll/rates/` | Exchange rates |
| POST | `/api/payroll/rates/` | Set exchange rate |
| GET | `/api/payroll/tax-tables/` | Tax tables |

## Dependencies

- HR Module (IEmployeeProvider)
- Leave Module (ILeaveProvider)
- Accounts Module (via events)
