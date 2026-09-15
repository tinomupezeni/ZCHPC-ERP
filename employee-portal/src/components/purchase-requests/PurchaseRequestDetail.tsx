import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle, Clock, FileEdit, FileText, MinusCircle, XCircle } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';
import type {
  PurchaseRequest,
  PurchaseRequestDecisionStage,
  PurchaseRequestStatus,
} from '@/types/purchase-request.types';
import { PurchaseRequestStatusBadge } from './PurchaseRequestStatusBadge';
import {
  APPROVAL_STAGES,
  STATUS_LABELS,
  STATUS_MESSAGES,
  decisionLabel,
  findRejection,
  getProgressLabel,
  getStageInfo,
  getWaitingHelperLine,
  statusTone,
  type StatusBadgeTone,
} from './statusConfig';

interface PurchaseRequestDetailProps {
  request: PurchaseRequest | null;
  isOpen: boolean;
  onClose: () => void;
  isLoading?: boolean;
}

function formatMoney(value: string): string {
  return `$${Number.parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value: string | null): string {
  if (!value) return '—';
  return format(parseISO(value), 'MMM d, yyyy h:mm a');
}

const HERO_CLASSES: Record<StatusBadgeTone, string> = {
  amber: 'border-amber-200 bg-amber-50 text-amber-900',
  red: 'border-red-200 bg-red-50 text-red-900',
  slate: 'border-slate-200 bg-slate-50 text-slate-700',
  green: 'border-green-200 bg-green-50 text-green-900',
};

const HERO_ICON: Record<StatusBadgeTone, React.ComponentType<{ className?: string }>> = {
  amber: FileEdit,
  red: XCircle,
  slate: Clock,
  green: CheckCircle,
};

/**
 * The employee-facing status "hero": what this request's state means and
 * whether anything is expected of the employee, ahead of the detailed
 * sections below. Subsumes what used to be a REJECTED-only alert card -
 * every status now gets an equivalent, appropriately-toned block.
 *
 * No CTA is rendered here by design (F13 Slice 1: presentation only - draft
 * and rejected-request editing are separate, not-yet-implemented slices).
 */
function StatusHero({ request }: { request: PurchaseRequest }) {
  const tone = statusTone(request.status);
  const Icon = HERO_ICON[tone];
  const rejection = findRejection(request);
  const progress = getProgressLabel(request.status);
  const waitingHelperLine = getWaitingHelperLine(request.status);

  return (
    <div className={cn('rounded-lg border p-4 flex items-start gap-3', HERO_CLASSES[tone])}>
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="space-y-1">
        <p className="font-semibold">{STATUS_LABELS[request.status]}</p>
        <p className="text-sm">
          {rejection ? rejection.reason || STATUS_MESSAGES.REJECTED : STATUS_MESSAGES[request.status]}
        </p>
        {waitingHelperLine && <p className="text-sm">{waitingHelperLine}</p>}
        {progress && <p className="text-xs opacity-75">{progress}</p>}
      </div>
    </div>
  );
}

function StageRow({
  stage,
  label,
  request,
}: {
  stage: PurchaseRequestDecisionStage;
  label: string;
  request: PurchaseRequest;
}) {
  const info = getStageInfo(stage, request);

  let icon = <Clock className="h-4 w-4 text-orange-500" />;
  let text = 'Pending';
  let sub: string | null = null;

  if (info.kind === 'decided') {
    const isRejected = info.decision.decision === 'REJECTED';
    icon = isRejected ? (
      <XCircle className="h-4 w-4 text-red-600" />
    ) : (
      <CheckCircle className="h-4 w-4 text-green-600" />
    );
    text = decisionLabel(info.decision);
    sub = formatDate(info.decision.created_at);
  } else if (info.kind === 'not_reached') {
    icon = <MinusCircle className="h-4 w-4 text-muted-foreground" />;
    text = 'Not Reached';
  } else if (info.kind === 'not_submitted') {
    icon = <MinusCircle className="h-4 w-4 text-muted-foreground" />;
    text = 'Not Submitted';
  }

  return (
    <div className="flex items-center justify-between py-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="flex items-center gap-2 font-medium">
        {icon}
        {text}
        {sub && <span className="text-xs text-muted-foreground font-normal">({sub})</span>}
      </span>
    </div>
  );
}

function procurementStatusLabel(status: PurchaseRequestStatus): string {
  return status === 'PROCESSED' ? 'Completed' : 'Being Processed';
}

export function PurchaseRequestDetail({
  request,
  isOpen,
  onClose,
  isLoading,
}: PurchaseRequestDetailProps) {
  if (!request && !isLoading) return null;

  const showProcurement =
    request && (request.status === 'PENDING_PROCUREMENT' || request.status === 'PROCESSED');

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <DialogTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {request ? request.requisition_number : 'Purchase Request'}
              </DialogTitle>
            </div>
            {request && <PurchaseRequestStatusBadge status={request.status} />}
          </div>
        </DialogHeader>

        {isLoading || !request ? (
          <div className="animate-pulse space-y-4 py-6">
            <div className="h-4 bg-muted rounded w-1/2"></div>
            <div className="h-24 bg-muted rounded"></div>
          </div>
        ) : (
          <ScrollArea className="flex-1 min-h-0">
            <div className="space-y-4 pr-4">
              <StatusHero request={request} />

              {/* Section A: Requester */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Requester Details</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">Requested By</p>
                    <p className="font-medium">{request.requester_name}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Designation</p>
                    <p className="font-medium">{request.designation || '—'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Contact</p>
                    <p className="font-medium">{request.contact || '—'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Department</p>
                    <p className="font-medium">{request.department_name}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Section B: Items */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Item(s) Requested</h4>
                <div className="space-y-2">
                  {request.items.map((item) => (
                    <div key={item.id} className="rounded-lg border p-3 text-sm space-y-1">
                      <p className="font-medium">{item.description}</p>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <span>Qty: {item.quantity}</span>
                        <span>Delivery: {item.expected_delivery_period}</span>
                        <span>Cost: {formatMoney(item.estimated_cost)}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between mt-3 p-3 bg-muted/50 rounded-lg">
                  <span className="font-medium text-sm">Total Estimated Cost</span>
                  <span className="text-lg font-semibold">
                    {formatMoney(request.total_estimated_cost)}
                  </span>
                </div>
              </div>

              <Separator />

              {/* Section C: Approvals (read-only) */}
              <div>
                <h4 className="text-sm font-semibold mb-1">Approval Workflow</h4>
                <div className="divide-y">
                  {APPROVAL_STAGES.map(({ stage, label }) => (
                    <StageRow key={stage} stage={stage} label={label} request={request} />
                  ))}
                </div>
              </div>

              {/* Section D: Procurement, only if actually returned */}
              {showProcurement && (
                <>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-semibold mb-1">Procurement</h4>
                    <div className="flex items-center justify-between py-1 text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <span className="font-medium">{procurementStatusLabel(request.status)}</span>
                    </div>
                    {request.processed_at && (
                      <div className="flex items-center justify-between py-1 text-sm">
                        <span className="text-muted-foreground">Date Processed</span>
                        <span className="font-medium">{formatDate(request.processed_at)}</span>
                      </div>
                    )}
                  </div>
                </>
              )}

              <p className="text-xs text-muted-foreground pt-2">
                Created {formatDate(request.created_at)}
                {request.updated_at && request.updated_at !== request.created_at && (
                  <> · Updated {formatDate(request.updated_at)}</>
                )}
              </p>
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestDetail;
