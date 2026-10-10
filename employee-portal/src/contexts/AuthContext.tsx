import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { isAxiosError } from 'axios';
import { authService } from '@/services/auth.service';
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from '@/services/api';
import type {
  AuthContextType,
  ChangePasswordRequest,
  Employee,
  LoginCredentials,
  MeAccess,
} from '@/types/auth.types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Load /me/access/ for a signed-in employee. Skipped while a temporary
 * password is held. A 403 PASSWORD_CHANGE_REQUIRED flags the employee, so
 * ProtectedRoute sends them to change it - never an empty menu or a logout.
 * Any other failure leaves access empty (useRole falls back to staff).
 */
async function loadAccess(
  employee: Employee
): Promise<{ employee: Employee; access: MeAccess | null }> {
  if (employee.must_change_password) return { employee, access: null };
  try {
    return { employee, access: await authService.getMyAccess() };
  } catch (error) {
    if (
      isAxiosError(error) &&
      (error.response?.data as { code?: string } | undefined)?.code === 'PASSWORD_CHANGE_REQUIRED'
    ) {
      return { employee: { ...employee, must_change_password: true }, access: null };
    }
    return { employee, access: null };
  }
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [access, setAccess] = useState<MeAccess | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(getAccessToken());
  const [refreshToken, setRefreshToken] = useState<string | null>(getRefreshToken());
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!accessToken && !!employee;

  // Initialize auth state from stored tokens
  useEffect(() => {
    const initAuth = async () => {
      const storedAccessToken = getAccessToken();
      const storedRefreshToken = getRefreshToken();

      if (storedAccessToken && storedRefreshToken) {
        try {
          const loaded = await loadAccess(await authService.getCurrentEmployee());
          setEmployee(loaded.employee);
          setAccess(loaded.access);
          setAccessToken(storedAccessToken);
          setRefreshToken(storedRefreshToken);
        } catch {
          // Token is invalid, clear everything
          clearTokens();
          setEmployee(null);
          setAccessToken(null);
          setRefreshToken(null);
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const response = await authService.login(credentials);
      const loaded = await loadAccess({
        ...response.employee,
        must_change_password: response.must_change_password,
      });
      setEmployee(loaded.employee);
      setAccess(loaded.access);
      setAccessToken(response.access);
      setRefreshToken(response.refresh);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const changePassword = useCallback(async (request: ChangePasswordRequest) => {
    const response = await authService.changePassword(request);
    setAccessToken(response.access);
    setRefreshToken(response.refresh);
    if (!employee) return;
    const loaded = await loadAccess({
      ...employee,
      must_change_password: response.must_change_password,
    });
    setEmployee(loaded.employee);
    setAccess(loaded.access);
  }, [employee]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setEmployee(null);
      setAccess(null);
      setAccessToken(null);
      setRefreshToken(null);
      clearTokens();
      setIsLoading(false);
    }
  }, []);

  const refreshAccessToken = useCallback(async () => {
    try {
      const newToken = await authService.refreshToken();
      if (newToken) {
        setAccessToken(newToken);
        const currentRefresh = getRefreshToken();
        if (currentRefresh) {
          setTokens(newToken, currentRefresh);
        }
      }
      return newToken;
    } catch {
      await logout();
      return null;
    }
  }, [logout]);

  const value: AuthContextType = {
    employee,
    access,
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAccessToken,
    changePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
