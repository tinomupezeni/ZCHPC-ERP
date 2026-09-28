import { useState } from "react";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";
import { KeyRound, Loader2 } from "lucide-react";
import apiClient from "@/services/apiClient";
import { useAuth } from "@/contexts/AuthContext";

/**
 * REM-07: replace a temporary password. The backend confines an account
 * holding one to this change; success revokes every earlier token and
 * returns a fresh pair.
 */
export default function ChangePasswordPage() {
  const { user, isLoading, logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isLoading && !user) return <Navigate to="/login" replace />;

  const forced = !!user?.must_change_password;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setErrors(["The new passwords do not match."]);
      return;
    }
    setErrors([]);
    setIsSubmitting(true);
    try {
      const { data } = await apiClient.post("/auth/password/change/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      localStorage.setItem("accessToken", data.access);
      localStorage.setItem("refreshToken", data.refresh);
      toast.success("Password changed");
      // Reload so the profile (now without the flag) is fetched fresh.
      window.location.assign("/dashboard");
    } catch (error: any) {
      const body = error.response?.data;
      setErrors(
        body?.errors?.length
          ? body.errors
          : body?.new_password?.length
          ? body.new_password
          : [body?.detail || "Your password could not be changed. Please try again."]
      );
      setIsSubmitting(false);
    }
  };

  const field = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
        <div className="text-center mb-6">
          <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
            <KeyRound className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800">Change your password</h1>
          <p className="text-sm text-slate-500 mt-1">
            {forced
              ? "You signed in with a temporary password. Choose your own password to continue."
              : "Choose a new password for your account."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.length > 0 && (
            <ul role="alert" className="rounded-md bg-red-50 text-red-700 text-sm p-3 space-y-1">
              {errors.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          )}
          <div className="space-y-1">
            <label htmlFor="current-password" className="text-sm font-medium text-slate-700">
              {forced ? "Temporary password" : "Current password"}
            </label>
            <input id="current-password" type="password" autoComplete="current-password" required
              className={field} value={currentPassword} disabled={isSubmitting}
              onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label htmlFor="new-password" className="text-sm font-medium text-slate-700">New password</label>
            <input id="new-password" type="password" autoComplete="new-password" required
              className={field} value={newPassword} disabled={isSubmitting}
              onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label htmlFor="confirm-password" className="text-sm font-medium text-slate-700">Confirm new password</label>
            <input id="confirm-password" type="password" autoComplete="new-password" required
              className={field} value={confirmPassword} disabled={isSubmitting}
              onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <button type="submit"
            disabled={isSubmitting || !currentPassword || !newPassword || !confirmPassword}
            className="w-full py-3 bg-primary text-white rounded-lg font-semibold disabled:opacity-60 flex items-center justify-center gap-2">
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "Saving..." : "Change password"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Not you?{" "}
          <button type="button" className="text-primary hover:underline" onClick={logout}>
            Sign out
          </button>
        </p>
      </div>
    </div>
  );
}
