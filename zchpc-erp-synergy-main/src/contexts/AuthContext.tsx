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

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const loggedInUser = await authService.login(email, password);
      setUser(loggedInUser);
      setIsLoading(false);
      return loggedInUser;
    } catch (error) {
      setUser(null);
      setIsLoading(false);
      throw error;
    }
  };

  console.log(user);
  

 const checkPermission = (requiredModules: string[]) => {
    if (!user) return false;

    // 1. System Admins (Django Superusers/Staff) see everything
    if (user.is_staff || user.is_superuser) return true;

    // 2. Get the user's role - check both direct and nested structure
    const rawRole = user.employee_profile?.role || user.role || "";
    const userRole = (typeof rawRole === 'string' ? rawRole : "").toUpperCase();

    // 3. Check if user is admin
    if (userRole === "ADMIN" || userRole === "SYSTEM_ADMINISTRATOR") return true;

    // 4. Role name mappings - map database role names to navConfig permission names
    // These map to the permission arrays in navConfig.tsx
    const roleToPermissionMap: Record<string, string[]> = {
      "HUMAN_RESOURCES": ["hr"],  // HR sees HR and Payroll (both accept "hr")
      "HR": ["hr"],
      "ACCOUNTANT": ["accountant"],
      "PROCUREMENT": ["procurement"],
      "PROCUREMENT_OFFICER": ["procurement"],
      "SALES": ["sales"],
      "SALES_REPRESENTATIVE": ["sales"],
      "MANAGER": ["hr", "accountant"],  // Manager sees HR, Payroll, Accounting
      "DEPARTMENT_MANAGER": ["hr", "accountant"],
      "STAFF": [],  // Staff has no sidebar access
      "REGULAR_STAFF": [],
      "INTERN": [],
      "INVENTORY": ["inventory"],
    };

    // 5. Get the permissions this role grants
    const rolePermissions = roleToPermissionMap[userRole] || [];

    // 6. Also include any explicit role_permissions from the backend
    const backendPermissions: string[] = user?.employee_profile?.role_permissions || [];

    // 7. Combine all permissions
    const allUserPermissions = [...rolePermissions, ...backendPermissions].map(p => p.toLowerCase());

    // 8. Check if user has any of the required permissions
    return requiredModules.some((mod) =>
      allUserPermissions.includes(mod.toLowerCase())
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
