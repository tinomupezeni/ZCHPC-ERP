import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, KeyRound, Loader2 } from 'lucide-react';

type ChangePasswordError = {
  response?: { data?: { detail?: string; errors?: string[]; new_password?: string[] } };
};

function errorMessages(err: unknown): string[] {
  const data = (err as ChangePasswordError)?.response?.data;
  if (data?.errors?.length) return data.errors;
  if (data?.new_password?.length) return data.new_password;
  if (data?.detail) return [data.detail];
  return ['Your password could not be changed. Please try again.'];
}

/**
 * REM-07: the one page an account holding a temporary password can use.
 * The backend confines such accounts to this change; replacing the password
 * lifts that and returns fresh tokens (the old ones are revoked).
 */
export function ChangePasswordPage() {
  const { employee, changePassword, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const forced = !!employee?.must_change_password;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setErrors(['The new passwords do not match.']);
      return;
    }
    setErrors([]);
    setIsSubmitting(true);
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      toast.success('Password changed');
      navigate('/portal', { replace: true });
    } catch (err) {
      setErrors(errorMessages(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-100 to-primary-50 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
            <KeyRound className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold">Change your password</CardTitle>
          <CardDescription>
            {forced
              ? 'You signed in with a temporary password. Choose your own password to continue.'
              : 'Choose a new password for your account.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.length > 0 && (
              <div
                role="alert"
                className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm"
              >
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <ul className="space-y-1">
                  {errors.map((message) => (
                    <li key={message}>{message}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="current-password">
                {forced ? 'Temporary password' : 'Current password'}
              </Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                required
                disabled={isSubmitting}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm new password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
                disabled={isSubmitting}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting || !currentPassword || !newPassword || !confirmPassword}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Change password'
              )}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Not you?{' '}
            <button type="button" className="text-primary hover:underline" onClick={() => logout()}>
              Sign out
            </button>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default ChangePasswordPage;
