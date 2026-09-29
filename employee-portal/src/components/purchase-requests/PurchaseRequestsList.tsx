import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, FileText, RefreshCcw } from 'lucide-react';
import { PurchaseRequestCard } from './PurchaseRequestCard';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';
import { type ActionBucket, getActionBucket, isActionRequired } from './statusConfig';

/**
 * "all" plus the three UI-derived buckets from statusConfig. This replaces
 * the previous per-status (PENDING_GM, etc.) filter dropdown - keeping both
 * would mean two competing, sometimes-contradictory filters, and the
 * granular one directly contradicted this slice's goal of not exposing
 * workflow terminology. Nothing is lost: within "Waiting", each card's own
 * badge already shows which of the five stages it's at.
 */
export type PurchaseRequestBucketFilter = ActionBucket | 'all';

interface PurchaseRequestsListProps {
  requests: PurchaseRequestListItem[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onView: (id: number) => void;
  /** Slice 2: opens the edit form for a DRAFT/REJECTED request. */
  onEdit: (id: number) => void;
  /** Slice 4: asks to delete a DRAFT request. */
  onDelete: (id: number) => void;
  bucketFilter: PurchaseRequestBucketFilter;
  onBucketFilterChange: (bucket: PurchaseRequestBucketFilter) => void;
}

const BUCKET_OPTIONS: { value: PurchaseRequestBucketFilter; label: string }[] = [
  { value: 'needs_action', label: 'Needs Action' },
  { value: 'waiting', label: 'Waiting' },
  { value: 'completed', label: 'Completed' },
  { value: 'all', label: 'All' },
];

export function PurchaseRequestsList({
  requests,
  isLoading,
  error,
  onRetry,
  onView,
  onEdit,
  onDelete,
  bucketFilter,
  onBucketFilterChange,
}: PurchaseRequestsListProps) {
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

  const needsActionCount = requests.filter((r) => isActionRequired(r.status)).length;
  const bucketCounts: Record<PurchaseRequestBucketFilter, number> = {
    needs_action: needsActionCount,
    waiting: requests.filter((r) => getActionBucket(r.status) === 'waiting').length,
    completed: requests.filter((r) => getActionBucket(r.status) === 'completed').length,
    all: requests.length,
  };

  const filtered =
    bucketFilter === 'all'
      ? requests
      : requests.filter((r) => getActionBucket(r.status) === bucketFilter);

  return (
    <div className="space-y-4">
      {needsActionCount > 0 && (
        <button
          type="button"
          onClick={() => onBucketFilterChange('needs_action')}
          className="w-full flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 text-left hover:bg-amber-100 transition-colors"
        >
          <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0" />
          <span>
            You have <strong>{needsActionCount}</strong> request
            {needsActionCount === 1 ? '' : 's'} that need
            {needsActionCount === 1 ? 's' : ''} your attention.
          </span>
        </button>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5" />
              My Purchase Requests
            </CardTitle>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
              {BUCKET_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  size="sm"
                  variant={bucketFilter === option.value ? 'default' : 'outline'}
                  onClick={() => onBucketFilterChange(option.value)}
                  aria-pressed={bucketFilter === option.value}
                >
                  {option.label} ({bucketCounts[option.value]})
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filtered.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
              {requests.length === 0 ? (
                <>
                  <p>No purchase requests found</p>
                  <p className="text-sm">Submit a new purchase requisition to get started</p>
                </>
              ) : (
                <>
                  <p>No requests in this view</p>
                  <p className="text-sm">Try a different filter above</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map((request) => (
                <PurchaseRequestCard
                  key={request.id}
                  request={request}
                  onView={onView}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default PurchaseRequestsList;
