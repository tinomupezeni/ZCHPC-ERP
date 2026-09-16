import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { CheckCircle, XCircle } from 'lucide-react';
import { PageHeader } from '@/components/layout';
import { Button } from '@/components/ui/button';
import {
  PurchaseRequestDetail,
  PurchaseRequestReviewList,
  PurchaseRequestApproveDialog,
  PurchaseRequestRejectDialog,
  type ReviewQueueError,
} from '@/components/purchase-requests';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type { PurchaseRequest, PurchaseRequestListItem } from '@/types/purchase-request.types';

/**
 * F17: the department head's review queue. Structurally deliberate mirror of
 * PurchaseRequestsPage (own queue state, own detail state, backend-
 * authoritative removal only on confirmed success) so the same shape can
 * naturally be reused for Accounts/GM/Director later without inventing a
 * generic workflow engine now.
 */
export function PurchaseRequestReviewPage() {
  const [searchParams, setSearchParams] = useSearchParams();

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
      const data = await purchaseRequestService.getPendingDepartmentHeadRequests();
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
              message: 'You do not have access to the department-head review queue.',
            }
          : {
              kind: 'generic',
              message: getPurchaseRequestErrorMessage(
                error,
                'Failed to load requests awaiting your review'
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

  /**
   * F19: a "Purchase Request Corrected" notification links here as
   * /portal/purchase-requests/review?requestId=<id>&action=view - the same
   * requestId/action query-param convention PurchaseRequestsPage already
   * uses for the requester-facing notifications. This page only ever opens
   * the read-only detail (there is no edit mode here), so action is read for
   * consistency but not otherwise branched on. Handled once, then the
   * params are cleared so refreshing or navigating back doesn't re-trigger
   * the same deep link.
   */
  useEffect(() => {
    const requestId = Number(searchParams.get('requestId'));
    if (!requestId) return;

    handleView(requestId);
    setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

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
      await purchaseRequestService.approveByDepartmentHead(pendingApprove.id);
      removeFromQueue(pendingApprove.id);
      toast.success(`${pendingApprove.requisition_number} approved and sent to Accounts`);
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
        title="Purchase Request Review"
        description="Requests submitted to you for department-head review"
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
        viewerRole="department_head"
        actions={
          selectedRequest?.status === 'PENDING_DEPARTMENT_HEAD' ? (
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

      <PurchaseRequestApproveDialog
        requisitionNumber={pendingApprove?.requisition_number ?? null}
        isApproving={isApproving}
        onConfirm={handleConfirmApprove}
        onCancel={handleCancelApprove}
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

export default PurchaseRequestReviewPage;
