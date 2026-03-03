import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CalendarDays,
  Clock,
  X,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import type { LeaveRequest, LeaveRequestStatus } from '@/types/leave.types';

interface LeaveRequestCardProps {
  request: LeaveRequest;
  onCancel?: (id: number) => Promise<void>;
  isCancelling?: boolean;
}

export function LeaveRequestCard({
  request,
  onCancel,
  isCancelling,
}: LeaveRequestCardProps) {
  const getStatusBadge = (status: LeaveRequestStatus) => {
    switch (status) {
      case 'Pending':
        return (
          <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
            <Clock className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        );
      case 'Approved':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        );
      case 'Rejected':
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        );
      case 'Cancelled':
        return (
          <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
            <AlertCircle className="h-3 w-3 mr-1" />
            Cancelled
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            {/* Header: Leave Type and Status */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="font-semibold">{request.leave_type_name}</h3>
              {getStatusBadge(request.status)}
            </div>

            {/* Date Range */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              <span>
                {format(parseISO(request.start_date), 'MMM d, yyyy')}
                {request.start_date !== request.end_date && (
                  <> - {format(parseISO(request.end_date), 'MMM d, yyyy')}</>
                )}
              </span>
              <span className="font-medium text-foreground">
                ({request.number_of_days} day{request.number_of_days !== 1 ? 's' : ''})
              </span>
            </div>

            {/* Reason */}
            {request.reason && (
              <p className="text-sm text-muted-foreground line-clamp-2">
                {request.reason}
              </p>
            )}

            {/* Meta Info */}
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span>
                Requested: {format(parseISO(request.requested_on), 'MMM d, yyyy')}
              </span>
              {request.reviewed_by_name && request.review_date && (
                <span>
                  Reviewed by {request.reviewed_by_name} on{' '}
                  {format(parseISO(request.review_date), 'MMM d, yyyy')}
                </span>
              )}
            </div>
          </div>

          {/* Cancel Button */}
          {request.can_cancel && onCancel && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => onCancel(request.id)}
              disabled={isCancelling}
            >
              {isCancelling ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <X className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default LeaveRequestCard;
