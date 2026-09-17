import { useEffect, useState } from 'react';
import { purchaseRequestService } from '@/services/purchase-request.service';

export interface PurchaseRequestReviewerAccess {
  /**
   * null while the check is still in flight. Callers must treat null the
   * same as false (never render the link) - showing it briefly and then
   * hiding it would be worse than a short delay before it appears.
   */
  canReviewAsDepartmentHead: boolean | null;
  canVerifyAsAccounts: boolean | null;
  canRecommendAsGM: boolean | null;
}

/**
 * Whether the current employee can reach the Department Head review queue,
 * the Accounts verification queue, and/or the GM recommendation queue (F20
 * follow-up, extended for F21).
 *
 * There is no permissions list anywhere the frontend can read today: the
 * portal login/`me` responses (EmployeeProfileSerializer) carry only name/
 * department/position, never role_name or a permissions array, and
 * useRole() is purely a coarse role-NAME guess (see its own module docstring
 * concerns) that doesn't reliably reflect either the dedicated PR_TEST_*
 * seed roles or, more generally, any real employee whose HR role name
 * doesn't line up with their actual purchase-request permission - for the
 * seeded accounts specifically, role_name comes back null entirely, so
 * useRole() falls back to 'staff' for every one of them regardless of who
 * actually holds department_head_approve/accounts_verify/gm_recommend.
 *
 * Rather than adding a new backend endpoint just to expose permission
 * strings, this reuses the exact same queue endpoints the review pages
 * themselves already call (getPendingDepartmentHeadRequests/
 * getPendingAccountsRequests/getPendingGMRequests) - a 200 (even with zero
 * rows) means the backend's own RBAC + PurchaseRequestAuthorizationPolicy
 * checks let this actor in, and any failure means they don't. That IS the
 * application's authoritative permission information, obtained through its
 * existing surface rather than a guessed role name or a new API. Mirrors
 * usePurchaseRequestActionCount's own precedent: the sidebar is mounted
 * independently of the review pages (siblings under MainLayout, no shared
 * fetch/cache), so it does its own lightweight calls rather than reusing
 * page-level state.
 *
 * Any failure (403 or otherwise) resolves to false, not just a 403 -
 * matching usePurchaseRequestActionCount's "fail silently, safe default"
 * behavior: hiding a link on a transient network error is a strictly safer
 * default than showing one that the backend then always rejects anyway.
 */
export function usePurchaseRequestReviewerAccess(): PurchaseRequestReviewerAccess {
  const [canReviewAsDepartmentHead, setCanReviewAsDepartmentHead] = useState<boolean | null>(
    null
  );
  const [canVerifyAsAccounts, setCanVerifyAsAccounts] = useState<boolean | null>(null);
  const [canRecommendAsGM, setCanRecommendAsGM] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;

    purchaseRequestService
      .getPendingDepartmentHeadRequests()
      .then(() => {
        if (!cancelled) setCanReviewAsDepartmentHead(true);
      })
      .catch(() => {
        if (!cancelled) setCanReviewAsDepartmentHead(false);
      });

    purchaseRequestService
      .getPendingAccountsRequests()
      .then(() => {
        if (!cancelled) setCanVerifyAsAccounts(true);
      })
      .catch(() => {
        if (!cancelled) setCanVerifyAsAccounts(false);
      });

    purchaseRequestService
      .getPendingGMRequests()
      .then(() => {
        if (!cancelled) setCanRecommendAsGM(true);
      })
      .catch(() => {
        if (!cancelled) setCanRecommendAsGM(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { canReviewAsDepartmentHead, canVerifyAsAccounts, canRecommendAsGM };
}

export default usePurchaseRequestReviewerAccess;
