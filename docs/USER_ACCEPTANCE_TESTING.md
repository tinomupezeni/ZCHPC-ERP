# User Acceptance Testing (UAT)

User Acceptance Testing (UAT) is the final phase of the software development lifecycle before a feature or release is deployed to production. This document outlines how UAT is conducted for ZCHPC ERP.

## 1. UAT Objectives
- Validate that the system meets the business requirements of the Zimbabwe Centre for High Performance Computing.
- Ensure usability from the perspective of non-technical end-users.
- Verify role-based access and security protocols in a production-like environment.

---

## 2. UAT Environment

UAT is conducted on a dedicated staging environment (or local equivalent mimicking production).
- **Database**: Populated with sanitized, production-like data to simulate real-world scale and scenarios.
- **Configuration**: Environment variables match production (with the exception of email hosts, which point to a mailtrap/sandbox).

---

## 3. Role-Based Testing Scenarios

Because ZCHPC ERP relies heavily on Role-Based Access Control (RBAC), testers must validate workflows using specific personas.

### 3.1 Employee Persona (Employee Portal)
- **Login**: Verify first-time login requires password change (default `erp@1234`).
- **Attendance**: Test the QR Clock-in/Clock-out mechanism.
- **Leave**: Submit a leave request, check leave balance deduction, and verify status updates.
- **Payroll**: Download and view monthly payslips.

### 3.2 HR Admin Persona (ERP Admin Frontend)
- **Employee Management**: Create a new employee, assign a department, and verify they can access the portal.
- **Leave Management**: Approve/Reject pending leave requests. Ensure proper validation (e.g., rejecting if insufficient balance).
- **Attendance Adjustments**: Manually correct missed clock-ins.

### 3.3 Accountant Persona (ERP Admin Frontend)
- **Payroll Processing**: Run a multi-currency payroll batch (USD/ZIG) and verify tax calculations.
- **Accounting**: Create a chart of accounts entry and post a journal entry.
- **Procurement**: Approve a purchase order.

---

## 4. Testing Execution Process

1. **Test Scripts Formulation**: QA team provides step-by-step UAT scripts mapped to user stories.
2. **Session Facilitation**: Super-users (department heads) are given access to the staging environment to run through the scripts.
3. **Issue Reporting**: Bugs or usability issues are logged via the internal IT Support Portal (or Jira) and tagged as `UAT-Defect`.
4. **Defect Triage**: `UAT-Defect` tickets bypass standard triage and go straight into the immediate Bug Fixing Buffer.

---

## 5. UAT Sign-Off Criteria

A feature is approved for production deployment only when:
- **No Critical/High Defects**: All P0 and P1 bugs identified during UAT are resolved and verified.
- **Usability Approved**: End-users confirm the workflow is logical and matches their business processes.
- **Stakeholder Sign-off**: The product owner or department head provides written approval for the release.
