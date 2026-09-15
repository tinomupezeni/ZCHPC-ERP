import { Card, CardContent } from '@/components/ui/card';
import { CalendarDays } from 'lucide-react';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';
import { PurchaseRequestStatusBadge } from './PurchaseRequestStatusBadge';
import { STATUS_MESSAGES, getWaitingHelperLine, statusTone } from './statusConfig';

interface PurchaseRequestCardProps {
  request: PurchaseRequestListItem;
  onView: (id: number) => void;
}

const ACCENT_CLASSES: Record<string, string> = {
  amber: 'border-l-4 border-l-amber-400',
  red: 'border-l-4 border-l-red-400',
};

const MESSAGE_CLASSES: Record<string, string> = {
  amber: 'text-amber-800',
  red: 'text-red-700',
  slate: 'text-muted-foreground',
  green: 'text-muted-foreground',
};

function formatMoney(value: string): string {
  return `$${Number.parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * The list endpoint (PurchaseRequestListSerializer) doesn't return
 * processed_at - only the full detail does. For a PROCESSED request,
 * updated_at is an accurate stand-in: the domain has no further mutations
 * once PROCESSED, so the last update *is* the moment it was processed.
 */
function getDateLine(request: PurchaseRequestListItem): string {
  if (request.status === 'PROCESSED') {
    const date = request.updated_at ?? request.created_at;
    return date ? `Processed ${format(parseISO(date), 'd MMMM yyyy')}` : 'Processed';
  }
  const prefix = request.status === 'DRAFT' ? 'Saved' : 'Submitted';
  if (!request.created_at) return prefix;
  return `${prefix} ${formatDistanceToNow(parseISO(request.created_at), { addSuffix: true })}`;
}

export function PurchaseRequestCard({ request, onView }: PurchaseRequestCardProps) {
  const tone = statusTone(request.status);
  const waitingHelperLine = getWaitingHelperLine(request.status);

  return (
    <Card
      className={cn(
        'cursor-pointer transition-colors hover:bg-muted/40',
        ACCENT_CLASSES[tone]
      )}
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

            <p className={cn('text-sm', MESSAGE_CLASSES[tone])}>
              {STATUS_MESSAGES[request.status]}
            </p>
            {waitingHelperLine && (
              <p className="text-xs text-muted-foreground">{waitingHelperLine}</p>
            )}

            <div className="flex items-center gap-2 text-sm text-muted-foreground pt-1">
              <CalendarDays className="h-4 w-4" />
              <span>{getDateLine(request)}</span>
              <span className="font-medium text-foreground ml-auto">
                {formatMoney(request.total_estimated_cost)}
              </span>
            </div>

            <p className="text-xs text-muted-foreground">{request.department_name}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default PurchaseRequestCard;
