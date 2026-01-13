import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { ROLE_ROUTES } from "@/types/auth";

export const useLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [viewPassword, setViewPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const user = await login(email, password);
      const rawRole = user?.employee_profile?.role || user?.role;

      if (rawRole) {
        const roleKey = rawRole.toLowerCase();
        toast.success(`Welcome back, ${user.first_name}!`);
        // Navigate to mapped route or default to dashboard
        navigate(ROLE_ROUTES[roleKey] || "/dashboard");
      } else {
        toast.error("User profile incomplete. Contact Admin.");
      }
    } catch (error) {
      toast.error("Authentication failed. Please check your credentials.");
    } finally {
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
