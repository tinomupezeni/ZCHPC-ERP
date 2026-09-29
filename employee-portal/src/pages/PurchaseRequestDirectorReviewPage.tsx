import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle, XCircle } from 'lucide-react';
import { PageHeader } from '@/components/layout';
import { Button } from '@/components/ui/button';
import {
  PurchaseRequestDetail,
  PurchaseRequestReviewList,
  PurchaseRequestActionDialog,
  PurchaseRequestRejectDialog,
  type ReviewQueueError,
} from '@/components/purchase-requests';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type { PurchaseRequest, PurchaseRequestListItem } from '@/types/purchase-request.types';

/**
 * F22: the Director approval queue. A deliberate copy/adapt of
 * PurchaseRequestGMReviewPage (F21) - confirmed by backend investigation to
 * behave identically in shape (organization-wide authorization via
 * authorize_director_approval, no department scoping, same generic reject
 * endpoint, no domain event/notification), with only the service methods,
 * page copy, and the action dialog's stage-specific wording actually
 * differing. See F17/F18's own investigation reports for why this stays a
 * copy/adapt rather than a shared "ReviewPageFactory" abstraction.
 */
export function PurchaseRequestDirectorReviewPage() {
  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [queueError, setQueueError] = useState<ReviewQueueError | null>(null);

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const [pendingApprove, setPendingApprove] = useState<PurchaseRequest | null>(null);
  const [isApproving, setIsApproving] = useState(false);

  const [pendingReject, setPendingReject] = useState<PurchaseRequest | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setQueueError(null);
    try {
      const data = await purchaseRequestService.getPendingDirectorRequests();
      setRequests(data);
    } catch (error) {
      const httpStatus = (error as { response?: { status?: number } })?.response?.status;
      setQueueError(
        httpStatus === 403
          ? {
              kind: 'unauthorized',
              // F20 follow-up convention: shown as-is to the employee, so
              // this must stay human-facing - never the backend's raw
              // permission identifier (e.g. "Missing required permission
              // '...'"), which getPurchaseRequestErrorMessage would
              // otherwise surface here since the backend's 403 body does
              // carry one.
              message: 'You do not have access to the Director approval queue.',
            }
          : {
              kind: 'generic',
              message: getPurchaseRequestErrorMessage(
                error,
                'Failed to load requests awaiting Director approval'
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
    } catch (error) {
      setIsDetailOpen(false);
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to load purchase request'));
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleOpenApprove = () => {
    if (!selectedRequest) return;
    setPendingApprove(selectedRequest);
  };

  const handleCancelApprove = () => {
    if (isApproving) return;
    setPendingApprove(null);
  };

  /**
   * Backend remains authoritative: the request is only removed from the
   * queue and the detail view only closes once the 200 actually comes back.
   * A failure leaves everything exactly as it was, with an error toast.
   */
  const handleConfirmApprove = async () => {
    if (!pendingApprove) return;
    setIsApproving(true);
    try {
      await purchaseRequestService.approveByDirector(pendingApprove.id);
      removeFromQueue(pendingApprove.id);
      toast.success(`${pendingApprove.requisition_number} approved and sent to Procurement`);
      setPendingApprove(null);
      closeDetail();
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to approve purchase request'));
    } finally {
      setIsApproving(false);
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Director Approval"
        description="Review purchase requests awaiting Director approval."
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
        viewerRole="director"
        actions={
          selectedRequest?.status === 'PENDING_DIRECTOR' ? (
            <div className="flex justify-end gap-2">
              <Button type="button" variant="destructive" onClick={handleOpenReject}>
                <XCircle className="h-4 w-4 mr-1.5" />
                Reject
              </Button>
              <Button type="button" onClick={handleOpenApprove}>
                <CheckCircle className="h-4 w-4 mr-1.5" />
                Approve
              </Button>
            </div>
          ) : undefined
        }
      />

      {/*
        No custom title is passed here: the dialog's own default title is
        `${DEFAULT_CONFIRM_LABEL} ${requisitionNumber}?` = "Approve
        PR-0042?" - since confirmLabel is also "Approve" (the same default
        Department Head's own dialog uses), that default already matches
        this stage's own wording exactly. Only the description actually
        needs to change, matching the established per-stage convention
        (Accounts/GM likewise only override description + confirmLabel).
      */}
      <PurchaseRequestActionDialog
        requisitionNumber={pendingApprove?.requisition_number ?? null}
        isSubmitting={isApproving}
        onConfirm={handleConfirmApprove}
        onCancel={handleCancelApprove}
        description="Approving this request will send it to Procurement for processing."
        confirmLabel="Approve"
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

export default PurchaseRequestDirectorReviewPage;
