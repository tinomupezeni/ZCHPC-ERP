import { Card, CardContent } from '@/components/ui/card';
import { CalendarDays } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';
import { PurchaseRequestStatusBadge } from './PurchaseRequestStatusBadge';

interface PurchaseRequestCardProps {
  request: PurchaseRequestListItem;
  onView: (id: number) => void;
}

export function PurchaseRequestCard({ request, onView }: PurchaseRequestCardProps) {
  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-muted/40"
      role="button"
      tabIndex={0}
      onClick={() => onView(request.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onView(request.id);
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2 min-w-0">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold truncate">{request.requisition_number}</h3>
              <PurchaseRequestStatusBadge status={request.status} />
            </div>

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              <span>
                {request.created_at
                  ? format(parseISO(request.created_at), 'MMM d, yyyy')
                  : 'Date unavailable'}
              </span>
              <span className="font-medium text-foreground">
                $
                {Number.parseFloat(request.total_estimated_cost).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
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
