// src/types/index.ts

export type UserRole = 'ADMIN' | 'HR' | 'FINANCE' | 'MANAGER' | 'EMPLOYEE';

export interface Department {
  id: number;
  name: string;
  code: string;
  created_at: string;
}

export interface User {
  id: string; // UUID from Django
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  department: number | null; // The ID
  department_name?: string;  // Flattened from serializer
  // REM-07: signed in with a temporary password that must be replaced first
  must_change_password?: boolean;

  // This matches your LoginPage logic for user.employee_profile.role
  employee_profile?: {
    role: UserRole;
    department: string;
    employee_id: string;
    date_joined: string;
  };
}

// GET /auth/users/me/access/: what the signed-in user may do (INT-01 §2)
export interface MeAccess {
  role: string | null;
  permissions: string[]; // e.g. "procurement.purchase_request.view", or "*"
  is_department_head: boolean;
  headed_department_ids: number[];
  active_modules: string[];
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}