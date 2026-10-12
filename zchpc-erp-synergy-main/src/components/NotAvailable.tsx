import { useNavigate } from "react-router-dom";
import { ArrowLeft, Hourglass } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Shown in place of any screen this version leaves out (navConfig).
 * homePath is the user's own landing page (the first item of their sidebar).
 */
const NotAvailable = ({ homePath = "/dashboard" }: { homePath?: string }) => {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-4 h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center">
        <Hourglass className="h-7 w-7 text-slate-400" />
      </div>
      <h1 className="text-2xl font-bold text-slate-800">Coming soon</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        This module is being built and isn't part of this version yet.
      </p>
      <Button className="mt-6" onClick={() => navigate(homePath)}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to dashboard
      </Button>
    </div>
  );
};

export default NotAvailable;
