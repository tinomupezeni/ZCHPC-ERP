import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredPermission 
}) => {
  const { isAuthenticated, user, loading, checkPermission } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Redirect to login if not authenticated
      navigate('/login', { 
        state: { from: location.pathname },
        replace: true
      });
    } else if (
      !loading && 
      isAuthenticated && 
      requiredPermission && 
      !checkPermission(requiredPermission)
    ) {
      // Redirect to dashboard if authenticated but doesn't have permission
      navigate('/dashboard', { replace: true });
    }
  }, [loading, isAuthenticated, navigate, location, requiredPermission, checkPermission]);

  // Show nothing while checking auth
  if (loading) {
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

  // If we have permission requirements and user doesn't have it, show nothing
  if (requiredPermission && !checkPermission(requiredPermission)) {
    return null;
  }

  // Otherwise render children
  return <>{children}</>;
};

export default ProtectedRoute;
