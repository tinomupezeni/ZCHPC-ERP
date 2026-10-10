import { ExternalLink, LayoutGrid } from "lucide-react";
import { Button } from "@/components/ui/button";

// The Employee Portal's origin, baked in at build time; no link when unset.
const PORTAL_URL: string = import.meta.env.VITE_PORTAL_URL || "";

/**
 * Shown instead of any screen to a user who has no module in this app
 * (empty sidebar), e.g. staff whose only grants are purchase requests.
 */
const WorkIsInPortal = () => (
  <div className="flex flex-col items-center justify-center py-24 text-center">
    <div className="mb-4 h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center">
      <LayoutGrid className="h-7 w-7 text-slate-400" />
    </div>
    <h1 className="text-2xl font-bold text-slate-800">
      Your work is in the Employee Portal
    </h1>
    <p className="mt-2 max-w-md text-sm text-slate-500">
      Your account has nothing to do in this app. Purchase requests, approvals
      and your own records are in the Employee Portal.
    </p>
    {PORTAL_URL && (
      <Button asChild className="mt-6">
        <a href={PORTAL_URL}>
          Open the Employee Portal
          <ExternalLink className="ml-2 h-4 w-4" />
        </a>
      </Button>
    )}
  </div>
);

export default WorkIsInPortal;
