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
 * F21: the GM recommendation queue. A deliberate copy/adapt of
 * PurchaseRequestAccountsReviewPage (F18) - confirmed by backend
 * investigation to behave identically in shape (organization-wide
 * authorization, no department scoping, same generic reject endpoint), with
 * only the service methods, page copy, and the action dialog's stage-
 * specific wording actually differing. See F17/F18's own investigation
 * reports for why this stays a copy/adapt rather than a shared
 * "ReviewPageFactory" abstraction.
 */
export function PurchaseRequestGMReviewPage() {
  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [queueError, setQueueError] = useState<ReviewQueueError | null>(null);

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const [pendingRecommend, setPendingRecommend] = useState<PurchaseRequest | null>(null);
  const [isRecommending, setIsRecommending] = useState(false);

  const [pendingReject, setPendingReject] = useState<PurchaseRequest | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [isRejecting, setIsRejecting] = useState(false);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setQueueError(null);
    try {
      const data = await purchaseRequestService.getPendingGMRequests();
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
              message: 'You do not have access to the GM recommendation queue.',
            }
          : {
              kind: 'generic',
              message: getPurchaseRequestErrorMessage(
                error,
                'Failed to load requests awaiting GM recommendation'
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

  const handleOpenRecommend = () => {
    if (!selectedRequest) return;
    setPendingRecommend(selectedRequest);
  };

  const handleCancelRecommend = () => {
    if (isRecommending) return;
    setPendingRecommend(null);
  };

  /**
   * Backend remains authoritative: the request is only removed from the
   * queue and the detail view only closes once the 200 actually comes back.
   * A failure leaves everything exactly as it was, with an error toast.
   */
  const handleConfirmRecommend = async () => {
    if (!pendingRecommend) return;
    setIsRecommending(true);
    try {
      await purchaseRequestService.recommendByGM(pendingRecommend.id);
      removeFromQueue(pendingRecommend.id);
      toast.success(`${pendingRecommend.requisition_number} recommended and sent to the Director`);
      setPendingRecommend(null);
      closeDetail();
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to recommend purchase request'));
    } finally {
      setIsRecommending(false);
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
        title="GM Recommendation"
        description="Review purchase requests awaiting GM recommendation."
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
        viewerRole="gm"
        actions={
          selectedRequest?.status === 'PENDING_GM' ? (
            <div className="flex justify-end gap-2">
              <Button type="button" variant="destructive" onClick={handleOpenReject}>
                <XCircle className="h-4 w-4 mr-1.5" />
                Reject
              </Button>
              <Button type="button" onClick={handleOpenRecommend}>
                <CheckCircle className="h-4 w-4 mr-1.5" />
                Recommend
              </Button>
            </div>
          ) : undefined
        }
      />

      <PurchaseRequestActionDialog
        requisitionNumber={pendingRecommend?.requisition_number ?? null}
        isSubmitting={isRecommending}
        onConfirm={handleConfirmRecommend}
        onCancel={handleCancelRecommend}
        title={`Recommend ${pendingRecommend?.requisition_number}?`}
        description="This will send the request to the Director for review."
        confirmLabel="Recommend"
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

export default PurchaseRequestGMReviewPage;
