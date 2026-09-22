import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, FileEdit, XCircle } from 'lucide-react';
import type { PurchaseRequestStatus } from '@/types/purchase-request.types';
import { STATUS_LABELS, statusTone, type StatusBadgeTone } from './statusConfig';

const TONE_CLASSES: Record<StatusBadgeTone, string> = {
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  slate: 'bg-slate-100 text-slate-600 border-slate-300',
  green: 'bg-green-50 text-green-700 border-green-200',
  red: 'bg-red-50 text-red-700 border-red-200',
};

const TONE_ICON: Record<StatusBadgeTone, React.ReactNode> = {
  amber: <FileEdit className="h-3 w-3 mr-1" />,
  slate: <Clock className="h-3 w-3 mr-1" />,
  green: <CheckCircle className="h-3 w-3 mr-1" />,
  red: <XCircle className="h-3 w-3 mr-1" />,
};

export function PurchaseRequestStatusBadge({ status }: { status: PurchaseRequestStatus }) {
  const tone = statusTone(status);
  return (
    <Badge variant="outline" className={TONE_CLASSES[tone]}>
      {TONE_ICON[tone]}
      {STATUS_LABELS[status]}
    </Badge>
  );
}

export default PurchaseRequestStatusBadge;
