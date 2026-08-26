# API Reference

Complete REST API documentation for the ZCHPC ERP system.

## Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## Authentication

All protected endpoints require JWT Bearer token authentication:

```
Authorization: Bearer <access_token>
```

---

## Authentication Endpoints

### Login

```http
POST /auth/token/
```

**Request:**
```json
{
  "email": "user@zchpc.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "uuid",
    "email": "user@zchpc.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "employee_profile": {
      "employee_id": "EMP0001",
      "role": "HR",
      "role_display_name": "Human Resources",
      "department": "Human Resources",
      "position": "HR Manager",
      "date_joined": "2024-01-15",
      "role_permissions": ["hr.*", "employees.*"]
    }
  }
}
```

### Refresh Token

```http
POST /auth/token/refresh/
```

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Get Current User

```http
GET /auth/users/me/
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@zchpc.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "employee_profile": { ... }
}
```

### List Users (Admin)

```http
GET /auth/users/
```

### Create User

```http
POST /auth/users/
```

**Request:**
```json
{
  "email": "newuser@zchpc.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": 1,
  "department": 2
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "newuser@zchpc.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "temp_password": "temp-password"
}
```

### Unlock User Account

```http
POST /auth/users/{id}/unlock/
```

### Audit Logs

```http
GET /auth/logs/
```

---

## Human Resources Endpoints

### Employees

#### List Employees
```http
GET /hr/employees/
```

**Query Parameters:**
- `department` - Filter by department ID
- `is_active` - Filter by active status (true/false)
- `search` - Search by name, email, employee_id

**Response (200):**
```json
[
  {
    "id": 1,
    "employee_id": "EMP0001",
    "first_name": "John",
    "surname": "Doe",
    "email": "john.doe@zchpc.com",
    "phone": "+263771234567",
    "department": { "id": 1, "name": "IT" },
    "position": { "id": 1, "title": "Developer" },
    "role": { "id": 1, "name": "STAFF", "display_name": "Staff" },
    "date_joined": "2024-01-15",
    "is_active": true,
    "usd_salary": "2500.00",
    "zig_salary": "25000.00"
  }
]
```

#### Get Employee
```http
GET /hr/employees/{id}/
```

#### Create Employee
```http
POST /hr/employees/
```

**Request:**
```json
{
  "first_name": "Jane",
  "surname": "Smith",
  "national_id": "63-123456-A-78",
  "date_of_birth": "1990-05-15",
  "gender": "Female",
  "marital_status": "Single",
  "email": "jane.smith@zchpc.com",
  "phone": "+263771234567",
  "department": 1,
  "position": 1,
  "role": 2,
  "employee_type": "Full-time",
  "date_joined": "2024-03-01",
  "contract_from": "2024-03-01",
  "contract_to": "2026-03-01",
  "usd_salary": "2000.00",
  "zig_salary": "20000.00",
  "pay_frequency": "Monthly",
  "bank_name": "FBC Bank",
  "bank_account": "1234567890",
  "leave_days_entitled": 22,
  "emergency_contact_name": "John Smith",
  "emergency_contact_number": "+263771234567",
  "emergency_contact_relationship": "Spouse"
}
```

#### Update Employee
```http
PATCH /hr/employees/{id}/
```

#### Delete Employee
```http
DELETE /hr/employees/{id}/
```

### Departments

```http
GET /hr/departments/
POST /hr/departments/
GET /hr/departments/{id}/
PUT /hr/departments/{id}/
DELETE /hr/departments/{id}/
```

### Positions

```http
GET /hr/positions/
POST /hr/positions/
GET /hr/positions/{id}/
PUT /hr/positions/{id}/
DELETE /hr/positions/{id}/
```

**Query Parameters:**
- `department` - Filter by department ID

### Roles

```http
GET /hr/roles/
POST /hr/roles/
GET /hr/roles/{id}/
PUT /hr/roles/{id}/
DELETE /hr/roles/{id}/
```

### Jobs (Recruitment)

#### List Jobs
```http
GET /hr/jobs/
```

**Query Parameters:**
- `status` - Filter by status (Open, Closed, Draft)
- `is_internal` - Filter internal jobs (true/false)

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Software Developer",
    "department": { "id": 1, "name": "IT" },
    "position": { "id": 1, "title": "Developer" },
    "status": "Open",
    "location": "Harare",
    "salary_usd_min": 2000,
    "salary_usd_max": 3500,
    "salary_zig_min": 20000,
    "salary_zig_max": 35000,
    "description": "Job description...",
    "responsibilities": ["Develop software", "Code review"],
    "qualifications": ["BSc Computer Science", "3+ years experience"],
    "competencies": ["Python", "Django", "React"],
    "is_internal": false,
    "posted_date": "2024-03-01",
    "reports_to": "IT Manager",
    "application_process": "Submit resume and cover letter",
    "contact_email": "hr@zchpc.ac.zw"
  }
]
```

#### Create Job
```http
POST /hr/jobs/
```

#### Get Job
```http
GET /hr/jobs/{id}/
```

#### Update Job
```http
PATCH /hr/jobs/{id}/
```

#### Delete Job
```http
DELETE /hr/jobs/{id}/
```

### Job Applications

```http
GET /hr/applications/
GET /hr/applications/{id}/
PATCH /hr/applications/{id}/
```

**Update Application Status:**
```json
{
  "status": "Shortlisted"
}
```

Status values: `Pending`, `Shortlisted`, `Interview`, `Offered`, `Hired`, `Rejected`

### Leave Types

```http
GET /hr/leave-types/
POST /hr/leave-types/
GET /hr/leave-types/{id}/
PUT /hr/leave-types/{id}/
DELETE /hr/leave-types/{id}/
```

### Leave Balances

```http
GET /hr/leave-balances/
POST /hr/leave-balances/
GET /hr/leave-balances/{id}/
PUT /hr/leave-balances/{id}/
```

**Query Parameters:**
- `employee` - Filter by employee ID
- `year` - Filter by year

### Leave Requests

```http
GET /hr/leave-requests/
POST /hr/leave-requests/
GET /hr/leave-requests/{id}/
PUT /hr/leave-requests/{id}/
DELETE /hr/leave-requests/{id}/
```

**Create Leave Request:**
```json
{
  "employee": 1,
  "leave_type": 1,
  "start_date": "2024-04-01",
  "end_date": "2024-04-05",
  "reason": "Annual vacation"
}
```

**Approve/Reject:**
```json
{
  "status": "Approved",
  "reviewed_by": 5
}
```

### Attendance

```http
GET /hr/attendance/
POST /hr/attendance/
```

**Query Parameters:**
- `employee` - Filter by employee ID
- `date` - Filter by specific date
- `date__gte` - Filter from date
- `date__lte` - Filter to date

### Training Programs

```http
GET /hr/training-programs/
POST /hr/training-programs/
GET /hr/training-programs/{id}/
PUT /hr/training-programs/{id}/
DELETE /hr/training-programs/{id}/
```

### Training Sessions

```http
GET /hr/training-sessions/
POST /hr/training-sessions/
GET /hr/training-sessions/{id}/
PUT /hr/training-sessions/{id}/
DELETE /hr/training-sessions/{id}/
```

### Training Enrollments

```http
GET /hr/training-enrollments/
POST /hr/training-enrollments/
```

### Certifications

```http
GET /hr/certifications/
POST /hr/certifications/
```

### HR Dashboard

```http
GET /hr/dashboard/
```

**Response (200):**
```json
{
  "total_employees": 150,
  "active_employees": 145,
  "new_this_month": 5,
  "departments_count": 8,
  "pending_leave_requests": 12,
  "attendance_today": 140
}
```

### HR Reports

```http
GET /hr/reports/leave-balances/
GET /hr/reports/paye/
GET /hr/reports/nssa/
GET /hr/reports/employees/
GET /hr/reports/training/
GET /hr/reports/summary/
```

**Query Parameters:**
- `period` - Month (YYYY-MM format)
- `department` - Department ID

---

## Payroll Endpoints

### List Payrolls

```http
GET /payroll/payrolls/
```

**Query Parameters:**
- `period` - Filter by month (YYYY-MM format)
- `status` - Filter by status (Draft, Pending, Processed, Paid)

**Response (200):**
```json
[
  {
    "id": 1,
    "employee": 1,
    "employee_id": "EMP0001",
    "employee_name": "John Doe",
    "employee_department": "IT",
    "employee_position": "Developer",
    "period": "2024-03-01",
    "base_salary_usd": "2500.00",
    "base_salary_zig": "25000.00",
    "net_salary_usd": "2125.00",
    "net_salary_zig": "21250.00",
    "paye_usd": "250.00",
    "paye_zig": "2500.00",
    "aids_levy_usd": "7.50",
    "aids_levy_zig": "75.00",
    "nssa_employee_usd": "112.50",
    "nssa_employee_zig": "1125.00",
    "total_allowances_usd": "300.00",
    "total_deductions_usd": "375.00",
    "exchange_rate": "10.0000",
    "status": "Processed"
  }
]
```

### Process Payroll

```http
POST /payroll/payrolls/process/
```

**Request:**
```json
{
  "month": "2024-03"
}
```

**Response (200):**
```json
{
  "message": "Payroll processed successfully",
  "processed_count": 145,
  "period": "2024-03-01"
}
```

### Approve Payslip

```http
POST /payroll/payrolls/{id}/approve/
```

### Payroll Summary

```http
GET /payroll/payrolls/summary/
```

**Query Parameters:**
- `period` - Month (YYYY-MM format)

**Response (200):**
```json
{
  "period": "2024-03",
  "total_employees": 145,
  "total_gross_usd": "362500.00",
  "total_gross_zig": "3625000.00",
  "total_net_usd": "308125.00",
  "total_net_zig": "3081250.00",
  "total_paye_usd": "36250.00",
  "total_nssa_employee_usd": "16312.50",
  "total_nssa_employer_usd": "16312.50"
}
```

### Exchange Rates

```http
GET /payroll/rates/
POST /payroll/rates/
```

**Create Rate:**
```json
{
  "date": "2024-03-15",
  "average": "10.5000"
}
```

---

## Accounts Endpoints

### Chart of Accounts

```http
GET /accounts/accounts/
POST /accounts/accounts/
GET /accounts/accounts/{id}/
PUT /accounts/accounts/{id}/
DELETE /accounts/accounts/{id}/
```

### Journal Entries

```http
GET /accounts/moves/
POST /accounts/moves/
GET /accounts/moves/{id}/
PUT /accounts/moves/{id}/
```

**Create Journal Entry:**
```json
{
  "journal": 1,
  "date": "2024-03-15",
  "ref": "JV-2024-001",
  "narration": "Monthly salary expense",
  "lines": [
    {
      "account": 100,
      "debit": "362500.00",
      "credit": "0.00"
    },
    {
      "account": 200,
      "debit": "0.00",
      "credit": "362500.00"
    }
  ]
}
```

### Analytic Accounts

```http
GET /accounts/analytic-accounts/
POST /accounts/analytic-accounts/
GET /accounts/analytic-accounts/{id}/
PUT /accounts/analytic-accounts/{id}/
DELETE /accounts/analytic-accounts/{id}/
```

### Partners

```http
GET /accounts/partners/
POST /accounts/partners/
GET /accounts/partners/{id}/
PUT /accounts/partners/{id}/
DELETE /accounts/partners/{id}/
```

### Currencies

```http
GET /accounts/currencies/
POST /accounts/currencies/
GET /accounts/currencies/{id}/
PUT /accounts/currencies/{id}/
DELETE /accounts/currencies/{id}/
```

### Financial Reports

```http
GET /accounts/reports/trial-balance/
GET /accounts/reports/profit-loss/
GET /accounts/reports/balance-sheet/
GET /accounts/reports/analytic/
```

**Query Parameters:**
- `date_from` - Start date
- `date_to` - End date
- `analytic_account` - Filter by cost center

---

## Employee Portal Endpoints

### Portal Authentication

```http
POST /portal/auth/login/
POST /portal/auth/refresh/
POST /portal/auth/logout/
GET /portal/auth/me/
```

**Portal Login:**
```json
{
  "ec_number": "EMP0001",
  "password": "password123"
}
```

### Portal Attendance

#### Get Status
```http
GET /portal/attendance/status/
```

**Response (200):**
```json
{
  "date": "2024-03-15",
  "clock_in": "08:30:00",
  "clock_out": null,
  "status": "clocked_in",
  "hours_worked": null
}
```

#### Manual Clock In/Out
```http
POST /portal/attendance/clock/
```

**Response (200):**
```json
{
  "action": "clock_in",
  "message": "Clocked in at 08:30",
  "date": "2024-03-15",
  "clock_in": "08:30:00",
  "clock_out": null,
  "hours_worked": null
}
```

#### Get QR Token (Public)
```http
GET /portal/attendance/qr/token/
```

**Response (200):**
```json
{
  "token": "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW",
  "expires_at": "2024-03-15T08:30:30Z",
  "time_remaining": 28,
  "validity_seconds": 30
}
```

#### QR Clock In
```http
POST /portal/attendance/qr/clock-in/
```

**Request:**
```json
{
  "token": "aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW"
}
```

**Response (200):**
```json
{
  "action": "clock_in",
  "message": "Successfully clocked in at 08:30",
  "date": "2024-03-15",
  "clock_in": "08:30:00",
  "clock_out": null,
  "hours_worked": null
}
```

**Error Response (400):**
```json
{
  "detail": "Invalid or expired QR code. Please scan the current code displayed at the office."
}
```

#### Attendance History
```http
GET /portal/attendance/history/
```

**Query Parameters:**
- `start_date` - From date (YYYY-MM-DD)
- `end_date` - To date (YYYY-MM-DD)
- `page` - Page number
- `page_size` - Records per page (default 30)

#### Attendance Summary
```http
GET /portal/attendance/summary/
```

**Query Parameters:**
- `month` - Month (1-12)
- `year` - Year

**Response (200):**
```json
{
  "month": 3,
  "year": 2024,
  "total_working_days": 22,
  "days_present": 18,
  "days_absent": 2,
  "days_late": 3,
  "days_on_leave": 2,
  "total_hours_worked": 144.5,
  "average_clock_in": "08:30:00",
  "average_clock_out": "17:30:00"
}
```

### Portal Leave

#### Get Leave Types
```http
GET /portal/leave/types/
```

#### Get Leave Balances
```http
GET /portal/leave/balances/
```

**Response (200):**
```json
[
  {
    "id": 1,
    "leave_type": 1,
    "leave_type_name": "Annual Leave",
    "year": 2024,
    "days_allowed": 22,
    "days_remaining": 18,
    "days_used": 4,
    "percentage_used": 18.18
  }
]
```

#### Leave Requests CRUD
```http
GET /portal/leave/requests/
POST /portal/leave/requests/
GET /portal/leave/requests/{id}/
PUT /portal/leave/requests/{id}/
DELETE /portal/leave/requests/{id}/
```

#### Cancel Leave Request
```http
POST /portal/leave/requests/{id}/cancel/
```

### Portal Payslips

#### List Payslips
```http
GET /portal/payslips/
```

**Query Parameters:**
- `year` - Filter by year

#### Get Payslip Detail
```http
GET /portal/payslips/{id}/
```

#### Download Payslip
```http
GET /portal/payslips/{id}/download/
```

Returns PDF file.

#### Year Summary
```http
GET /portal/payslips/summary/
```

### Public Job Endpoints (No Auth)

#### List Public Jobs
```http
GET /portal/public/jobs/
```

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Software Developer",
    "department": "IT",
    "location": "Harare",
    "salary_usd_min": 2000,
    "salary_usd_max": 3500,
    "description": "...",
    "qualifications": ["..."],
    "responsibilities": ["..."],
    "posted_date": "2024-03-01",
    "is_internal": false
  }
]
```

#### Get Job Detail
```http
GET /portal/public/jobs/{id}/
```

#### Check If Already Applied
```http
POST /portal/public/jobs/check-application/
```

**Request:**
```json
{
  "id_number": "63-123456-A-78",
  "job_id": 1
}
```

**Response (200):**
```json
{
  "has_applied": false
}
```

#### Submit Application
```http
POST /portal/public/jobs/apply/
Content-Type: multipart/form-data
```

**Form Fields:**
- `job_id` - Job ID
- `id_number` - National ID
- `first_name` - First name
- `last_name` - Last name
- `email` - Email address
- `phone` - Phone number
- `address` - Physical address
- `date_of_birth` - Date of birth (YYYY-MM-DD)
- `qualifications` - Qualifications text
- `experience` - Experience text
- `cover_letter` - Cover letter text
- `resume` - Resume file (PDF/DOC)

#### Check Application Status
```http
POST /portal/public/applications/status/
```

**Request:**
```json
{
  "id_number": "63-123456-A-78"
}
```

**Response (200):**
```json
[
  {
    "id": 1,
    "job_title": "Software Developer",
    "job_department": "IT",
    "applied_on": "2024-03-10T10:30:00Z",
    "status": "Shortlisted"
  }
]
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data",
  "errors": {
    "email": ["This field is required."],
    "password": ["Password must be at least 8 characters."]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error."
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Consider adding for production:
- Login endpoint: 5 attempts per minute
- API endpoints: 100 requests per minute

---

## Pagination

List endpoints support pagination:

```http
GET /hr/employees/?page=1&page_size=20
```

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/hr/employees/?page=2",
  "previous": null,
  "results": [...]
}
```
