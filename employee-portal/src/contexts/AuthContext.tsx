import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { authService } from '@/services/auth.service';
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from '@/services/api';
import type { Employee, LoginCredentials, AuthContextType } from '@/types/auth.types';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [employee, setEmployee] = useState<Employee | null>(null);
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
          const employeeData = await authService.getCurrentEmployee();
          setEmployee(employeeData);
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
      setEmployee(response.employee);
      setAccessToken(response.access);
      setRefreshToken(response.refresh);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setEmployee(null);
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
    accessToken,
    refreshToken,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshAccessToken,
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
