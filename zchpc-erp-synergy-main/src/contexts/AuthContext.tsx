import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import * as authService from '../server/auth.services';

// Define the shape of your context
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  checkPermission: (requiredRoles: string[]) => boolean;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create the provider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start as true on app load

  // On initial app load, check if the user is already logged in
  useEffect(() => {
    const checkAuthStatus = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('accessToken');
      
      if (token) {
        const userProfile = await authService.getProfile();
        if (userProfile) {
          setUser(userProfile);
        } else {
          // Token was invalid or expired
          authService.logout();
        }
      }
      setIsLoading(false);
    };
    
    checkAuthStatus();
  }, []);

  // Login function for the context
  const login = async (email: string, password: string) => {
    try {
      const loggedInUser = await authService.login(email, password);
      setUser(loggedInUser);
      return loggedInUser;
    } catch (error) {
      setUser(null);
      throw error; // Re-throw for the login page to handle
    }
  };

  // Logout function for the context
  const logout = () => {
    authService.logout();
    setUser(null);
    location.reload()
  };

  // Permission check (using the correct nested 'role')
  const checkPermission = (requiredRoles: string[]) => {
    // 1. Get the user's actual role from the profile
    const userRole = user?.employee_profile?.role; // e.g., "ADMIN"

    // 2. If no user or no role, they have no permission
    if (!userRole) {
      return false;
    }

    // 3. Check if the user's role is in the required list
    // We compare in uppercase to be safe and match the database
    return requiredRoles.some(
      (role) => role.toLowerCase() === userRole.toLowerCase()
    );
  };

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    checkPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Create the custom hook for components to use
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};