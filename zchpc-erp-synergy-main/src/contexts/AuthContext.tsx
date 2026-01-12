import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { User } from "../types/index";
import * as authService from "../services/auth.services";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  checkPermission: (requiredModules: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = () => {
    authService.clearTokens();
    setUser(null);
    window.location.href = "/login";
  };

  useEffect(() => {
    const handleGlobalLogout = () => logout();
    window.addEventListener("auth:logout", handleGlobalLogout);

    const checkAuthStatus = async () => {
      const token = localStorage.getItem("accessToken");
      if (token) {
        try {
          const userProfile = await authService.getProfile();
          if (userProfile) {
            setUser(userProfile);
          } else {
            logout();
          }
        } catch (err) {
          logout();
        }
      }
      setIsLoading(false); // Critical: Loading ends after fetch
    };

    checkAuthStatus();
    return () => window.removeEventListener("auth:logout", handleGlobalLogout);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const loggedInUser = await authService.login(email, password);
      setUser(loggedInUser);
      return loggedInUser;
    } catch (error) {
      setUser(null);
      throw error;
    }
  };

  const checkPermission = (requiredModules: string[]) => {
    if (!user) return false;

    // 1. System Admins (Django Superusers) see everything
    if (user.is_staff || user.is_superuser) return true;

    // 2. Get permissions from the profile (sent by the backend serializer)
    const userPermissions: string[] =
      user?.employee_profile?.role_permissions || [];

    // 3. Normalize to Uppercase for matching
    const normalizedUserPerms = userPermissions.map((p) => p.toUpperCase());

    return requiredModules.some((mod) =>
      normalizedUserPerms.includes(mod.toUpperCase())
    );
  };

  return (
    <AuthContext.Provider
      value={{
        user,
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
