import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LeaveBalances,
  LeaveRequestForm,
  LeaveRequestsList,
} from '@/components/leave';
import { leaveService } from '@/services/leave.service';
import type {
  LeaveType,
  LeaveBalance,
  LeaveRequest,
  LeaveRequestStatus,
  CreateLeaveRequestData,
} from '@/types/leave.types';

export function LeavePage() {
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [balanceSummary, setBalanceSummary] = useState<{
    total_allowed: number;
    total_used: number;
    total_remaining: number;
  } | null>(null);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<LeaveRequestStatus | 'all'>('all');
  const [activeTab, setActiveTab] = useState('balances');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadRequests();
  }, [statusFilter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [typesData, balancesData, requestsData] = await Promise.all([
        leaveService.getLeaveTypes(),
        leaveService.getBalances(),
        leaveService.getRequests(),
      ]);

      setLeaveTypes(typesData);
      setBalances(balancesData.balances);
      setBalanceSummary(balancesData.summary);
      setRequests(requestsData);
    } catch (error) {
      console.error('Failed to load leave data:', error);
      toast.error('Failed to load leave data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadRequests = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : undefined;
      const requestsData = await leaveService.getRequests(params);
      setRequests(requestsData);
    } catch (error) {
      console.error('Failed to load requests:', error);
    }
  };

  const handleSubmitRequest = async (data: CreateLeaveRequestData) => {
    setIsSubmitting(true);
    try {
      await leaveService.createRequest(data);
      toast.success('Leave request submitted successfully');

      // Refresh balances and requests
      const [balancesData, requestsData] = await Promise.all([
        leaveService.getBalances(),
        leaveService.getRequests(),
      ]);
      setBalances(balancesData.balances);
      setBalanceSummary(balancesData.summary);
      setRequests(requestsData);

      // Switch to requests tab
      setActiveTab('requests');
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to submit leave request';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelRequest = async (id: number) => {
    setCancellingId(id);
    try {
      await leaveService.cancelRequest(id);
      toast.success('Leave request cancelled');

      // Refresh balances and requests
      const [balancesData, requestsData] = await Promise.all([
        leaveService.getBalances(),
        leaveService.getRequests(
          statusFilter !== 'all' ? { status: statusFilter } : undefined
        ),
      ]);
      setBalances(balancesData.balances);
      setBalanceSummary(balancesData.summary);
      setRequests(requestsData);
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to cancel request';
      toast.error(errorMessage);
    } finally {
      setCancellingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave"
        description="Manage your leave requests and view balances"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="balances">Balances</TabsTrigger>
          <TabsTrigger value="request">New Request</TabsTrigger>
          <TabsTrigger value="requests">My Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="balances" className="mt-4">
          <LeaveBalances
            balances={balances}
            summary={balanceSummary}
            isLoading={isLoading}
          />
        </TabsContent>

        <TabsContent value="request" className="mt-4">
          <LeaveRequestForm
            leaveTypes={leaveTypes}
            balances={balances}
            onSubmit={handleSubmitRequest}
            isSubmitting={isSubmitting}
          />
        </TabsContent>

        <TabsContent value="requests" className="mt-4">
          <LeaveRequestsList
            requests={requests}
            isLoading={isLoading}
            onCancel={handleCancelRequest}
            cancellingId={cancellingId}
            onStatusFilter={setStatusFilter}
            statusFilter={statusFilter}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default LeavePage;
