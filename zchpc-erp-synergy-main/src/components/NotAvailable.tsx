import { Ban } from "lucide-react";

/** Shown in place of any screen the evaluation leaves out (navConfig). */
const NotAvailable = () => (
  <div className="flex flex-col items-center justify-center py-24 text-center">
    <div className="mb-4 h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center">
      <Ban className="h-7 w-7 text-slate-400" />
    </div>
    <h1 className="text-2xl font-bold text-slate-800">
      Not available in this evaluation
    </h1>
    <p className="mt-2 max-w-md text-sm text-slate-500">
      This part of the system is not part of the current evaluation.
    </p>
  </div>
);

export default NotAvailable;
