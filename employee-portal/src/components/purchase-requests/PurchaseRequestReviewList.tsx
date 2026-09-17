import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, FileText, RefreshCcw, ShieldAlert } from 'lucide-react';
import { PurchaseRequestReviewCard } from './PurchaseRequestReviewCard';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';

/**
 * A 403 from the queue endpoint (no department-head authority at all) must
 * never be presented the same way as a genuinely empty queue - see
 * PurchaseRequestReviewPage.loadQueue, which is the only place this is set.
 */
export interface ReviewQueueError {
  kind: 'unauthorized' | 'generic';
  message: string;
}

interface PurchaseRequestReviewListProps {
  requests: PurchaseRequestListItem[];
  isLoading: boolean;
  error: ReviewQueueError | null;
  onRetry: () => void;
  onView: (id: number) => void;
}

export function PurchaseRequestReviewList({
  requests,
  isLoading,
  error,
  onRetry,
  onView,
}: PurchaseRequestReviewListProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Pending Requests</CardTitle>
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

  if (error?.kind === 'unauthorized') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Pending Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 space-y-3">
            <ShieldAlert className="h-10 w-10 mx-auto text-muted-foreground" />
            <p className="text-sm font-medium">You don't have access to this queue</p>
            <p className="text-sm text-muted-foreground">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Pending Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 space-y-3">
            <AlertCircle className="h-10 w-10 mx-auto text-destructive" />
            <p className="text-sm text-muted-foreground">{error.message}</p>
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
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Pending Requests
        </CardTitle>
      </CardHeader>
      <CardContent>
        {requests.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No requests waiting for your review.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {requests.map((request) => (
              <PurchaseRequestReviewCard key={request.id} request={request} onView={onView} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default PurchaseRequestReviewList;
