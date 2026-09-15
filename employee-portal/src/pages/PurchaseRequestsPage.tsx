import { useCallback, useEffect, useState } from 'react';
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

  const [activeTab, setActiveTab] = useState('requests');

  const [requests, setRequests] = useState<PurchaseRequestListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [bucketFilter, setBucketFilter] = useState<PurchaseRequestBucketFilter>('all');

  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

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

  const handleSubmitted = (request: PurchaseRequest) => {
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

  if (!employee) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Requests"
        description="Raise and track your purchase requisitions"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="new">New Requisition</TabsTrigger>
          <TabsTrigger value="requests">My Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="new" className="mt-4">
          <PurchaseRequestForm employee={employee} onSubmitted={handleSubmitted} />
        </TabsContent>

        <TabsContent value="requests" className="mt-4">
          <PurchaseRequestsList
            requests={requests}
            isLoading={isLoading}
            error={listError}
            onRetry={loadRequests}
            onView={handleView}
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
      />
    </div>
  );
}

export default PurchaseRequestsPage;
