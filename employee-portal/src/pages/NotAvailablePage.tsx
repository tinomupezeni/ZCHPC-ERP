import { Link } from 'react-router-dom';
import { ArrowLeft, Hourglass } from 'lucide-react';

export const COMING_SOON_TITLE = 'Coming soon';
export const COMING_SOON_TEXT = "This module is being built and isn't part of this version yet.";

/** Shown in place of any page this version leaves out (navAvailability). */
export function NotAvailablePage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-4 h-14 w-14 rounded-full bg-slate-100 flex items-center justify-center">
        <Hourglass className="h-7 w-7 text-slate-400" />
      </div>
      <h1 className="text-2xl font-bold text-slate-800">{COMING_SOON_TITLE}</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">{COMING_SOON_TEXT}</p>
      <Link
        to="/portal"
        className="mt-6 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to dashboard
      </Link>
    </div>
  );
}

export default NotAvailablePage;
