import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, FileText, RefreshCcw } from 'lucide-react';
import { PurchaseRequestCard } from './PurchaseRequestCard';
import type { PurchaseRequestListItem, PurchaseRequestStatus } from '@/types/purchase-request.types';
import { STATUS_LABELS } from './statusConfig';

interface PurchaseRequestsListProps {
  requests: PurchaseRequestListItem[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onView: (id: number) => void;
  statusFilter: PurchaseRequestStatus | 'all';
  onStatusFilterChange: (status: PurchaseRequestStatus | 'all') => void;
}

export function PurchaseRequestsList({
  requests,
  isLoading,
  error,
  onRetry,
  onView,
  statusFilter,
  onStatusFilterChange,
}: PurchaseRequestsListProps) {
  const filtered =
    statusFilter === 'all' ? requests : requests.filter((r) => r.status === statusFilter);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">My Purchase Requests</CardTitle>
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

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">My Purchase Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 space-y-3">
            <AlertCircle className="h-10 w-10 mx-auto text-destructive" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCcw className="h-4 w-4 mr-2" />
              Retry
            </Button>
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
            My Purchase Requests
          </CardTitle>
          <Select
            value={statusFilter}
            onValueChange={(value) => onStatusFilterChange(value as PurchaseRequestStatus | 'all')}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No purchase requests found</p>
            <p className="text-sm">Submit a new purchase requisition to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((request) => (
              <PurchaseRequestCard key={request.id} request={request} onView={onView} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default PurchaseRequestsList;
