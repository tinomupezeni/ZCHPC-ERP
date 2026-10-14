import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Clock, XCircle } from 'lucide-react';

interface RequisitionStatusBadgeProps {
  status: string;
  labels?: Record<string, string>;
}

const DEFAULT_LABELS: Record<string, string> = {
  PENDING_DEPARTMENT: 'Awaiting Department Head',
  PENDING_RECIPIENT: 'Awaiting Recipient / Driver',
  PENDING_PROCUREMENT: 'Awaiting Procurement / Stores',
  PENDING_ACCOUNTS: 'Awaiting Accounts / Finance',
  PENDING_FINANCE: 'Awaiting Finance / GM',
  PENDING_GENERAL_MANAGER: 'Awaiting General Manager',
  PENDING_DIRECTOR: 'Awaiting Director',
  PENDING_ADMIN: 'Awaiting Administration',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
};

export function RequisitionStatusBadge({ status, labels }: RequisitionStatusBadgeProps) {
  const displayLabel = labels?.[status] || DEFAULT_LABELS[status] || status;

  if (status === 'APPROVED') {
    return (
      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 gap-1 font-medium">
        <CheckCircle2 className="h-3.5 w-3.5" />
        {displayLabel}
      </Badge>
    );
  }

  if (status === 'REJECTED') {
    return (
      <Badge variant="outline" className="bg-rose-50 text-rose-700 border-rose-200 gap-1 font-medium">
        <XCircle className="h-3.5 w-3.5" />
        {displayLabel}
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 gap-1 font-medium">
      <Clock className="h-3.5 w-3.5" />
      {displayLabel}
    </Badge>
  );
}

export default RequisitionStatusBadge;

