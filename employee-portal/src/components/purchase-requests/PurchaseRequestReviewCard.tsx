import { Card, CardContent } from '@/components/ui/card';
import { CalendarDays } from 'lucide-react';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';
import { PurchaseRequestStatusBadge } from './PurchaseRequestStatusBadge';
import { statusTone } from './statusConfig';

interface PurchaseRequestReviewCardProps {
  request: PurchaseRequestListItem;
  onView: (id: number) => void;
}

const ACCENT_CLASSES: Record<string, string> = {
  amber: 'border-l-4 border-l-amber-400',
  red: 'border-l-4 border-l-red-400',
};

function formatMoney(value: string): string {
  return `$${Number.parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function getSubmittedLine(request: PurchaseRequestListItem): string {
  if (!request.created_at) return 'Submitted';
  return `Submitted ${formatDistanceToNow(parseISO(request.created_at), { addSuffix: true })}`;
}

/**
 * A row in the department head's review queue (F17). Deliberately just a
 * summary - requester, department, cost, submitted-when, status - with a
 * single click-through to the shared PurchaseRequestDetail for everything
 * else; no edit/delete affordances belong here, unlike PurchaseRequestCard.
 */
export function PurchaseRequestReviewCard({ request, onView }: PurchaseRequestReviewCardProps) {
  const tone = statusTone(request.status);

  return (
    <Card
      className={cn('cursor-pointer transition-colors hover:bg-muted/40', ACCENT_CLASSES[tone])}
      role="button"
      tabIndex={0}
      onClick={() => onView(request.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onView(request.id);
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1.5 min-w-0">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold truncate">{request.requisition_number}</h3>
              <PurchaseRequestStatusBadge status={request.status} />
            </div>

            <p className="text-sm text-muted-foreground truncate">
              {request.requester_name} &middot; {request.department_name}
            </p>

            <div className="flex items-center gap-2 text-sm text-muted-foreground pt-1">
              <CalendarDays className="h-4 w-4" />
              <span>{getSubmittedLine(request)}</span>
              <span className="font-medium text-foreground ml-auto">
                {formatMoney(request.total_estimated_cost)}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PurchaseRequestReviewCard;
