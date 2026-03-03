# Employee Portal - Full Implementation Plan

## Project Overview
A separate React.js Vite application providing employees with self-service capabilities, QR-based attendance, request management, and company resource access.

**Tech Stack:**
- Frontend: React.js + Vite + TypeScript
- UI: Tailwind CSS + shadcn/ui
- Backend: Django REST Framework
- Database: PostgreSQL (existing)
- Authentication: EC Number + Password (JWT)

---

# PHASE 1: Foundation & Authentication
**Duration: 3-4 days**

## 1.1 Project Initialization

### Frontend Setup
```
Files to create:
├── employee-portal/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   └── vite-env.d.ts
```

**Tasks:**
- [ ] Initialize Vite React TypeScript project
- [ ] Install dependencies (tailwindcss, axios, react-router-dom, date-fns, lucide-react)
- [ ] Configure Tailwind CSS
- [ ] Setup shadcn/ui components
- [ ] Create base folder structure

### Backend Setup
```
Files to create/modify:
├── erp_project/
│   ├── employee_portal/              # New Django app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── auth_views.py
│   │   │   └── profile_views.py
│   │   └── serializers/
│   │       ├── __init__.py
│   │       └── auth_serializers.py
```

**Tasks:**
- [ ] Create `employee_portal` Django app
- [ ] Register app in settings.py
- [ ] Add URL routing in main urls.py

---

## 1.2 Authentication System

### Backend Files
```
employee_portal/views/auth_views.py
employee_portal/serializers/auth_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/portal/auth/login/` | EC Number + Password login |
| POST | `/api/portal/auth/refresh/` | Refresh JWT token |
| POST | `/api/portal/auth/logout/` | Logout (blacklist token) |
| GET | `/api/portal/auth/me/` | Get current user info |

**Backend Tasks:**
- [ ] Create EmployeeLoginSerializer (validates EC number + password)
- [ ] Create EmployeeTokenObtainView (returns JWT + employee data)
- [ ] Create EmployeeProfileView (returns logged-in employee details)
- [ ] Add employee_portal URLs to main router

### Frontend Files
```
src/
├── contexts/
│   └── AuthContext.tsx
├── services/
│   ├── api.ts                    # Axios instance
│   └── auth.service.ts           # Auth API calls
├── pages/
│   └── LoginPage.tsx
├── components/
│   └── ProtectedRoute.tsx
├── hooks/
│   └── useAuth.ts
└── types/
    └── auth.types.ts
```

**Frontend Tasks:**
- [ ] Create AuthContext with login/logout/user state
- [ ] Create api.ts with axios instance + interceptors
- [ ] Create auth.service.ts with login/logout/refresh functions
- [ ] Create LoginPage.tsx with EC number + password form
- [ ] Create ProtectedRoute.tsx for auth guard
- [ ] Setup React Router with public/protected routes

---

## 1.3 Base Layout & Navigation

### Frontend Files
```
src/
├── components/
│   └── layout/
│       ├── MainLayout.tsx        # Main app wrapper
│       ├── MobileNav.tsx         # Bottom navigation (mobile)
│       ├── Sidebar.tsx           # Side navigation (desktop)
│       ├── Header.tsx            # Top header with user menu
│       └── PageHeader.tsx        # Page title component
```

**Tasks:**
- [ ] Create MainLayout with responsive design
- [ ] Create MobileNav (bottom tabs for mobile)
- [ ] Create Header with user avatar and dropdown
- [ ] Create Sidebar for desktop navigation
- [ ] Implement mobile-first responsive breakpoints

---

# PHASE 2: Dashboard & Profile
**Duration: 3-4 days**

## 2.1 Employee Dashboard

### Backend Files
```
employee_portal/views/dashboard_views.py
employee_portal/serializers/dashboard_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/dashboard/` | Dashboard summary data |
| GET | `/api/portal/notifications/` | Employee notifications |
| PATCH | `/api/portal/notifications/{id}/read/` | Mark as read |

**Backend Tasks:**
- [ ] Create DashboardView returning:
  - Leave balances
  - Pending requests count
  - Recent attendance
  - Upcoming events
- [ ] Create NotificationViewSet with list/mark-read

### Frontend Files
```
src/
├── pages/
│   └── DashboardPage.tsx
├── components/
│   └── dashboard/
│       ├── WelcomeCard.tsx
│       ├── StatsCards.tsx
│       ├── LeaveBalanceCard.tsx
│       ├── QuickActions.tsx
│       ├── AnnouncementsList.tsx
│       └── NotificationsDropdown.tsx
├── services/
│   └── dashboard.service.ts
└── types/
    └── dashboard.types.ts
```

**Frontend Tasks:**
- [ ] Create DashboardPage layout
- [ ] Create WelcomeCard with greeting + date
- [ ] Create StatsCards (leave balance, attendance, requests)
- [ ] Create QuickActions (Clock In, Request Leave, etc.)
- [ ] Create AnnouncementsList component
- [ ] Create NotificationsDropdown in header

---

## 2.2 Employee Profile

### Backend Files
```
employee_portal/views/profile_views.py
employee_portal/serializers/profile_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/profile/` | Get employee profile |
| PATCH | `/api/portal/profile/` | Update allowed fields |
| POST | `/api/portal/profile/photo/` | Upload profile photo |

**Backend Tasks:**
- [ ] Create EmployeeProfileSerializer (read + partial update)
- [ ] Define editable fields (phone, emergency contact, address)
- [ ] Create profile photo upload endpoint

### Frontend Files
```
src/
├── pages/
│   └── ProfilePage.tsx
├── components/
│   └── profile/
│       ├── ProfileHeader.tsx      # Photo + name + position
│       ├── PersonalInfoCard.tsx   # Personal details
│       ├── ContactInfoCard.tsx    # Editable contact info
│       ├── EmploymentCard.tsx     # Job details (read-only)
│       ├── EmergencyContactCard.tsx
│       └── EditProfileModal.tsx
├── services/
│   └── profile.service.ts
└── types/
    └── profile.types.ts
```

**Frontend Tasks:**
- [ ] Create ProfilePage with sections
- [ ] Create ProfileHeader with photo upload
- [ ] Create PersonalInfoCard (read-only details)
- [ ] Create ContactInfoCard (editable phone, email)
- [ ] Create EmergencyContactCard (editable)
- [ ] Create EditProfileModal for inline editing

---

# PHASE 3: Attendance System
**Duration: 4-5 days**

## 3.1 QR Code Attendance

### Backend Files
```
employee_portal/views/attendance_views.py
employee_portal/serializers/attendance_serializers.py
employee_portal/utils/qr_validator.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/portal/attendance/clock/` | Clock in/out via QR |
| GET | `/api/portal/attendance/status/` | Current clock status |
| GET | `/api/portal/attendance/history/` | Attendance history |
| GET | `/api/portal/attendance/summary/` | Monthly summary |

**Backend Tasks:**
- [ ] Create QR code generation for office locations
- [ ] Create QRClockSerializer (validates QR token + timestamp)
- [ ] Create ClockInOutView (handles clock in/out logic)
- [ ] Create AttendanceStatusView (today's status)
- [ ] Create AttendanceHistoryView with date filters
- [ ] Create MonthlySummaryView (days worked, hours, etc.)

### Frontend Files
```
src/
├── pages/
│   └── AttendancePage.tsx
├── components/
│   └── attendance/
│       ├── QRScanner.tsx          # Camera QR scanner
│       ├── ClockStatus.tsx        # Current clock status
│       ├── ClockButton.tsx        # Manual clock (fallback)
│       ├── AttendanceCalendar.tsx # Monthly calendar view
│       ├── AttendanceList.tsx     # Daily records list
│       ├── AttendanceSummary.tsx  # Monthly stats
│       └── ScanSuccessModal.tsx   # Success feedback
├── services/
│   └── attendance.service.ts
├── hooks/
│   └── useQRScanner.ts
└── types/
    └── attendance.types.ts
```

**Frontend Tasks:**
- [ ] Install react-qr-reader package
- [ ] Create QRScanner component with camera access
- [ ] Create ClockStatus showing today's clock in/out
- [ ] Create AttendanceCalendar with color-coded days
- [ ] Create AttendanceList for detailed records
- [ ] Create AttendanceSummary with monthly stats
- [ ] Create ScanSuccessModal with timestamp feedback
- [ ] Handle camera permissions gracefully

---

# PHASE 4: Leave Management
**Duration: 3-4 days**

## 4.1 Leave Requests

### Backend Files
```
employee_portal/views/leave_views.py
employee_portal/serializers/leave_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/leave/balances/` | Employee leave balances |
| GET | `/api/portal/leave/requests/` | My leave requests |
| POST | `/api/portal/leave/requests/` | Submit new request |
| DELETE | `/api/portal/leave/requests/{id}/` | Cancel pending request |
| GET | `/api/portal/leave/types/` | Available leave types |

**Backend Tasks:**
- [ ] Create EmployeeLeaveBalanceView (filter by current user)
- [ ] Create EmployeeLeaveRequestViewSet (CRUD for own requests)
- [ ] Add validation (sufficient balance, date conflicts)
- [ ] Send notification on submission

### Frontend Files
```
src/
├── pages/
│   └── LeavePage.tsx
├── components/
│   └── leave/
│       ├── LeaveBalances.tsx      # Balance cards by type
│       ├── LeaveRequestForm.tsx   # New request form
│       ├── LeaveRequestsList.tsx  # My requests list
│       ├── LeaveRequestCard.tsx   # Single request card
│       ├── LeaveCalendar.tsx      # Calendar with leave dates
│       └── CancelRequestModal.tsx
├── services/
│   └── leave.service.ts
└── types/
    └── leave.types.ts
```

**Frontend Tasks:**
- [ ] Create LeavePage with tabs (Balances, Requests, Calendar)
- [ ] Create LeaveBalances with visual progress bars
- [ ] Create LeaveRequestForm with date picker + type selector
- [ ] Create LeaveRequestsList with status filters
- [ ] Create LeaveRequestCard with status badge
- [ ] Create LeaveCalendar showing approved/pending leaves
- [ ] Add cancel functionality for pending requests

---

# PHASE 5: Payslips
**Duration: 2-3 days**

## 5.1 Payslip Access

### Backend Files
```
employee_portal/views/payslip_views.py
employee_portal/serializers/payslip_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/payslips/` | List employee payslips |
| GET | `/api/portal/payslips/{id}/` | Payslip details |
| GET | `/api/portal/payslips/{id}/pdf/` | Download PDF |

**Backend Tasks:**
- [ ] Create EmployeePayslipViewSet (filter by current user)
- [ ] Create PayslipPDFView (generate/return PDF)
- [ ] Add date range filtering

### Frontend Files
```
src/
├── pages/
│   └── PayslipsPage.tsx
├── components/
│   └── payslips/
│       ├── PayslipsList.tsx       # List of payslips
│       ├── PayslipCard.tsx        # Summary card
│       ├── PayslipDetail.tsx      # Full payslip view
│       ├── PayslipFilters.tsx     # Year/month filters
│       └── DownloadButton.tsx     # PDF download
├── services/
│   └── payslip.service.ts
└── types/
    └── payslip.types.ts
```

**Frontend Tasks:**
- [ ] Create PayslipsPage with year filter
- [ ] Create PayslipsList showing monthly payslips
- [ ] Create PayslipCard with gross/net summary
- [ ] Create PayslipDetail with full breakdown
- [ ] Implement PDF download functionality

---

# PHASE 6: Expense Claims
**Duration: 3-4 days**

## 6.1 Expense Management

### Backend Files
```
employee_portal/models.py           # Add ExpenseClaim model
employee_portal/views/expense_views.py
employee_portal/serializers/expense_serializers.py
```

**New Model: ExpenseClaim**
```python
class ExpenseClaim(models.Model):
    employee = ForeignKey(Employees)
    category = CharField(choices=[...])
    amount = DecimalField()
    currency = CharField()
    description = TextField()
    receipt = FileField()
    date_incurred = DateField()
    status = CharField()  # Draft, Submitted, Approved, Rejected, Paid
    submitted_on = DateTimeField()
    reviewed_by = ForeignKey(Employees, null=True)
    review_date = DateTimeField(null=True)
    review_notes = TextField(blank=True)
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/expenses/` | My expense claims |
| POST | `/api/portal/expenses/` | Submit new claim |
| GET | `/api/portal/expenses/{id}/` | Claim details |
| PATCH | `/api/portal/expenses/{id}/` | Update draft claim |
| DELETE | `/api/portal/expenses/{id}/` | Delete draft claim |
| GET | `/api/portal/expenses/categories/` | Expense categories |

**Backend Tasks:**
- [ ] Create ExpenseClaim model
- [ ] Run migrations
- [ ] Create ExpenseClaimSerializer with receipt upload
- [ ] Create ExpenseClaimViewSet (CRUD for own claims)
- [ ] Create expense categories list endpoint

### Frontend Files
```
src/
├── pages/
│   └── ExpensesPage.tsx
├── components/
│   └── expenses/
│       ├── ExpensesList.tsx       # List of claims
│       ├── ExpenseCard.tsx        # Claim summary card
│       ├── ExpenseForm.tsx        # New/edit claim form
│       ├── ExpenseDetail.tsx      # Full claim view
│       ├── ReceiptUpload.tsx      # Image/PDF upload
│       └── ExpenseFilters.tsx     # Status/date filters
├── services/
│   └── expense.service.ts
└── types/
    └── expense.types.ts
```

**Frontend Tasks:**
- [ ] Create ExpensesPage with tabs (All, Pending, Approved)
- [ ] Create ExpensesList with status badges
- [ ] Create ExpenseForm with category dropdown
- [ ] Create ReceiptUpload with image preview
- [ ] Create ExpenseDetail with receipt viewer
- [ ] Add draft save functionality

---

# PHASE 7: Support Tickets
**Duration: 3-4 days**

## 7.1 IT/HR Ticket System

### Backend Files
```
employee_portal/models.py           # Add SupportTicket, TicketMessage
employee_portal/views/ticket_views.py
employee_portal/serializers/ticket_serializers.py
```

**New Models:**
```python
class SupportTicket(models.Model):
    employee = ForeignKey(Employees)
    category = CharField()  # IT, HR, Facilities, Other
    priority = CharField()  # Low, Medium, High
    subject = CharField()
    description = TextField()
    status = CharField()    # Open, In Progress, Resolved, Closed
    created_at = DateTimeField()
    updated_at = DateTimeField()
    assigned_to = ForeignKey(Employees, null=True)

class TicketMessage(models.Model):
    ticket = ForeignKey(SupportTicket)
    sender = ForeignKey(Employees)
    message = TextField()
    attachment = FileField(null=True)
    created_at = DateTimeField()
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/tickets/` | My tickets |
| POST | `/api/portal/tickets/` | Create new ticket |
| GET | `/api/portal/tickets/{id}/` | Ticket details |
| POST | `/api/portal/tickets/{id}/messages/` | Add message |
| PATCH | `/api/portal/tickets/{id}/close/` | Close ticket |

**Backend Tasks:**
- [ ] Create SupportTicket and TicketMessage models
- [ ] Run migrations
- [ ] Create TicketSerializer with nested messages
- [ ] Create TicketViewSet (CRUD + messaging)
- [ ] Add notification on ticket updates

### Frontend Files
```
src/
├── pages/
│   └── TicketsPage.tsx
├── components/
│   └── tickets/
│       ├── TicketsList.tsx        # List of tickets
│       ├── TicketCard.tsx         # Ticket summary
│       ├── TicketForm.tsx         # New ticket form
│       ├── TicketDetail.tsx       # Full ticket view
│       ├── TicketThread.tsx       # Message conversation
│       ├── MessageInput.tsx       # Reply input
│       └── TicketFilters.tsx      # Status/category filters
├── services/
│   └── ticket.service.ts
└── types/
    └── ticket.types.ts
```

**Frontend Tasks:**
- [ ] Create TicketsPage with status tabs
- [ ] Create TicketsList with priority indicators
- [ ] Create TicketForm with category + priority
- [ ] Create TicketDetail with conversation thread
- [ ] Create MessageInput with attachment support
- [ ] Implement real-time updates (polling or WebSocket)

---

# PHASE 8: Company Resources
**Duration: 2-3 days**

## 8.1 Documents & Calendar

### Backend Files
```
employee_portal/views/resource_views.py
employee_portal/serializers/resource_serializers.py
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/documents/` | Company documents |
| GET | `/api/portal/documents/{id}/download/` | Download document |
| GET | `/api/portal/calendar/` | Company calendar events |
| GET | `/api/portal/announcements/` | Company announcements |
| GET | `/api/portal/directory/` | Employee directory |

**Backend Tasks:**
- [ ] Create CompanyDocumentViewSet (read-only for employees)
- [ ] Create EmployeeDirectoryView (basic info only)
- [ ] Filter calendar events (public only)
- [ ] Filter announcements (published only)

### Frontend Files
```
src/
├── pages/
│   ├── DocumentsPage.tsx
│   ├── CalendarPage.tsx
│   └── DirectoryPage.tsx
├── components/
│   └── resources/
│       ├── DocumentsList.tsx      # Document categories
│       ├── DocumentCard.tsx       # Single document
│       ├── CalendarView.tsx       # Month calendar
│       ├── EventsList.tsx         # Upcoming events
│       ├── AnnouncementCard.tsx   # Announcement display
│       ├── DirectorySearch.tsx    # Employee search
│       └── EmployeeCard.tsx       # Directory entry
├── services/
│   └── resource.service.ts
└── types/
    └── resource.types.ts
```

**Frontend Tasks:**
- [ ] Create DocumentsPage with categories
- [ ] Create CalendarPage with month view
- [ ] Create DirectoryPage with search
- [ ] Implement document download
- [ ] Create responsive card layouts

---

# PHASE 9: Polish & Testing
**Duration: 3-4 days**

## 9.1 UI/UX Polish

**Tasks:**
- [ ] Loading states and skeletons
- [ ] Error boundaries and fallbacks
- [ ] Empty states with illustrations
- [ ] Toast notifications (success/error)
- [ ] Form validation messages
- [ ] Accessibility improvements (ARIA labels)
- [ ] Keyboard navigation support

## 9.2 Mobile Optimization

**Tasks:**
- [ ] Test all pages on mobile viewports
- [ ] Optimize touch targets (min 44px)
- [ ] Implement pull-to-refresh
- [ ] Add swipe gestures where needed
- [ ] Test bottom navigation usability
- [ ] Optimize images for mobile

## 9.3 Testing

**Tasks:**
- [ ] Unit tests for services
- [ ] Component tests with React Testing Library
- [ ] API endpoint tests (Django)
- [ ] Integration tests for key flows
- [ ] Cross-browser testing
- [ ] Mobile device testing

## 9.4 Deployment Preparation

**Tasks:**
- [ ] Environment configuration
- [ ] Build optimization
- [ ] API URL configuration
- [ ] Error tracking setup (Sentry)
- [ ] Analytics setup (optional)
- [ ] Documentation

---

# Summary

| Phase | Description | Duration | Priority |
|-------|-------------|----------|----------|
| 1 | Foundation & Auth | 3-4 days | Critical |
| 2 | Dashboard & Profile | 3-4 days | Critical |
| 3 | Attendance (QR) | 4-5 days | Critical |
| 4 | Leave Management | 3-4 days | Critical |
| 5 | Payslips | 2-3 days | High |
| 6 | Expense Claims | 3-4 days | High |
| 7 | Support Tickets | 3-4 days | Medium |
| 8 | Company Resources | 2-3 days | Medium |
| 9 | Polish & Testing | 3-4 days | High |

**Total Estimated Duration: 27-35 days**

---

# File Count Summary

**Frontend (React):**
- Pages: 9 files
- Components: ~45 files
- Services: 8 files
- Hooks: 5 files
- Types: 9 files
- Contexts: 2 files
- **Total: ~78 files**

**Backend (Django):**
- Views: 8 files
- Serializers: 8 files
- Models: 2 new models
- URLs: 1 file
- Utils: 2 files
- **Total: ~21 files**

---

# Getting Started

To begin implementation, start with Phase 1:

```bash
# Frontend
npm create vite@latest employee-portal -- --template react-ts
cd employee-portal
npm install

# Backend
cd erp_project
python manage.py startapp employee_portal
```

Ready to proceed with Phase 1?
