import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import {
  PurchaseRequestForm,
  PurchaseRequestsList,
  PurchaseRequestDetail,
} from '@/components/purchase-requests';
import type { PurchaseRequestBucketFilter } from '@/components/purchase-requests/PurchaseRequestsList';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type { PurchaseRequest, PurchaseRequestListItem } from '@/types/purchase-request.types';

export function PurchaseRequestsPage() {
  const { employee } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [activeTab, setActiveTab] = useState('requests');

  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [bucketFilter, setBucketFilter] = useState<PurchaseRequestBucketFilter>('all');

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  // Slice 2: the DRAFT/REJECTED request currently open for editing, if any.
  // null means the "New Requisition" tab is a fresh, blank create form.
  const [editingRequest, setEditingRequest] = useState<PurchaseRequest | null>(null);

  const loadRequests = useCallback(async () => {
    setIsLoading(true);
    setListError(null);
    try {
      const data = await purchaseRequestService.getMyRequests();
      setRequests(data);
    } catch (error) {
      setListError(
        getPurchaseRequestErrorMessage(error, 'Failed to load your purchase requests')
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const handleCreateSubmitted = (request: PurchaseRequest) => {
    setRequests((prev) => [
      {
        id: request.id,
        requisition_number: request.requisition_number,
        requester_id: request.requester_id,
        requester_name: request.requester_name,
        department_id: request.department_id,
        department_name: request.department_name,
        status: request.status,
        total_estimated_cost: request.total_estimated_cost,
        created_at: request.created_at,
        updated_at: request.updated_at,
      },
      ...prev,
    ]);
    setActiveTab('requests');
    loadRequests();
  };

  /** Slice 2: a save or a submit from the edit form - both return to "My Requests". */
  const handleEditFinished = () => {
    setEditingRequest(null);
    setActiveTab('requests');
    loadRequests();
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

  /** Slice 2: "Continue Editing" (DRAFT) / "Review & Correct" (REJECTED), from either the list or the detail dialog. */
  const handleEdit = async (id: number) => {
    setIsDetailOpen(false);
    try {
      const detail = await purchaseRequestService.getRequest(id);
      setEditingRequest(detail);
      setActiveTab('new');
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to load purchase request'));
    }
  };

  /**
   * Slice 3: a notification (rejected -> edit, processed -> view) links here
   * as /portal/purchase-requests?requestId=<id>&action=<edit|view>. Handled
   * once, then the params are cleared so refreshing or navigating back to
   * this page doesn't re-trigger the same deep link.
   */
  useEffect(() => {
    const requestId = Number(searchParams.get('requestId'));
    if (!requestId) return;

    if (searchParams.get('action') === 'edit') {
      handleEdit(requestId);
    } else {
      handleView(requestId);
    }
    setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handleTabChange = (tab: string) => {
    if (tab === 'new') {
      // Choosing "New Requisition" directly always starts a fresh request.
      setEditingRequest(null);
    }
    setActiveTab(tab);
  };

  if (!employee) {
    return null;
  }

  const newTabLabel = editingRequest
    ? editingRequest.status === 'REJECTED'
      ? 'Review & Correct'
      : 'Continue Editing'
    : 'New Requisition';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Requests"
        description="Raise and track your purchase requisitions"
      />

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="new">{newTabLabel}</TabsTrigger>
          <TabsTrigger value="requests">My Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="new" className="mt-4">
          <PurchaseRequestForm
            key={editingRequest?.id ?? 'new'}
            employee={employee}
            mode={editingRequest ? 'edit' : 'create'}
            existingRequest={editingRequest ?? undefined}
            onSubmitted={editingRequest ? handleEditFinished : handleCreateSubmitted}
            onSaved={editingRequest ? handleEditFinished : handleCreateSubmitted}
          />
        </TabsContent>

        <TabsContent value="requests" className="mt-4">
          <PurchaseRequestsList
            requests={requests}
            isLoading={isLoading}
            error={listError}
            onRetry={loadRequests}
            onView={handleView}
            onEdit={handleEdit}
            bucketFilter={bucketFilter}
            onBucketFilterChange={setBucketFilter}
          />
        </TabsContent>
      </Tabs>

      <PurchaseRequestDetail
        request={selectedRequest}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        isLoading={isDetailLoading}
        onEdit={handleEdit}
      />
    </div>
  );
}

export default PurchaseRequestsPage;
