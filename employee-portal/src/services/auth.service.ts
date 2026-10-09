import api, { setTokens, clearTokens, getRefreshToken, TOKEN_REFRESH_PATH } from './api';
import type {
  ChangePasswordRequest,
  ChangePasswordResponse,
  LoginCredentials,
  LoginResponse,
  Employee,
  TokenRefreshResponse,
} from '@/types/auth.types';

export const authService = {
  /**
   * Login with EC number and password
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/portal/auth/login/', credentials);
    const { access, refresh } = response.data;

    // Store tokens
    setTokens(access, refresh);

    return response.data;
  },

  /**
   * Logout - blacklist refresh token
   */
  async logout(): Promise<void> {
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        await api.post('/portal/auth/logout/', { refresh: refreshToken });
      }
    } finally {
      clearTokens();
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string | null> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    try {
      const response = await api.post<TokenRefreshResponse>(TOKEN_REFRESH_PATH, {
        refresh: refreshToken,
      });
      return response.data.access;
    } catch {
      clearTokens();
      return null;
    }
  },

  /**
   * Get current user's profile
   */
  async getCurrentEmployee(): Promise<Employee> {
    const response = await api.get<Employee>('/portal/auth/me/');
    return response.data;
  },

  /**
   * Replace the caller's own password (REM-07). The change revokes every
   * earlier token, so the fresh pair returned replaces the stored one.
   */
  async changePassword(request: ChangePasswordRequest): Promise<ChangePasswordResponse> {
    const response = await api.post<ChangePasswordResponse>('/auth/password/change/', request);
    setTokens(response.data.access, response.data.refresh);
    return response.data;
  },
};

export default authService;
