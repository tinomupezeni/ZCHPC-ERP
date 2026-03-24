"""
Portal Module - Employee Self-Service Portal

This module provides a unified employee portal with:
- EC number based authentication
- Dashboard with aggregated data from multiple modules
- Attendance tracking with QR code support
- Leave request management
- Payslip viewing
- Expense claim submission
- Support ticket system
- Document management
- Notification system
- Public job applications

API Endpoints: /api/v2/portal/

Module Structure:
- domain/: Domain layer (entities, value objects)
- application/: Application layer (services, interfaces)
- infrastructure/: Infrastructure layer (Django providers, repositories)
- api/: API layer (views, serializers, URLs)

For backwards compatibility, legacy endpoints at /api/portal/
are still available but deprecated.
"""
