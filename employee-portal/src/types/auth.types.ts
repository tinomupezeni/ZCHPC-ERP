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

export interface TokenRefreshResponse {
  access: string;
}

export interface AuthState {
  employee: Employee | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
}
