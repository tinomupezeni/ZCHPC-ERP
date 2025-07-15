
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { BarChart3, Home } from "lucide-react";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="flex items-center justify-center mb-4">
        <div className="p-3 rounded-full bg-primary/10 text-primary">
          <BarChart3 className="h-12 w-12" />
        </div>
      </div>
      <h1 className="text-4xl font-bold mb-2">404</h1>
      <h2 className="text-2xl font-medium mb-4">Page Not Found</h2>
      <p className="text-muted-foreground text-center mb-8 max-w-md">
        The page you are looking for doesn't exist or has been moved. Please check the URL or return to the dashboard.
      </p>
      <Button onClick={() => navigate("/dashboard")} className="animate-pulse-light">
        <Home className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Button>
    </div>
  );
};

export default NotFound;
