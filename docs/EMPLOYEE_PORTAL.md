# Employee Portal Documentation

This document covers the Employee Self-Service Portal built with React and TypeScript.

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Routing & Navigation](#routing--navigation)
4. [Authentication](#authentication)
5. [Features by Module](#features-by-module)
6. [QR Attendance System](#qr-attendance-system)
7. [Services & API](#services--api)
8. [Types & Interfaces](#types--interfaces)
9. [Adding New Features](#adding-new-features)

---

## Overview

The Employee Portal is a self-service application allowing employees to:

- Clock in/out via QR code scanning
- View attendance history and summary
- Request leave and view balances
- Access payslips
- Apply for internal jobs
- View company documents

**URL:** http://localhost:5174

---

## Project Structure

```
employee-portal/
├── src/
│   ├── pages/                      # Route-level components
│   │   ├── DashboardPage.tsx       # Employee dashboard
│   │   ├── AttendancePage.tsx      # Clock in/out, QR scanning
│   │   ├── LeavePage.tsx           # Leave requests
│   │   ├── PayslipsPage.tsx        # Payslip viewing
│   │   ├── QRDisplayPage.tsx       # Office QR display
│   │   ├── JobsListPage.tsx        # Public job listings
│   │   ├── JobDetailPage.tsx       # Job details
│   │   ├── JobApplicationPage.tsx  # Application form
│   │   └── ApplicationStatusPage.tsx
│   │
│   ├── components/
│   │   ├── ui/                     # Shadcn/ui components
│   │   ├── layout/                 # Layout components
│   │   │   ├── MainLayout.tsx      # Protected layout
│   │   │   ├── PublicLayout.tsx    # Public pages layout
│   │   │   ├── Header.tsx          # Top header
│   │   │   ├── Sidebar.tsx         # Desktop sidebar
│   │   │   └── MobileNav.tsx       # Mobile bottom nav
│   │   ├── attendance/
│   │   │   ├── ClockStatus.tsx     # Clock in/out widget
│   │   │   ├── QRScanner.tsx       # QR scanning component
│   │   │   ├── AttendanceHistory.tsx
│   │   │   └── AttendanceSummaryCard.tsx
│   │   ├── leave/
│   │   │   ├── LeaveBalances.tsx
│   │   │   ├── LeaveRequestForm.tsx
│   │   │   └── LeaveRequestsList.tsx
│   │   ├── payslips/
│   │   │   ├── PayslipsList.tsx
│   │   │   └── PayslipDetail.tsx
│   │   ├── dashboard/
│   │   │   ├── WelcomeCard.tsx
│   │   │   ├── StatsCards.tsx
│   │   │   └── QuickActions.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── contexts/
│   │   └── AuthContext.tsx         # Authentication state
│   │
│   ├── services/
│   │   ├── api.ts                  # Axios instance
│   │   ├── auth.service.ts
│   │   ├── attendance.service.ts
│   │   ├── leave.service.ts
│   │   ├── payslip.service.ts
│   │   └── jobs.service.ts
│   │
│   ├── types/
│   │   ├── auth.types.ts
│   │   ├── attendance.types.ts
│   │   ├── leave.types.ts
│   │   ├── payslip.types.ts
│   │   └── jobs.types.ts
│   │
│   ├── App.tsx
│   └── main.tsx
│
├── package.json
└── vite.config.ts
```

---

## Routing & Navigation

### Route Structure (App.tsx)

```tsx
<Routes>
  {/* QR Display - standalone, no layout */}
  <Route path="/attendance/qr-display" element={<QRDisplayPage />} />

  {/* Public Routes - careers & job applications */}
  <Route element={<PublicLayout />}>
    <Route path="/" element={<Navigate to="/careers" replace />} />
    <Route path="/careers" element={<JobsListPage />} />
    <Route path="/careers/status" element={<ApplicationStatusPage />} />
    <Route path="/careers/:id" element={<JobDetailPage />} />
    <Route path="/careers/:id/apply" element={<JobApplicationPage />} />
  </Route>

  {/* Login redirect */}
  <Route path="/login" element={<Navigate to="/careers" replace />} />

  {/* Protected Routes - employee portal */}
  <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
    <Route path="/portal" element={<DashboardPage />} />
    <Route path="/portal/attendance" element={<AttendancePage />} />
    <Route path="/portal/leave" element={<LeavePage />} />
    <Route path="/portal/payslips" element={<PayslipsPage />} />
  </Route>

  {/* Catch all */}
  <Route path="*" element={<Navigate to="/careers" replace />} />
</Routes>
```

### Navigation Items (Sidebar.tsx)

```tsx
const navItems = [
  { path: '/portal', label: 'Dashboard', icon: Home, description: 'Overview & stats' },
  { path: '/portal/attendance', label: 'Attendance', icon: Clock, description: 'Clock in/out' },
  { path: '/portal/leave', label: 'Leave', icon: CalendarDays, description: 'Request time off' },
  { path: '/portal/payslips', label: 'Payslips', icon: FileText, description: 'View earnings' },
];
```

---

## Authentication

### AuthContext

```tsx
// contexts/AuthContext.tsx

interface AuthContextType {
  employee: Employee | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login(credentials: LoginCredentials): Promise<void>;
  logout(): void;
}

export const AuthProvider: React.FC = ({ children }) => {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing tokens on mount
  useEffect(() => {
    const storedAccess = localStorage.getItem('portal_access_token');
    const storedRefresh = localStorage.getItem('portal_refresh_token');
    if (storedAccess && storedRefresh) {
      setAccessToken(storedAccess);
      setRefreshToken(storedRefresh);
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const response = await authService.login(credentials);
    localStorage.setItem('portal_access_token', response.access);
    localStorage.setItem('portal_refresh_token', response.refresh);
    setAccessToken(response.access);
    setRefreshToken(response.refresh);
    setEmployee(response.employee);
  };

  const logout = () => {
    localStorage.removeItem('portal_access_token');
    localStorage.removeItem('portal_refresh_token');
    setAccessToken(null);
    setRefreshToken(null);
    setEmployee(null);
  };

  // ...
};
```

### Login Flow

The portal uses an embedded login panel in the PublicLayout header:

1. User visits `/careers` (default landing page)
2. Clicks "Employee Login" button in header
3. Login panel slides down with EC number and password fields
4. On success, redirected to `/portal` (dashboard)

### Token Storage

- `portal_access_token` - JWT access token (24 hour expiry)
- `portal_refresh_token` - JWT refresh token (30 day expiry)

---

## Features by Module

### Dashboard

**Page:** `DashboardPage.tsx`

**Components:**
- `WelcomeCard` - Greeting with employee name, initials avatar
- `StatsCards` - Leave balance, days present, pending requests
- `QuickActions` - Clock In, Request Leave, View Payslip shortcuts

### Attendance

**Page:** `AttendancePage.tsx`

**Components:**
- `ClockStatus` - Current time, status (clocked in/out/not clocked), manual clock button
- `QRScanner` - Camera-based QR code scanning for clock in/out
- `AttendanceSummaryCard` - Monthly stats (days present, absent, on leave, hours worked)
- `AttendanceHistory` - Recent attendance records list

**Layout:**
```tsx
<div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
  <ClockStatus />           {/* Manual clock */}
  <QRScanner />            {/* QR code clock */}
  <AttendanceSummaryCard /> {/* Monthly summary */}
  <AttendanceHistory />     {/* Recent records */}
</div>
```

### Leave

**Page:** `LeavePage.tsx`

**Components:**
- `LeaveBalances` - Leave type balances with progress bars
- `LeaveRequestForm` - New request form with date picker
- `LeaveRequestsList` - Request history with status badges

**Features:**
- View balances by leave type
- Submit new leave requests
- Cancel pending requests
- Filter requests by status

### Payslips

**Page:** `PayslipsPage.tsx`

**Components:**
- `PayslipsList` - Grid of payslips by month
- `PayslipDetail` - Full payslip breakdown (modal/sheet)

**Features:**
- Year filter
- View earnings breakdown (base salary, allowances, gross)
- View deductions breakdown (PAYE, AIDS levy, NSSA, other)
- Download payslip as PDF

### Careers (Public)

**Pages:**
- `JobsListPage` - Browse open positions
- `JobDetailPage` - Full job description
- `JobApplicationPage` - Application form with resume upload
- `ApplicationStatusPage` - Check status by ID number

---

## QR Attendance System

The QR attendance system prevents fraud by using rotating QR codes that expire every 30 seconds.

### Architecture

```
+-------------------+          +-------------------+
| Office Display    |          | Employee Phone    |
| (QR Display Page) |          | (Portal App)      |
+-------------------+          +-------------------+
        |                              |
        | GET /qr/token/               | POST /qr/clock-in/
        | (every 25s)                  | (with scanned token)
        v                              v
+--------------------------------------------------+
|                  Django Backend                   |
|  - Generate rotating tokens (30s validity)        |
|  - Verify token on clock-in                       |
|  - Create attendance record                       |
+--------------------------------------------------+
```

### QR Display Page

**Path:** `/attendance/qr-display`
**File:** `src/pages/QRDisplayPage.tsx`

This page is displayed on an office tablet/kiosk for employees to scan.

**Features:**
- Large QR code (256x256px) centered on screen
- Current time display (HH:MM:SS)
- Circular progress indicator showing time until refresh
- Color-coded timer (green > 10s, yellow 5-10s, red < 5s)
- Instructions for scanning

```tsx
// Token fetching logic
const fetchToken = useCallback(async () => {
  const data = await attendanceService.getQRToken();
  setToken(data);
  setTimeRemaining(data.time_remaining);
}, []);

// Fetch every 25 seconds (before 30s expiry)
useEffect(() => {
  fetchToken();
  const interval = setInterval(fetchToken, 25000);
  return () => clearInterval(interval);
}, [fetchToken]);

// Countdown display
useEffect(() => {
  const interval = setInterval(() => {
    setCurrentTime(new Date());
    setTimeRemaining(prev => Math.max(0, prev - 1));
  }, 1000);
  return () => clearInterval(interval);
}, []);
```

### QR Scanner Component

**File:** `src/components/attendance/QRScanner.tsx`

Uses `html5-qrcode` library for camera-based scanning.

```tsx
import { Html5QrcodeScanner, Html5QrcodeScanType } from 'html5-qrcode';

// Scanner initialization
const scanner = new Html5QrcodeScanner(
  'qr-reader',
  {
    fps: 10,
    qrbox: { width: 250, height: 250 },
    aspectRatio: 1,
    supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA],
    rememberLastUsedCamera: true,
  },
  false
);

// Render scanner with callbacks
scanner.render(
  async (decodedText) => {
    // Success - token scanned
    await scanner.clear();
    const response = await attendanceService.qrClockIn(decodedText);
    toast.success(response.message);
    onSuccess(); // Refresh attendance data
  },
  (errorMessage) => {
    // Ignore - continuous scanning attempts
    console.debug('QR scan error:', errorMessage);
  }
);
```

**States:**
- `idle` - Scanner not open
- `scanning` - Camera active, looking for QR
- `processing` - Token found, verifying with backend
- `success` - Clock in successful
- `error` - Token invalid/expired, retry in 3s

### Backend Endpoints

```
GET /api/portal/attendance/qr/token/
Response: {
  token: string,        // 32-char random token
  expires_at: string,   // ISO datetime
  time_remaining: number, // Seconds until expiry
  validity_seconds: number // Always 30
}

POST /api/portal/attendance/qr/clock-in/
Request: { token: string }
Response: {
  action: 'clock_in' | 'clock_out',
  message: string,
  date: string,
  clock_in: string | null,
  clock_out: string | null,
  hours_worked: number | null
}
```

### Security Features

1. **Token Rotation** - Tokens expire after 30 seconds
2. **Cryptographic Tokens** - 32-character random alphanumeric
3. **Usage Tracking** - Backend tracks how many times each token is used
4. **Deactivation** - Old tokens are deactivated when new ones are created
5. **Physical Presence Required** - Must be at office to scan current code

---

## Services & API

### API Client Configuration

```tsx
// services/api.ts
import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      try {
        const refresh = localStorage.getItem('portal_refresh_token');
        const response = await axios.post(`${baseURL}/portal/auth/refresh/`, {
          refresh,
        });
        localStorage.setItem('portal_access_token', response.data.access);
        error.config.headers.Authorization = `Bearer ${response.data.access}`;
        return api(error.config);
      } catch {
        window.location.href = '/careers';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Attendance Service

```tsx
// services/attendance.service.ts

export const attendanceService = {
  // Manual clock in/out
  async clock(): Promise<ClockResponse> {
    const response = await api.post('/portal/attendance/clock/');
    return response.data;
  },

  // Get current QR token (public, no auth)
  async getQRToken(): Promise<QRTokenResponse> {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
    const response = await axios.get(`${baseUrl}/portal/attendance/qr/token/`);
    return response.data;
  },

  // Clock in via QR code
  async qrClockIn(token: string): Promise<ClockResponse> {
    const response = await api.post('/portal/attendance/qr/clock-in/', { token });
    return response.data;
  },

  // Get today's status
  async getStatus(): Promise<AttendanceStatus> {
    const response = await api.get('/portal/attendance/status/');
    return response.data;
  },

  // Get attendance history
  async getHistory(params?: HistoryParams): Promise<AttendanceHistory> {
    const response = await api.get('/portal/attendance/history/', { params });
    return response.data;
  },

  // Get monthly summary
  async getSummary(params?: SummaryParams): Promise<AttendanceSummary> {
    const response = await api.get('/portal/attendance/summary/', { params });
    return response.data;
  },
};
```

### Leave Service

```tsx
// services/leave.service.ts

export const leaveService = {
  async getTypes(): Promise<LeaveType[]> {
    const response = await api.get('/portal/leave/types/');
    return response.data;
  },

  async getBalances(): Promise<LeaveBalance[]> {
    const response = await api.get('/portal/leave/balances/');
    return response.data;
  },

  async getRequests(params?: RequestParams): Promise<LeaveRequest[]> {
    const response = await api.get('/portal/leave/requests/', { params });
    return response.data;
  },

  async createRequest(data: LeaveRequestData): Promise<LeaveRequest> {
    const response = await api.post('/portal/leave/requests/', data);
    return response.data;
  },

  async cancelRequest(id: number): Promise<void> {
    await api.post(`/portal/leave/requests/${id}/cancel/`);
  },
};
```

### Payslip Service

```tsx
// services/payslip.service.ts

export const payslipService = {
  async getList(params?: ListParams): Promise<PayslipListItem[]> {
    const response = await api.get('/portal/payslips/', { params });
    return response.data;
  },

  async getDetail(id: number): Promise<PayslipDetail> {
    const response = await api.get(`/portal/payslips/${id}/`);
    return response.data;
  },

  async download(id: number): Promise<Blob> {
    const response = await api.get(`/portal/payslips/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async getSummary(year?: number): Promise<YearSummary> {
    const response = await api.get('/portal/payslips/summary/', {
      params: { year },
    });
    return response.data;
  },
};
```

### Jobs Service (Public)

```tsx
// services/jobs.service.ts

// Uses public axios instance (no auth required)
const publicApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const jobsService = {
  async getJobs(): Promise<Job[]> {
    const response = await publicApi.get('/portal/public/jobs/');
    return response.data;
  },

  async getJob(id: number): Promise<Job> {
    const response = await publicApi.get(`/portal/public/jobs/${id}/`);
    return response.data;
  },

  async checkApplication(idNumber: string, jobId: number): Promise<boolean> {
    const response = await publicApi.post('/portal/public/jobs/check-application/', {
      id_number: idNumber,
      job_id: jobId,
    });
    return response.data.has_applied;
  },

  async submitApplication(data: FormData): Promise<Application> {
    const response = await publicApi.post('/portal/public/jobs/apply/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getApplicationStatus(idNumber: string): Promise<ApplicationStatus[]> {
    const response = await publicApi.post('/portal/public/applications/status/', {
      id_number: idNumber,
    });
    return response.data;
  },
};
```

---

## Types & Interfaces

### Authentication Types

```tsx
// types/auth.types.ts

export interface Employee {
  id: number;
  employee_id: string;
  first_name: string;
  surname: string;
  full_name: string;
  email: string;
  phone: string;
  gender: string;
  date_of_birth: string | null;
  date_joined: string;
  department_name: string | null;
  position_title: string | null;
  role_name: string | null;
  role_display_name: string | null;
  employee_type: string;
  is_active: boolean;
  leave_days_entitled: number;
}

export interface LoginCredentials {
  ec_number: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  employee: Employee;
}
```

### Attendance Types

```tsx
// types/attendance.types.ts

export interface AttendanceStatus {
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: 'not_clocked' | 'clocked_in' | 'clocked_out';
  hours_worked: number | null;
}

export interface AttendanceRecord {
  id: number;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: 'complete' | 'clocked_in' | 'absent';
}

export interface AttendanceSummary {
  month: number;
  year: number;
  total_working_days: number;
  days_present: number;
  days_absent: number;
  days_late: number;
  days_on_leave: number;
  total_hours_worked: number;
  average_clock_in: string | null;
  average_clock_out: string | null;
}

export interface ClockResponse {
  action: 'clock_in' | 'clock_out';
  message: string;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  hours_worked: number | null;
}

export interface QRTokenResponse {
  token: string;
  expires_at: string;
  time_remaining: number;
  validity_seconds: number;
}
```

### Leave Types

```tsx
// types/leave.types.ts

export interface LeaveType {
  id: number;
  name: string;
  default_days_allowed: number;
}

export interface LeaveBalance {
  id: number;
  leave_type: number;
  leave_type_name: string;
  year: number;
  days_allowed: number;
  days_remaining: number;
  days_used: number;
  percentage_used: number;
}

export interface LeaveRequest {
  id: number;
  leave_type: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  reason: string;
  status: 'Pending' | 'Approved' | 'Rejected' | 'Cancelled';
  requested_on: string;
  reviewed_by_name: string | null;
  review_date: string | null;
  can_cancel: boolean;
}
```

### Payslip Types

```tsx
// types/payslip.types.ts

export interface PayslipListItem {
  id: number;
  period: string;
  period_display: string;
  month: number;
  year: number;
  status: 'Draft' | 'Pending' | 'Processed' | 'Failed' | 'Paid';
  base_salary_usd: number;
  net_salary_usd: number;
  base_salary_zig: number;
  net_salary_zig: number;
  exchange_rate: number;
}

export interface PayslipDetail {
  id: number;
  period: string;
  period_display: string;
  employee_name: string;
  employee_id: string;
  department: string;
  position: string;
  exchange_rate: number;
  earnings: {
    base_salary: { usd: number; zig: number };
    allowances: { usd: number; zig: number };
    gross: { usd: number; zig: number };
  };
  deductions: {
    paye: { usd: number; zig: number };
    aids_levy: { usd: number; zig: number };
    nssa_employee: { usd: number; zig: number };
    other_deductions: { usd: number; zig: number };
    total: { usd: number; zig: number };
  };
  summary: {
    gross_salary: { usd: number; zig: number };
    total_deductions: { usd: number; zig: number };
    net_salary: { usd: number; zig: number };
  };
}
```

---

## Adding New Features

### Creating a New Page

1. Create page component:
```tsx
// src/pages/NewPage.tsx
import { PageHeader } from '@/components/layout';

export function NewPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="New Feature"
        description="Feature description"
      />
      {/* Page content */}
    </div>
  );
}

export default NewPage;
```

2. Add route in `App.tsx`:
```tsx
<Route path="/portal/new-feature" element={<NewPage />} />
```

3. Add to navigation in `Sidebar.tsx`:
```tsx
const navItems = [
  // ... existing items
  { path: '/portal/new-feature', label: 'New Feature', icon: NewIcon, description: 'Description' },
];
```

### Creating a New Service

```tsx
// src/services/newFeature.service.ts
import api from './api';

export interface NewFeatureData {
  // Define interface
}

export const newFeatureService = {
  async getAll(): Promise<NewFeatureData[]> {
    const response = await api.get('/portal/new-feature/');
    return response.data;
  },

  async create(data: NewFeatureData): Promise<NewFeatureData> {
    const response = await api.post('/portal/new-feature/', data);
    return response.data;
  },
};
```

### Creating a New Component

```tsx
// src/components/newFeature/NewComponent.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface NewComponentProps {
  data: DataType;
}

export function NewComponent({ data }: NewComponentProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  );
}

export default NewComponent;
```

Don't forget to export from index:
```tsx
// src/components/newFeature/index.ts
export { NewComponent } from './NewComponent';
```
