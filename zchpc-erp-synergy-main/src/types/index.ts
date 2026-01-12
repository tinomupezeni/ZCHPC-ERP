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
  
  // This matches your LoginPage logic for user.employee_profile.role
  employee_profile?: {
    role: UserRole;
    department: string;
    employee_id: string;
    date_joined: string;
  };
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}