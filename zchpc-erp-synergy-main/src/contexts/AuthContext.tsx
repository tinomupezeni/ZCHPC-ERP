import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Server from "../server/Server";

// Create the context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// The AuthProvider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // The login function
  const login = useCallback(async (email, password) => {
    try {
      const response = await Server.login(email, password);
      const { access, refresh } = response.data;

      // Store tokens in localStorage
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);

      // Fetch the user details after successful login
      const userResponse = await Server.fetchUserDetailsFromToken();
      setUser(userResponse.data);
      setIsAuthenticated(true);
      toast.success("Login successful!");
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      toast.error("Login failed. Please check your credentials.");
      return false;
    }
  }, []);

  // The logout function
  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    setIsAuthenticated(false);
    toast.info("Logged out.");
    navigate("/login", { replace: true });
  }, [navigate]);

  // Check for stored tokens on component mount
  useEffect(() => {
    const access_token = localStorage.getItem("access_token");

    const checkToken = async () => {
      if (access_token) {
        try {
          const userResponse = await Server.fetchUserDetailsFromToken();
          
          setUser(userResponse.data);
          setIsAuthenticated(true);
        } catch (error) {
          // Token is invalid or expired, log out the user
          console.error("Token validation failed:", error);
          logout();
        } finally {
          setIsLoading(false);
        }
      } else {
        // No token, so the user is not authenticated
        setIsLoading(false);
      }
    };

    checkToken();
  }, []);

  // This is the corrected checkPermission function
  const checkPermission = useCallback(
    (permissions) => {
      if (!user) {
        return false;
      }
      const userRole = user.role?.toLowerCase();

      if (typeof permissions === "string") {
        return userRole === permissions.toLowerCase();
      }
      if (Array.isArray(permissions)) {
        return permissions.some((p) => userRole === p.toLowerCase());
      }
      return false;
    },
    [user]
  );

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    checkPermission,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};