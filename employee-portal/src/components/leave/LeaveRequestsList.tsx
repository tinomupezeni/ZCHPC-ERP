import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText } from 'lucide-react';
import { LeaveRequestCard } from './LeaveRequestCard';
import type { LeaveRequest, LeaveRequestStatus } from '@/types/leave.types';

interface LeaveRequestsListProps {
  requests: LeaveRequest[];
  isLoading: boolean;
  onCancel: (id: number) => Promise<void>;
  cancellingId?: number | null;
  onStatusFilter: (status: LeaveRequestStatus | 'all') => void;
  statusFilter: LeaveRequestStatus | 'all';
}

export function LeaveRequestsList({
  requests,
  isLoading,
  onCancel,
  cancellingId,
  onStatusFilter,
  statusFilter,
}: LeaveRequestsListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">My Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-muted rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="h-5 w-5" />
            My Requests
          </CardTitle>
          <Select
            value={statusFilter}
            onValueChange={(value) =>
              onStatusFilter(value as LeaveRequestStatus | 'all')
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="Pending">Pending</SelectItem>
              <SelectItem value="Approved">Approved</SelectItem>
              <SelectItem value="Rejected">Rejected</SelectItem>
              <SelectItem value="Cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {requests.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No leave requests found</p>
            <p className="text-sm">Submit a new request to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {requests.map((request) => (
              <LeaveRequestCard
                key={request.id}
                request={request}
                onCancel={onCancel}
                isCancelling={cancellingId === request.id}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default LeaveRequestsList;
