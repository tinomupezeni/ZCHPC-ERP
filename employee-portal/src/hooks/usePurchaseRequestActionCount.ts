import { useEffect, useState } from 'react';
import { purchaseRequestService } from '@/services/purchase-request.service';
import { isActionRequired } from '@/components/purchase-requests/statusConfig';

/**
 * Count of the caller's own purchase requests needing action (DRAFT or
 * REJECTED), for the sidebar nav badge.
 *
 * Sidebar is mounted independently of PurchaseRequestsPage (siblings under
 * MainLayout, no shared fetch/cache between them), so this does its own
 * lightweight call to the existing `scope=mine` endpoint rather than reusing
 * page-level state - no new backend endpoint, just the same list call used
 * elsewhere, counted client-side. Fails silently: the badge is a convenience
 * cue, not something worth showing an error state for in the nav.
 */
export function usePurchaseRequestActionCount(): number {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    purchaseRequestService
      .getMyRequests()
      .then((requests) => {
        if (cancelled) return;
        setCount(requests.filter((request) => isActionRequired(request.status)).length);
      })
      .catch(() => {
        // Silent by design - see module docstring.
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return count;
}

export default usePurchaseRequestActionCount;
