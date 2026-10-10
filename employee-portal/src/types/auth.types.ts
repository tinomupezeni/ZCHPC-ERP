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
  /** REM-07: the account holds a temporary password that must be replaced. */
  must_change_password?: boolean;
}

/** GET /auth/users/me/access/: the caller's role and what it may do. */
export interface MeAccess {
  role: string | null;
  permissions: string[];
  is_department_head: boolean;
  headed_department_ids: number[];
  active_modules: string[];
}

export interface LoginCredentials {
  ec_number: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  employee: Employee;
  must_change_password: boolean;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  detail: string;
  must_change_password: boolean;
  access: string;
  refresh: string;
}

export interface TokenRefreshResponse {
  access: string;
}

export interface AuthState {
  employee: Employee | null;
  /** null until loaded, while a temporary password is held, or on failure. */
  access: MeAccess | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
  changePassword: (request: ChangePasswordRequest) => Promise<void>;
}
