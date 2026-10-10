import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { isAxiosError } from "axios";
import { MeAccess, User } from "../types/index";
import * as authService from "../services/auth.services";

interface AuthContextType {
  user: User | null;
  access: MeAccess | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  checkPermission: (requiredModules: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Load /me/access/ for a signed-in user. A login still holding a temporary
 * password gets 403 PASSWORD_CHANGE_REQUIRED there (REM-07): that user comes
 * back flagged so ProtectedRoute sends them to /change-password. Any other
 * failure leaves access empty rather than signing the user out.
 */
const loadAccess = async (
  user: User
): Promise<{ user: User; access: MeAccess | null }> => {
  if (user.must_change_password) return { user, access: null };
  try {
    return { user, access: await authService.getMyAccess() };
  } catch (error) {
    if (
      isAxiosError(error) &&
      error.response?.data?.code === "PASSWORD_CHANGE_REQUIRED"
    ) {
      return { user: { ...user, must_change_password: true }, access: null };
    }
    console.error("Failed to load /auth/users/me/access/", error);
    return { user, access: null };
  }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [access, setAccess] = useState<MeAccess | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Local only: used when the session is already gone (failed refresh or
  // profile load), so it never calls the server and cannot loop.
  const endSession = () => {
    authService.clearTokens();
    setUser(null);
    setAccess(null);
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  };

  // The user's logout: revoke the refresh token on the server, then end the
  // session locally even if that call fails.
  const logout = async () => {
    try {
      await authService.revokeRefreshToken();
    } catch {
      // still log out locally
    } finally {
      endSession();
    }
  };

  useEffect(() => {
    const handleGlobalLogout = () => endSession();
    window.addEventListener("auth:logout", handleGlobalLogout);

    const checkAuthStatus = async () => {
      const token = localStorage.getItem("accessToken");
      if (token) {
        try {
          const userProfile = await authService.getProfile();
          if (userProfile) {
            const loaded = await loadAccess(userProfile);
            setUser(loaded.user);
            setAccess(loaded.access);
          } else {
            endSession();
          }
        } catch (err) {
          endSession();
        }
      }
      setIsLoading(false); // Critical: Loading ends after fetch
    };

    checkAuthStatus();
    return () => window.removeEventListener("auth:logout", handleGlobalLogout);
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const loaded = await loadAccess(await authService.login(email, password));
      setUser(loaded.user);
      setAccess(loaded.access);
      setIsLoading(false);
      return loaded.user;
    } catch (error) {
      setUser(null);
      setAccess(null);
      setIsLoading(false);
      throw error;
    }
  };

  // requiredModules are backend permission modules ("hr", "payroll", ...),
  // or "admin" for the full "*" grant. A module is held when any permission
  // starts with it, the same rule the backend route gate applies.
  const checkPermission = (requiredModules: string[]) => {
    const permissions = access?.permissions ?? [];
    if (permissions.includes("*")) return true;

    const heldModules = new Set(
      permissions.map((permission) => permission.split(".")[0].toLowerCase())
    );
    return requiredModules.some(
      (module) => module !== "admin" && heldModules.has(module.toLowerCase())
    );
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        access,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        checkPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
