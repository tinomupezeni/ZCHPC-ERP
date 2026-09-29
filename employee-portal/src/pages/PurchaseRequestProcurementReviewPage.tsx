import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle, Printer } from 'lucide-react';
import { PageHeader } from '@/components/layout';
import { Button } from '@/components/ui/button';
import {
  PurchaseRequestDetail,
  PurchaseRequestReviewList,
  PurchaseRequestProcessDialog,
  type ReviewQueueError,
} from '@/components/purchase-requests';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type { PurchaseRequest, PurchaseRequestListItem } from '@/types/purchase-request.types';

/**
 * F23: the Procurement processing queue - the final workflow stage.
 *
 * Deliberately not a copy of the Approve/Reject pattern the four approval
 * stages share (F17-F22): the backend has no decline/reject path once a
 * request reaches PENDING_PROCUREMENT (the domain's reject() only recognizes
 * the four approval stages), so there is no Reject action here - inventing
 * one would be UI for a capability the backend doesn't support. The single
 * action is "Process", which requires a manually entered Purchase Order
 * number (see PurchaseRequestProcessDialog) and moves the request to
 * PROCESSED, its final state.
 */
export function PurchaseRequestProcurementReviewPage() {
  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [queueError, setQueueError] = useState<ReviewQueueError | null>(null);

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const [pendingProcess, setPendingProcess] = useState<PurchaseRequest | null>(null);
  const [purchaseOrderNumber, setPurchaseOrderNumber] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const loadQueue = useCallback(async () => {
    setIsLoading(true);
    setQueueError(null);
    try {
      const data = await purchaseRequestService.getPendingProcurementRequests();
      setRequests(data);
    } catch (error) {
      const httpStatus = (error as { response?: { status?: number } })?.response?.status;
      setQueueError(
        httpStatus === 403
          ? {
              kind: 'unauthorized',
              message: 'You do not have access to the Procurement processing queue.',
            }
          : {
              kind: 'generic',
              message: getPurchaseRequestErrorMessage(
                error,
                'Failed to load requests awaiting Procurement processing'
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

  const handleOpenProcess = () => {
    if (!selectedRequest) return;
    setPendingProcess(selectedRequest);
    setPurchaseOrderNumber('');
  };

  const handleCancelProcess = () => {
    if (isProcessing) return;
    setPendingProcess(null);
    setPurchaseOrderNumber('');
  };

  /**
   * Backend remains authoritative: the request is only removed from the
   * queue once the 200 actually comes back. A failure (e.g. a duplicate PO
   * number, 409) leaves everything exactly as it was, with an error toast,
   * and the typed PO number is preserved so the officer doesn't have to
   * retype it.
   *
   * On success the detail dialog is deliberately kept open, now showing the
   * request in its final PROCESSED state, rather than closed - this is what
   * makes the Print Requisition action (see the `actions` slot below)
   * reachable at all: a processed request immediately leaves the
   * pending-procurement queue/scope, so this is the only moment the officer
   * can get from "Process" straight to "Print" for this request.
   */
  const handleConfirmProcess = async () => {
    if (!pendingProcess || purchaseOrderNumber.trim().length === 0) return;
    setIsProcessing(true);
    try {
      const processed = await purchaseRequestService.processRequest(
        pendingProcess.id,
        purchaseOrderNumber.trim()
      );
      removeFromQueue(pendingProcess.id);
      toast.success(`${pendingProcess.requisition_number} processed`);
      setPendingProcess(null);
      setPurchaseOrderNumber('');
      setSelectedRequest(processed);
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to process purchase request'));
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Procurement Processing"
        description="Process purchase requests that have completed the approval workflow."
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
        viewerRole="procurement"
        actions={
          selectedRequest?.status === 'PENDING_PROCUREMENT' ? (
            <div className="flex justify-end gap-2">
              <Button type="button" onClick={handleOpenProcess}>
                <CheckCircle className="h-4 w-4 mr-1.5" />
                Process
              </Button>
            </div>
          ) : selectedRequest?.status === 'PROCESSED' ? (
            <div className="flex justify-end gap-2">
              <Button asChild>
                <a
                  href={`/portal/purchase-requests/${selectedRequest.id}/print`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Printer className="h-4 w-4 mr-1.5" />
                  Print Requisition
                </a>
              </Button>
            </div>
          ) : undefined
        }
      />

      <PurchaseRequestProcessDialog
        requisitionNumber={pendingProcess?.requisition_number ?? null}
        purchaseOrderNumber={purchaseOrderNumber}
        onPurchaseOrderNumberChange={setPurchaseOrderNumber}
        isProcessing={isProcessing}
        onConfirm={handleConfirmProcess}
        onCancel={handleCancelProcess}
      />
    </div>
  );
}

export default PurchaseRequestProcurementReviewPage;
