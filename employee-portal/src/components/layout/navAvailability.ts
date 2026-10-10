/**
 * What the evaluation leaves out (PLAN §4a). This list is the policy; edit
 * only here.
 * - 'hidden': dropped from the sidebar and the mobile nav.
 * - 'not-available': kept in the navigation, marked "Not available".
 * Either way MainLayout renders "Not available in this evaluation" for the
 * route instead of the page, so a direct URL never reaches a broken page or
 * falls through to /careers. A path also covers its sub-paths.
 */
export type Availability = 'hidden' | 'not-available';

export const EVALUATION_AVAILABILITY: Record<string, Availability> = {
  // Role-group links with no page behind them (INT-01 §2)
  '/portal/employees': 'hidden',
  '/portal/reports': 'hidden',
  '/portal/payroll': 'hidden',
  '/portal/accounts': 'hidden',
  '/portal/expenses': 'hidden',
  '/portal/procurement': 'hidden',
  '/portal/inventory': 'hidden',
  '/portal/suppliers': 'hidden',
  '/portal/settings': 'hidden',
  // Real pages that are not ready (PY-1, A-6, B12)
  '/portal/payslips': 'not-available',
  '/portal/leave': 'not-available',
  // Dashboard tiles. The leave balance is not real yet (the API returns none);
  // remove together with /portal/leave once it is.
  'tile:dashboard/leave-balance': 'not-available',
};

export function availabilityFor(path: string): Availability | undefined {
  if (EVALUATION_AVAILABILITY[path]) return EVALUATION_AVAILABILITY[path];
  const prefix = Object.keys(EVALUATION_AVAILABILITY).find((entry) =>
    path.startsWith(`${entry}/`)
  );
  return prefix ? EVALUATION_AVAILABILITY[prefix] : undefined;
}

/** Hidden paths have no page of their own; App.tsx gives them a route. */
export const HIDDEN_PATHS = Object.keys(EVALUATION_AVAILABILITY).filter(
  (path) => EVALUATION_AVAILABILITY[path] === 'hidden'
);
