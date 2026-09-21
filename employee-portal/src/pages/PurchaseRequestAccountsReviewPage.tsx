import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle, XCircle } from 'lucide-react';
import { PageHeader } from '@/components/layout';
import { Button } from '@/components/ui/button';
import {
  PurchaseRequestDetail,
  PurchaseRequestReviewList,
  PurchaseRequestActionDialog,
  PurchaseRequestBudgetCodeAssignment,
  PurchaseRequestRejectDialog,
  type ReviewQueueError,
} from '@/components/purchase-requests';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type {
  BudgetCode,
  PurchaseRequest,
  PurchaseRequestListItem,
} from '@/types/purchase-request.types';

/**
 * F18: the Accounts review queue. A deliberate copy/adapt of
 * PurchaseRequestReviewPage (F17's Department Head page), not a shared
 * abstraction - the only real differences are which two service methods are
 * called, the page copy, and the Verify dialog's stage-specific wording.
 * GM/Director will likely follow the same pattern rather than a generic
 * "ReviewPageFactory" - see F17/F18's own investigation reports for why.
 */
export function PurchaseRequestAccountsReviewPage() {
  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [queueError, setQueueError] = useState<ReviewQueueError | null>(null);

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const [budgetCodes, setBudgetCodes] = useState<BudgetCode[] | null>(null);
  const [budgetCodeError, setBudgetCodeError] = useState<string | null>(null);
  const [savingItemId, setSavingItemId] = useState<number | null>(null);

  const [pendingVerify, setPendingVerify] = useState<PurchaseRequest | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const [pendingReject, setPendingReject] = useState<PurchaseRequest | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setQueueError(null);
    try {
      const data = await purchaseRequestService.getPendingAccountsRequests();
      setRequests(data);
    } catch (error) {
      const httpStatus = (error as { response?: { status?: number } })?.response?.status;
      setQueueError(
        httpStatus === 403
          ? {
              kind: 'unauthorized',
              // F20 follow-up: shown as-is to the employee, so this must stay
              // human-facing - never the backend's raw permission identifier
              // (e.g. "Missing required permission '...'"), which
              // getPurchaseRequestErrorMessage would otherwise surface here
              // since the backend's 403 body does carry one.
              message: 'You do not have access to the Accounts verification queue.',
            }
          : {
              kind: 'generic',
              message: getPurchaseRequestErrorMessage(
                error,
                'Failed to load requests awaiting Accounts verification'
              ),
            }
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  /** F25: the approved budget codes are fetched once, on first need. */
  const loadBudgetCodes = useCallback(async () => {
    setBudgetCodeError(null);
    try {
      setBudgetCodes(await purchaseRequestService.getBudgetCodes());
    } catch (error) {
      setBudgetCodeError(getPurchaseRequestErrorMessage(error, 'Failed to load budget codes'));
    }
  }, []);

  const handleAssignBudgetCode = async (itemId: number, budgetCodeId: number) => {
    if (!selectedRequest) return;
    setSavingItemId(itemId);
    try {
      const updated = await purchaseRequestService.assignItemBudgetCode(
        selectedRequest.id,
        itemId,
        budgetCodeId
      );
      setSelectedRequest(updated);
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to assign budget code'));
    } finally {
      setSavingItemId(null);
    }
  };

  const removeFromQueue = (id: number) => {
    setRequests((prev) => prev.filter((r) => r.id !== id));
  };

  const closeDetail = () => {
    setIsDetailOpen(false);
    setSelectedRequest(null);
  };

  const handleView = async (id: number) => {
    setIsDetailOpen(true);
    setIsDetailLoading(true);
    setSelectedRequest(null);
    try {
      const detail = await purchaseRequestService.getRequest(id);
      setSelectedRequest(detail);
      if (budgetCodes === null) void loadBudgetCodes();
    } catch (error) {
      setIsDetailOpen(false);
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to load purchase request'));
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleOpenVerify = () => {
    if (!selectedRequest) return;
    setPendingVerify(selectedRequest);
  };

  const handleCancelVerify = () => {
    if (isVerifying) return;
    setPendingVerify(null);
  };

  /**
   * Backend remains authoritative: the request is only removed from the
   * queue and the detail view only closes once the 200 actually comes back.
   * A failure leaves everything exactly as it was, with an error toast.
   */
  const handleConfirmVerify = async () => {
    if (!pendingVerify) return;
    setIsVerifying(true);
    try {
      await purchaseRequestService.verifyByAccounts(pendingVerify.id);
      removeFromQueue(pendingVerify.id);
      toast.success(`${pendingVerify.requisition_number} verified and sent to the General Manager`);
      setPendingVerify(null);
      closeDetail();
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to verify purchase request'));
    } finally {
      setIsVerifying(false);
    }
  };

  const handleOpenReject = () => {
    if (!selectedRequest) return;
    setPendingReject(selectedRequest);
    setRejectReason('');
  };

  const handleCancelReject = () => {
    if (isRejecting) return;
    setPendingReject(null);
    setRejectReason('');
  };

  /**
   * On failure the reason is deliberately preserved (not cleared) so the
   * reviewer doesn't have to retype it to retry - only a successful
   * rejection resets the dialog's state.
   */
  const handleConfirmReject = async () => {
    if (!pendingReject || rejectReason.trim().length === 0) return;
    setIsRejecting(true);
    try {
      await purchaseRequestService.rejectRequest(pendingReject.id, rejectReason.trim());
      removeFromQueue(pendingReject.id);
      toast.success(`${pendingReject.requisition_number} rejected`);
      setPendingReject(null);
      setRejectReason('');
      closeDetail();
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to reject purchase request'));
    } finally {
      setIsRejecting(false);
    }
  };

  // The backend blocks verification until this is true; the button just
  // mirrors that so Accounts is not offered an action that will be refused.
  const allItemsAssigned =
    !!selectedRequest &&
    selectedRequest.items.length > 0 &&
    selectedRequest.items.every((item) => item.budget_code_id !== null);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Accounts Verification"
        description="Review purchase requests awaiting Accounts verification."
      />

      <PurchaseRequestReviewList
        requests={requests}
        isLoading={isLoading}
        error={queueError}
        onRetry={loadQueue}
        onView={handleView}
      />

      <PurchaseRequestDetail
        request={selectedRequest}
        isOpen={isDetailOpen}
        onClose={closeDetail}
        isLoading={isDetailLoading}
        onEdit={() => {}}
        viewerRole="accounts"
        actions={
          selectedRequest?.status === 'PENDING_ACCOUNTS' ? (
            <div className="space-y-4">
              <PurchaseRequestBudgetCodeAssignment
                request={selectedRequest}
                budgetCodes={budgetCodeError ? [] : budgetCodes}
                loadError={budgetCodeError}
                savingItemId={savingItemId}
                onAssign={handleAssignBudgetCode}
              />
              <div className="flex items-center justify-end gap-2">
                {!allItemsAssigned && (
                  <span className="mr-auto text-xs text-muted-foreground">
                    Assign a budget code to every item to verify.
                  </span>
                )}
                <Button type="button" variant="destructive" onClick={handleOpenReject}>
                  <XCircle className="h-4 w-4 mr-1.5" />
                  Reject
                </Button>
                <Button type="button" onClick={handleOpenVerify} disabled={!allItemsAssigned}>
                  <CheckCircle className="h-4 w-4 mr-1.5" />
                  Verify
                </Button>
              </div>
            </div>
          ) : undefined
        }
      />

      <PurchaseRequestActionDialog
        requisitionNumber={pendingVerify?.requisition_number ?? null}
        isSubmitting={isVerifying}
        onConfirm={handleConfirmVerify}
        onCancel={handleCancelVerify}
        title={`Verify ${pendingVerify?.requisition_number}?`}
        description="This will send the request to the General Manager for review."
        confirmLabel="Verify"
      />

      <PurchaseRequestRejectDialog
        requisitionNumber={pendingReject?.requisition_number ?? null}
        reason={rejectReason}
        onReasonChange={setRejectReason}
        isRejecting={isRejecting}
        onConfirm={handleConfirmReject}
        onCancel={handleCancelReject}
      />
    </div>
  );
}

export default PurchaseRequestAccountsReviewPage;
