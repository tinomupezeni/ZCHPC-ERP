# Attendance Module

Time tracking and QR-based clock in/out.

## Domain

### Aggregates

**AttendanceRecord** (root):
- id, employee_id, date
- time_in, time_out
- status (calculated)

**QRToken** (root):
- id, token (32 chars)
- created_at, expires_at
- is_active, used_count

### Value Objects

- `ClockTime`: Time value
- `AttendanceStatus`: Present, Absent, Late, HalfDay
- `WorkDuration`: hours, minutes

### Domain Services

- `QRTokenGenerator`: Generate secure tokens
- `QRTokenValidator`: Validate and expire tokens
- `AttendanceSummaryCalculator`: Monthly summaries
- `LateArrivalDetector`: Check against schedule

### Events

- `EmployeeClockedIn`
- `EmployeeClockedOut`
- `QRTokenGenerated`
- `QRTokenUsed`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance/` | List attendance records |
| POST | `/api/attendance/clock-in/` | Manual clock in |
| POST | `/api/attendance/clock-out/` | Manual clock out |
| GET | `/api/attendance/qr/token/` | Get current QR token |
| POST | `/api/attendance/qr/clock-in/` | QR-based clock in |
| GET | `/api/attendance/summary/` | Monthly summary |

## Dependencies

- HR Module (IEmployeeProvider)
