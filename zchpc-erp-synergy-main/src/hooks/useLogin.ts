import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { ROLE_ROUTES } from "@/types/auth";

export const useLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [viewPassword, setViewPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);

  const navigate = useNavigate();
  const { login, user, isAuthenticated } = useAuth();
  const hasNavigated = useRef(false);

  // Navigate when user state is updated after login
  useEffect(() => {
    if (pendingNavigation && isAuthenticated && user && !hasNavigated.current) {
      hasNavigated.current = true;
      navigate(pendingNavigation);
      setPendingNavigation(null);
    }
  }, [pendingNavigation, isAuthenticated, user, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    hasNavigated.current = false;

    try {
      const loggedInUser = await login(email, password);
      
      // Check if user is admin/superuser first
      if (loggedInUser?.is_superuser || loggedInUser?.is_staff) {
        toast.success(`Welcome back, ${loggedInUser.first_name}!`);
        setPendingNavigation("/dashboard"); // or your admin route
        return;
      }

      // For regular users, check for employee profile and role
      const rawRole = loggedInUser?.employee_profile?.role || loggedInUser?.role;

      if (rawRole) {
        const roleKey = rawRole.toLowerCase();
        toast.success(`Welcome back, ${loggedInUser.first_name}!`);
        // Set pending navigation - useEffect will handle actual navigation
        const targetRoute = ROLE_ROUTES[roleKey] || "/dashboard";
        setPendingNavigation(targetRoute);
      } else {
        // Regular user without role/profile - this is an error
        toast.error("User profile incomplete. Contact Admin.");
        setIsSubmitting(false);
      }
    } catch (error) {
      toast.error("Authentication failed. Please check your credentials.");
      setIsSubmitting(false);
    }
  };

  return {
    email,
    setEmail,
    password,
    setPassword,
    viewPassword,
    setViewPassword,
    isSubmitting,
    handleLogin,
  };
};