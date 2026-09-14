import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, FileEdit, XCircle } from 'lucide-react';
import type { PurchaseRequestStatus } from '@/types/purchase-request.types';
import { STATUS_LABELS, statusTone } from './statusConfig';

const TONE_CLASSES: Record<string, string> = {
  gray: 'bg-gray-50 text-gray-700 border-gray-200',
  orange: 'bg-orange-50 text-orange-700 border-orange-200',
  green: 'bg-green-50 text-green-700 border-green-200',
  red: 'bg-red-50 text-red-700 border-red-200',
};

const TONE_ICON: Record<string, React.ReactNode> = {
  gray: <FileEdit className="h-3 w-3 mr-1" />,
  orange: <Clock className="h-3 w-3 mr-1" />,
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
