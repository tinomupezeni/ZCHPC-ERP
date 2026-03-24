"""
Attendance Module.

Handles employee time tracking and QR-based clock in/out.

Key Features:
- Manual clock-in/out
- QR code-based attendance (rotating tokens)
- Attendance history and summaries
- Late arrival detection
- Work duration calculations

API Endpoints (v2):
- POST /api/v2/attendance/clock-in/     - Manual clock in
- POST /api/v2/attendance/clock-out/    - Manual clock out
- GET  /api/v2/attendance/status/       - Today's status
- GET  /api/v2/attendance/history/      - Attendance history
- GET  /api/v2/attendance/summary/      - Monthly summary
- GET  /api/v2/attendance/qr/token/     - Get current QR token (public)
- POST /api/v2/attendance/qr/clock-in/  - QR-based clock in/out
"""
