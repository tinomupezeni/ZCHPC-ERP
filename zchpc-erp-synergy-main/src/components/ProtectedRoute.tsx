import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { homePathFor } from '@/layout/navConfig';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredPermission 
}) => {
  const { user, access, isLoading, checkPermission } = useAuth(); // This now works!
  const navigate = useNavigate();
  const location = useLocation();
  const allowed = !requiredPermission || checkPermission(requiredPermission);
  // Undefined when the user has no ERP module; MainLayout then shows
  // "Your work is in the Employee Portal" on whatever page they are on.
  const homePath = homePathFor(checkPermission, access?.active_modules ?? []);

  useEffect(() => {
    if (isLoading) return; // Wait for the context's auth check

    // If check is done and there's no user, redirect to login
    if (!user) {
      navigate('/login', {
        state: { from: location.pathname },
        replace: true,
      });
      return;
    }

    // REM-07: a temporary password must be replaced before anything else
    // (the backend enforces this; this keeps the user on the page that works).
    if (user.must_change_password) {
      navigate('/change-password', { replace: true });
      return;
    }

    // Without the permission, go to the user's own landing page. Never to
    // /dashboard by default: it is the Administrator's page, and its data
    // call is refused for every other role ("Failed to Load Dashboard").
    if (!allowed && homePath && homePath !== location.pathname) {
      navigate(homePath, { replace: true });
    }
  }, [isLoading, user, allowed, homePath, navigate, location.pathname]);
  // Render a isLoading spinner while the auth status is being determined
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse-light">
          <svg
            className="w-12 h-12 text-primary"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0
              3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        </div>
      </div>
    );
  }

  // Not even mounted while a redirect is pending: the page's own data calls
  // would be refused. With no landing page (no ERP module) the children
  // render, and MainLayout replaces the page with the Portal pointer.
  if (user && !allowed && homePath) return null;

  // If authenticated and has permission (or no permission is required), render children
  return <>{children}</>;
};

export default ProtectedRoute;