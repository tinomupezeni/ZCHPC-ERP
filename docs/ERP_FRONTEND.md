# ERP Admin Frontend Documentation

This document covers the main ERP admin dashboard built with React and TypeScript.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Technology Stack](#technology-stack)
3. [Routing & Navigation](#routing--navigation)
4. [State Management](#state-management)
5. [Components by Module](#components-by-module)
6. [Services & API Integration](#services--api-integration)
7. [Authentication Flow](#authentication-flow)
8. [Types & Interfaces](#types--interfaces)
9. [Custom Hooks](#custom-hooks)
10. [Adding New Features](#adding-new-features)

---

## Project Structure

```
zchpc-erp-synergy-main/
├── src/
│   ├── pages/                      # Route-level components
│   │   ├── LoginPage.tsx
│   │   ├── Dashboard.tsx
│   │   ├── HRPage.tsx
│   │   ├── PayrollPage.tsx
│   │   ├── AccountingPage.tsx
│   │   ├── ProcurementPage.tsx
│   │   ├── InventoryPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── components/                 # Feature components
│   │   ├── ui/                    # Shadcn/ui components (50+)
│   │   ├── HR/                    # Human Resources
│   │   │   ├── employees/         # Employee management
│   │   │   ├── recruitment/       # Job postings & applications
│   │   │   ├── training_development/
│   │   │   └── reports/           # HR reports
│   │   ├── Payroll/               # Payroll processing
│   │   ├── Accounting/            # Financial management
│   │   ├── Procurement/           # Purchase management
│   │   └── System/                # System configuration
│   │
│   ├── contexts/                   # React Context providers
│   │   └── AuthContext.tsx
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useLogin.ts
│   │   ├── useAddEmployee.ts
│   │   ├── usePostJob.ts
│   │   └── useEmployeeDetail.ts
│   │
│   ├── services/                   # API integration
│   │   ├── apiClient.ts           # Axios instance
│   │   ├── auth.services.tsx
│   │   ├── employees.services.tsx
│   │   ├── hr.services.tsx
│   │   ├── jobs.services.ts
│   │   ├── payroll.services.tsx
│   │   └── reports.services.tsx
│   │
│   ├── types/                      # TypeScript definitions
│   │   ├── index.ts
│   │   ├── auth.ts
│   │   ├── addEmployee.ts
│   │   └── postJob.ts
│   │
│   ├── layout/                     # Layout components
│   │   ├── MainLayout.tsx
│   │   ├── SidebarItem.tsx
│   │   └── navConfig.tsx
│   │
│   ├── lib/                        # Utilities
│   │   └── utils.ts               # cn() function, etc.
│   │
│   ├── App.tsx                     # Root component & routing
│   └── main.tsx                    # Entry point
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI Framework |
| TypeScript | 5.5.3 | Type Safety |
| Vite | 5.4.1 | Build Tool |
| React Router | 6.26.2 | Routing |
| React Query | 5.56.2 | Server State |
| Axios | 1.8.4 | HTTP Client |
| Tailwind CSS | 3.4.11 | Styling |
| Shadcn/ui | - | Component Library |
| Radix UI | - | Accessible Primitives |
| Lucide React | 0.462.0 | Icons |
| Recharts | 2.12.7 | Charts |
| React Hook Form | 7.53.0 | Form Handling |
| Sonner | 1.7.4 | Toast Notifications |

---

## Routing & Navigation

### Route Structure (App.tsx)

```tsx
<Routes>
  {/* Public */}
  <Route path="/" element={<Navigate to="/login" />} />
  <Route path="/login" element={<LoginPage />} />

  {/* Protected Routes */}
  <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/hr/*" element={<HRPage />} />
    <Route path="/payroll/*" element={<PayrollPage />} />
    <Route path="/accounting/*" element={<AccountingPage />} />
    <Route path="/procurement/*" element={<ProcurementPage />} />
    <Route path="/inventory/*" element={<InventoryPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Route>
</Routes>
```

### Navigation Configuration (navConfig.tsx)

```tsx
interface SidebarItemConfig {
  title: string;
  icon: React.ElementType;
  path: string;
  permission: string[];      // Required permissions
  subItems?: SidebarItemConfig[];
}

export const navItems: SidebarItemConfig[] = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    path: "/dashboard",
    permission: ["admin"]
  },
  {
    title: "HR",
    icon: Users,
    path: "/hr",
    permission: ["hr", "admin"],
    subItems: [
      { title: "Employees", path: "/hr/hr-employees", permission: ["hr"] },
      { title: "Attendance", path: "/hr/hr-attendance", permission: ["hr"] },
      { title: "Recruitment", path: "/hr/hr-recruitment", permission: ["hr"] },
      { title: "Leave", path: "/hr/hr-leave", permission: ["hr"] },
      { title: "Training", path: "/hr/hr-training", permission: ["hr"] },
      { title: "Reports", path: "/hr/hr-reports", permission: ["hr"] },
    ]
  },
  {
    title: "Payroll",
    icon: CreditCard,
    path: "/payroll",
    permission: ["accountant", "hr", "admin"],
    subItems: [
      { title: "Process Payroll", path: "/payroll/process", permission: ["accountant"] },
      { title: "Currency Rates", path: "/payroll/rates", permission: ["accountant"] },
      { title: "Deductions", path: "/payroll/deductions", permission: ["accountant"] },
    ]
  },
  // ... more items
];
```

### Permission Mapping

| Role | Accessible Modules |
|------|-------------------|
| admin | All modules |
| hr | HR, Employees |
| accountant | Payroll, Accounting |
| procurement | Procurement |
| sales | Sales |
| inventory | Inventory |
| manager | HR, Payroll (view) |

---

## State Management

### AuthContext (Primary Global State)

```tsx
// contexts/AuthContext.tsx

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login(email: string, password: string): Promise<User>;
  logout(): void;
  checkPermission(requiredModules: string[]): boolean;
}

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Permission checking
  const checkPermission = useCallback((requiredModules: string[]) => {
    if (!user) return false;

    // Staff/Superuser get all permissions
    if (user.is_staff || user.is_superuser) return true;

    // Admin role gets all permissions
    const role = user.employee_profile?.role || user.role;
    if (role === 'ADMIN' || role === 'SYSTEM_ADMINISTRATOR') return true;

    // Map role to permissions
    const rolePermissions = roleToPermissionMap[role] || [];
    const explicitPermissions = user.employee_profile?.role_permissions || [];
    const allPermissions = [...rolePermissions, ...explicitPermissions];

    return requiredModules.some(mod => allPermissions.includes(mod));
  }, [user]);

  // ... rest of implementation
};

// Usage
const { user, checkPermission } = useAuth();
if (checkPermission(['hr', 'admin'])) {
  // Show HR features
}
```

### Role to Permission Mapping

```tsx
const roleToPermissionMap: Record<string, string[]> = {
  'ADMIN': ['admin', 'hr', 'accountant', 'procurement', 'sales', 'inventory'],
  'SYSTEM_ADMINISTRATOR': ['admin', 'hr', 'accountant', 'procurement', 'sales', 'inventory'],
  'HUMAN_RESOURCES': ['hr'],
  'HR': ['hr'],
  'ACCOUNTANT': ['accountant'],
  'PROCUREMENT': ['procurement'],
  'PROCUREMENT_OFFICER': ['procurement'],
  'SALES': ['sales'],
  'SALES_REPRESENTATIVE': ['sales'],
  'MANAGER': ['hr', 'accountant'],
  'DEPARTMENT_MANAGER': ['hr', 'accountant'],
  'INVENTORY': ['inventory'],
};
```

### React Query Integration

```tsx
// App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      cacheTime: 10 * 60 * 1000,     // 10 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* App content */}
    </QueryClientProvider>
  );
}
```

---

## Components by Module

### HR Module Components

**Path:** `src/components/HR/`

| Component | Path | Description |
|-----------|------|-------------|
| `HrDashboard` | `HrDashboard.tsx` | HR metrics overview |
| `Employees` | `employees/Employees.tsx` | Employee list & management |
| `AddEmployee` | `employees/AddEmployee.tsx` | Employee creation form |
| `EmployeeDetailModal` | `employees/EmployeeDetailModal.tsx` | View/edit employee |
| `Recruitment` | `Recruitment.tsx` | Job postings management |
| `ListedJobs` | `recruitment/ListedJobs.tsx` | Job listings table |
| `PostJobModal` | `recruitment/PostJobModal.tsx` | Create/edit job posting |
| `Candidates` | `recruitment/Candidates.tsx` | Candidate management |
| `ApplicantsModal` | `recruitment/ApplicantsModal.tsx` | Application tracking |
| `Attendence` | `Attendence.tsx` | Attendance tracking |
| `LeaveApplications` | `LeaveApplications.tsx` | Leave request processing |
| `CompanyCalendar` | `CompanyCalendar.tsx` | Calendar view |
| `HrReports` | `HrReports.tsx` | Report generation |

**Report Components:**
- `BasicSalaryReport.tsx` - Salary distribution
- `AllowancesReport.tsx` - Benefits summary
- `DeductionsReport.tsx` - Deduction analysis
- `PAYEReport.tsx` - Tax withholding
- `NSSAReport.tsx` - Social security
- `LeaveBalanceReport.tsx` - Leave usage

### Payroll Module Components

**Path:** `src/components/Payroll/`

| Component | Description |
|-----------|-------------|
| `PayrollDashboard` | Payroll metrics & status |
| `ProcessPayroll` | Monthly payroll processing |
| `ProcessPayrollModal` | Payroll execution interface |
| `SalarySetup` | Employee salary configuration |
| `Deductions` | Allowance/deduction management |
| `CurrencyRates` | ZIG/USD exchange rates |
| `PayslipModal` | Payslip viewer |
| `PayrollStatusBadge` | Status indicator |
| `PayrollSummaryCard` | Summary statistics |

### Accounting Module Components

**Path:** `src/components/Accounting/`

| Component | Description |
|-----------|-------------|
| `AccountDashboard` | Accounting overview |
| `GeneralLedger` | Chart of accounts |
| `JournalEntries` | Journal entry recording |
| `Currencies` | Currency management |
| `AccountsPayable` | Vendor invoices |
| `AccountsReceivable` | Customer invoices |
| `ReportsDashboard` | Financial reports |
| `TaxManager` | Tax configuration |
| `PartnerManager` | Partner management |

### Procurement Module Components

**Path:** `src/components/Procurement/`

| Component | Description |
|-----------|-------------|
| `ProcurementDashboard` | Procurement metrics |
| `PurchaseOrders` | PO management |
| `Suppliers` | Vendor management |
| `PurchaseRequests` | PR handling |
| `BudgetCenters` | Budget allocation |
| `Deliveries` | Goods receipt |

---

## Services & API Integration

### API Client Configuration

```tsx
// services/apiClient.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/token/refresh/', {
            refresh: refreshToken,
          });
          localStorage.setItem('accessToken', response.data.access);
          // Retry original request
          return apiClient(error.config);
        } catch {
          // Refresh failed, logout
          window.dispatchEvent(new Event('logout'));
        }
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Service Pattern

```tsx
// services/employees.services.tsx
import apiClient from './apiClient';

export const employeeService = {
  async getAll() {
    const response = await apiClient.get('/hr/employees/');
    return response.data;
  },

  async getById(id: number) {
    const response = await apiClient.get(`/hr/employees/${id}/`);
    return response.data;
  },

  async create(data: EmployeeFormData) {
    const response = await apiClient.post('/hr/employees/', data);
    return response.data;
  },

  async update(id: number, data: Partial<EmployeeFormData>) {
    const response = await apiClient.patch(`/hr/employees/${id}/`, data);
    return response.data;
  },

  async delete(id: number) {
    await apiClient.delete(`/hr/employees/${id}/`);
  },
};
```

### Available Services

| Service | File | Endpoints |
|---------|------|-----------|
| `authService` | `auth.services.tsx` | Login, profile, users |
| `employeeService` | `employees.services.tsx` | Employee CRUD |
| `hrService` | `hr.services.tsx` | Departments, roles, positions |
| `jobsService` | `jobs.services.ts` | Job postings, applications |
| `payrollService` | `payroll.services.tsx` | Payroll processing |
| `reportsService` | `reports.services.tsx` | Report generation |
| `Server` | `Server.tsx` | Legacy API class |

---

## Authentication Flow

### Login Process

```tsx
// 1. User submits credentials
const handleLogin = async (email: string, password: string) => {
  const response = await authService.login(email, password);
  // Returns: { access, refresh, user }

  // 2. Store tokens
  localStorage.setItem('accessToken', response.access);
  localStorage.setItem('refreshToken', response.refresh);

  // 3. Update context
  setUser(response.user);

  // 4. Redirect based on role
  const role = response.user.employee_profile?.role?.toLowerCase();
  navigate(ROLE_ROUTES[role] || '/dashboard');
};
```

### Protected Route Component

```tsx
// components/ProtectedRoute.tsx
export const ProtectedRoute: React.FC<Props> = ({ children, requiredPermissions }) => {
  const { isAuthenticated, isLoading, checkPermission } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (requiredPermissions && !checkPermission(requiredPermissions)) {
    return <Navigate to="/dashboard" />;
  }

  return <>{children}</>;
};
```

---

## Types & Interfaces

### User Types

```tsx
// types/index.ts
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  role: string;
  department: number | null;
  employee_profile?: {
    employee_id: string;
    role: string;
    role_display_name: string;
    department: string;
    position: string;
    date_joined: string;
    role_permissions: string[];
  };
}

export interface Department {
  id: number;
  name: string;
  description: string;
}

export interface Position {
  id: number;
  title: string;
  department: number;
  description: string;
}
```

### Employee Form Types

```tsx
// types/addEmployee.ts
export interface EmployeeFormState {
  ecNumber: string;
  firstname: string;
  surname: string;
  nationalId: string;
  dob: string;
  gender: string;
  maritalStatus: string;
  email: string;
  phone: string;
  bankName: string;
  accountNumber: string;
  payFrequency: string;
  employeeType: string;
  leaveDays: number;
  pensionScheme: string;
  position: string;
  department: string;
  usd_salary: string;
  zig_salary: string;
  contractFrom: string;
  contractTo: string;
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelationship: string;
  selectedDeductions: Deduction[];
}

export interface Deduction {
  id: number;
  name: string;
  amount: number;
  currency: 'USD' | 'ZIG';
}
```

### Job Posting Types

```tsx
// types/postJob.ts
export interface JobListing {
  id?: number;
  title: string;
  department_id: string | number;
  position_id: string | number;
  status: string;
  postedDate: string;
  description: string;
  qualifications: string[];
  responsibilities: string[];
  competencies: string[];
  applicationProcess: string;
  location: string;
  salaryUsdMin?: number | null;
  salaryUsdMax?: number | null;
  salaryZigMin?: number | null;
  salaryZigMax?: number | null;
  contactEmail: string;
  reportsTo: string;
  isInternal: boolean;
}
```

---

## Custom Hooks

### useLogin

```tsx
// hooks/useLogin.ts
export const useLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [viewPassword, setViewPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const user = await login(email, password);
      const role = user.employee_profile?.role?.toLowerCase();
      navigate(ROLE_ROUTES[role] || '/dashboard');
    } catch (error) {
      toast.error('Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    email, setEmail,
    password, setPassword,
    viewPassword, setViewPassword,
    isSubmitting,
    handleLogin,
  };
};
```

### useAddEmployee

```tsx
// hooks/useAddEmployee.ts
export const useAddEmployee = () => {
  const [formData, setFormData] = useState<EmployeeFormState>(initialState);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [deductionTypes, setDeductionTypes] = useState<DeductionType[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load departments on mount
  useEffect(() => {
    loadDepartments();
    loadDeductionTypes();
  }, []);

  // Load positions when department changes
  useEffect(() => {
    if (formData.department) {
      loadPositions(formData.department);
    }
  }, [formData.department]);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await employeeService.create(transformFormData(formData));
      toast.success('Employee created');
      return true;
    } catch (error) {
      handleError(error);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    formData, setFormData,
    departments, positions, deductionTypes,
    isSubmitting,
    handleSubmit,
  };
};
```

### usePostJob

```tsx
// hooks/usePostJob.ts
export const usePostJob = (existingJob?: JobListing) => {
  const [job, setJob] = useState<JobListing>(existingJob || initialJobState);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);

  // Dynamic list management
  const addQualification = () => {
    setJob(prev => ({
      ...prev,
      qualifications: [...prev.qualifications, '']
    }));
  };

  const updateQualification = (index: number, value: string) => {
    setJob(prev => ({
      ...prev,
      qualifications: prev.qualifications.map((q, i) => i === index ? value : q)
    }));
  };

  const removeQualification = (index: number) => {
    setJob(prev => ({
      ...prev,
      qualifications: prev.qualifications.filter((_, i) => i !== index)
    }));
  };

  // Similar for responsibilities and competencies...

  const handleSubmit = async () => {
    if (existingJob?.id) {
      await jobsService.update(existingJob.id, job);
    } else {
      await jobsService.create(job);
    }
  };

  return {
    job, setJob,
    departments, positions,
    addQualification, updateQualification, removeQualification,
    handleSubmit,
  };
};
```

---

## Adding New Features

### Creating a New Page

1. Create page component in `src/pages/`:
```tsx
// src/pages/NewFeaturePage.tsx
export const NewFeaturePage: React.FC = () => {
  return <div>New Feature Content</div>;
};
```

2. Add route in `App.tsx`:
```tsx
<Route path="/new-feature" element={<NewFeaturePage />} />
```

3. Add navigation item in `navConfig.tsx`:
```tsx
{
  title: "New Feature",
  icon: SomeIcon,
  path: "/new-feature",
  permission: ["admin", "hr"],
}
```

### Creating a New Component

1. Create component file:
```tsx
// src/components/NewModule/NewComponent.tsx
interface NewComponentProps {
  data: DataType;
  onAction: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({ data, onAction }) => {
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
};
```

### Creating a New Service

```tsx
// src/services/newFeature.services.ts
import apiClient from './apiClient';

export const newFeatureService = {
  async getAll(): Promise<DataType[]> {
    const response = await apiClient.get('/new-feature/');
    return response.data;
  },

  async create(data: CreateDataType): Promise<DataType> {
    const response = await apiClient.post('/new-feature/', data);
    return response.data;
  },
};
```

### Creating a New Hook

```tsx
// src/hooks/useNewFeature.ts
export const useNewFeature = () => {
  const [data, setData] = useState<DataType[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const result = await newFeatureService.getAll();
      setData(result);
    } finally {
      setIsLoading(false);
    }
  };

  return { data, isLoading, refresh: loadData };
};
```

---

## UI Components

The project uses **Shadcn/ui** components. Available components in `src/components/ui/`:

- **Form:** Input, Textarea, Select, Checkbox, RadioGroup, Switch, Slider
- **Feedback:** Alert, Badge, Progress, Skeleton, Toast
- **Containers:** Card, Dialog, Sheet, Drawer, Popover, Tooltip
- **Navigation:** Tabs, Pagination, Breadcrumb, Command
- **Data Display:** Table, Accordion, Collapsible
- **Specialized:** Calendar, Chart, InputOTP

### Using Shadcn/ui

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Usage
<Card>
  <CardHeader>
    <CardTitle>Form Title</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      <div>
        <Label htmlFor="name">Name</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <Label>Department</Label>
        <Select value={dept} onValueChange={setDept}>
          <SelectTrigger>
            <SelectValue placeholder="Select..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">IT</SelectItem>
            <SelectItem value="2">HR</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button onClick={handleSubmit}>Submit</Button>
    </div>
  </CardContent>
</Card>
```
