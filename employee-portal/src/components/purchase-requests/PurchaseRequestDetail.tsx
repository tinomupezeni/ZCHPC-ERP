import type { ReactNode } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { DocumentSection, DocumentField, DocumentFieldGrid } from '@/components/documents';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileEdit,
  MinusCircle,
  Pencil,
  XCircle,
} from 'lucide-react';
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
  getEditCtaLabel,
  getProgressLabel,
  getStageInfo,
  getStatusHeroLabel,
  getStatusHeroMessage,
  getSupersededRejection,
  getWaitingHelperLine,
  hasCorrectionHistory,
  isCorrectedResubmission,
  stageLabel,
  statusTone,
  type PurchaseRequestViewerRole,
  type StatusBadgeTone,
} from './statusConfig';

interface PurchaseRequestDetailProps {
  request: PurchaseRequest | null;
  isOpen: boolean;
  onClose: () => void;
  isLoading?: boolean;
  /** Slice 2: opens the edit form for this request. Only called for DRAFT/REJECTED. */
  onEdit: (id: number) => void;
  /**
   * F17: an optional footer area for caller-owned controls (e.g. the
   * Department Head review page's Approve/Reject buttons). This component
   * stays role-agnostic - it has no idea what the slot contains or when it
   * should be shown; that decision belongs entirely to whichever page passes
   * it in.
   */
  actions?: ReactNode;
  /**
   * F19/F20: whose perspective the status hero's copy should be written
   * from. Defaults to 'requester' so every existing caller
   * (PurchaseRequestsPage) keeps its current wording unchanged; each review
   * page passes its own role (see statusConfig's PurchaseRequestViewerRole).
   */
  viewerRole?: PurchaseRequestViewerRole;
}

function formatMoney(value: number | string): string {
  const amount = typeof value === 'number' ? value : Number.parseFloat(value);
  return `$${amount.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * estimated_cost is a per-unit price (see PurchaseRequestItemsForm) - this
 * request's own total_estimated_cost is server-computed as the sum of these
 * per-line totals, so the per-item breakdown here must use the same
 * quantity x unit cost math rather than showing the raw unit cost alone.
 * Cents-based to avoid float rounding artifacts, matching draftItem.ts.
 */
function lineTotal(item: { quantity: number; estimated_cost: string }): number {
  const unitCostCents = Math.round(Number.parseFloat(item.estimated_cost) * 100);
  return (unitCostCents * item.quantity) / 100;
}

function formatDate(value: string | null): string {
  if (!value) return '—';
  return format(parseISO(value), 'MMM d, yyyy h:mm a');
}

function formatShortDate(value: string | null): string {
  if (!value) return '—';
  return format(parseISO(value), 'MMM d, yyyy');
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
 * The document's current-state "hero": what this request's state means and
 * whether anything is expected of the current viewer, ahead of the detailed
 * sections below. Subsumes what used to be a REJECTED-only alert card -
 * every status now gets an equivalent, appropriately-toned block.
 *
 * The edit CTA (Slice 2) only ever appears for DRAFT/REJECTED - see
 * getEditCtaLabel. Every other status stays exactly as presentation-only.
 */
function StatusHero({
  request,
  onEdit,
  viewerRole = 'requester',
}: {
  request: PurchaseRequest;
  onEdit: (id: number) => void;
  viewerRole?: PurchaseRequestViewerRole;
}) {
  const tone = statusTone(request.status);
  const Icon = HERO_ICON[tone];
  const rejection = findRejection(request);
  const progress = getProgressLabel(request.status);
  const waitingHelperLine = getWaitingHelperLine(request.status, viewerRole);
  const editCtaLabel = getEditCtaLabel(request.status);

  return (
    <div className={cn('rounded-md border p-4 flex items-start gap-3', HERO_CLASSES[tone])}>
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="space-y-2 flex-1">
        <div className="space-y-1">
          <p className="font-semibold">{getStatusHeroLabel(request, viewerRole)}</p>
          <p className="text-sm">
            {rejection
              ? rejection.reason || STATUS_MESSAGES.REJECTED
              : getStatusHeroMessage(request, viewerRole)}
          </p>
          {waitingHelperLine && <p className="text-sm">{waitingHelperLine}</p>}
          {progress && <p className="text-xs opacity-75">{progress}</p>}
        </div>
        {editCtaLabel && (
          <Button type="button" size="sm" onClick={() => onEdit(request.id)}>
            <Pencil className="h-3.5 w-3.5 mr-1.5" />
            {editCtaLabel}
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * One stage's entry in the Approval Workflow, restyled (F20) as an official
 * workflow record - stage name, then its outcome and date on the line below,
 * rather than a single justified row - while keeping exactly the same
 * underlying data (getStageInfo) and text content existing tests already
 * pin (Approved/Rejected/Not Reached/Not Submitted/Pending).
 */
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
  let reason: string | null = null;

  if (info.kind === 'decided') {
    const isRejected = info.decision.decision === 'REJECTED';
    icon = isRejected ? (
      <XCircle className="h-4 w-4 text-red-600" />
    ) : (
      <CheckCircle className="h-4 w-4 text-green-600" />
    );
    text = decisionLabel(info.decision);
    sub = formatDate(info.decision.created_at);
    if (isRejected && info.decision.reason) {
      reason = info.decision.reason;
    }
  } else if (info.kind === 'not_reached') {
    icon = <MinusCircle className="h-4 w-4 text-muted-foreground" />;
    text = 'Not Reached';
  } else if (info.kind === 'not_submitted') {
    icon = <MinusCircle className="h-4 w-4 text-muted-foreground" />;
    text = 'Not Submitted';
  }

  return (
    <div className="py-2.5 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium">{label}</span>
        <span className="flex items-center gap-1.5 text-muted-foreground">
          {icon}
          {text}
        </span>
      </div>
      {(reason || sub) && (
        <div className="mt-0.5 pl-0 flex items-center justify-between text-xs text-muted-foreground">
          {reason ? <span className="italic">&ldquo;{reason}&rdquo;</span> : <span />}
          {sub && <span>{sub}</span>}
        </div>
      )}
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
  onEdit,
  actions,
  viewerRole = 'requester',
}: PurchaseRequestDetailProps) {
  if (!request && !isLoading) return null;

  const showProcurement =
    request && (request.status === 'PENDING_PROCUREMENT' || request.status === 'PROCESSED');
  const supersededRejection = request ? getSupersededRejection(request) : undefined;
  // Suppressed exactly when the status hero above is already showing this
  // same fact in its own words (a department head re-reviewing a corrected
  // request) - everywhere else, this section is the only place it appears.
  const heroAlreadyExplainsCorrection =
    !!request && viewerRole === 'department_head' && isCorrectedResubmission(request);
  const showCorrectionContext =
    !!request &&
    !!supersededRejection &&
    hasCorrectionHistory(request) &&
    !heroAlreadyExplainsCorrection;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        {/* Corporate document header (F20): ZCHPC identity + document title,
            with the requisition number/date/status as document metadata -
            the same information a paper requisition would carry in its own
            header, using the application's existing logo asset. */}
        <DialogHeader className="space-y-0">
          <div className="flex items-start justify-between gap-4 flex-wrap pb-4 border-b">
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="ZCHPC" className="h-9 w-auto flex-shrink-0" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Zimbabwe Centre for High Performance Computing
                </p>
                <DialogTitle className="text-lg font-bold tracking-tight">
                  Purchase Requisition
                </DialogTitle>
              </div>
            </div>
            {request && (
              <div className="text-right space-y-1 flex-shrink-0">
                <p className="text-sm font-semibold">{request.requisition_number}</p>
                <p className="text-xs text-muted-foreground">
                  {formatShortDate(request.created_at)}
                </p>
                <PurchaseRequestStatusBadge status={request.status} />
              </div>
            )}
          </div>
        </DialogHeader>

        {isLoading || !request ? (
          <div className="animate-pulse space-y-4 py-6">
            <div className="h-4 bg-muted rounded w-1/2"></div>
            <div className="h-24 bg-muted rounded"></div>
          </div>
        ) : (
          <ScrollArea className="flex-1 min-h-0">
            <div className="space-y-5 pr-4">
              <StatusHero request={request} onEdit={onEdit} viewerRole={viewerRole} />

              <DocumentSection title="Requester Details">
                <DocumentFieldGrid>
                  <DocumentField label="Requested By" value={request.requester_name} />
                  <DocumentField label="Designation" value={request.designation || '—'} />
                  <DocumentField label="Contact" value={request.contact || '—'} />
                  <DocumentField label="Department" value={request.department_name} />
                </DocumentFieldGrid>
              </DocumentSection>

              <Separator />

              <DocumentSection title="Request Details">
                <DocumentFieldGrid>
                  <DocumentField label="Requisition Number" value={request.requisition_number} />
                  <DocumentField label="Request Date" value={formatShortDate(request.created_at)} />
                  <DocumentField label="Current Status" value={STATUS_LABELS[request.status]} />
                </DocumentFieldGrid>
              </DocumentSection>

              <Separator />

              <DocumentSection title="Items Requested">
                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr className="text-left">
                        <th className="px-3 py-2 font-medium text-muted-foreground w-10">#</th>
                        <th className="px-3 py-2 font-medium text-muted-foreground">
                          Description
                        </th>
                        <th className="px-3 py-2 font-medium text-muted-foreground">Category</th>
                        <th className="px-3 py-2 font-medium text-muted-foreground text-right">
                          Qty
                        </th>
                        <th className="px-3 py-2 font-medium text-muted-foreground text-right">
                          Unit Cost
                        </th>
                        <th className="px-3 py-2 font-medium text-muted-foreground text-right">
                          Line Total
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {request.items.map((item, index) => (
                        <tr key={item.id}>
                          <td className="px-3 py-2 align-top text-muted-foreground">
                            {index + 1}
                          </td>
                          <td className="px-3 py-2 align-top font-medium">
                            {item.description}
                            <div className="text-xs font-normal text-muted-foreground">
                              Delivery: {item.expected_delivery_period}
                            </div>
                          </td>
                          <td className="px-3 py-2 align-top text-muted-foreground">
                            {item.category?.name ?? '—'}
                          </td>
                          <td className="px-3 py-2 align-top text-right tabular-nums">
                            {item.quantity}
                          </td>
                          <td className="px-3 py-2 align-top text-right tabular-nums">
                            {formatMoney(item.estimated_cost)}
                          </td>
                          <td className="px-3 py-2 align-top text-right tabular-nums font-semibold">
                            {formatMoney(lineTotal(item))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </DocumentSection>

              <Separator />

              <DocumentSection title="Financial Information">
                <div className="flex items-center justify-between rounded-md border bg-muted/30 px-4 py-3">
                  <span className="text-sm font-medium">Total Estimated Cost</span>
                  <span className="text-lg font-semibold tabular-nums">
                    {formatMoney(request.total_estimated_cost)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Category classification is recorded per line item - see Items Requested above.
                </p>
              </DocumentSection>

              <Separator />

              <DocumentSection title="Approval Workflow">
                <div className="divide-y rounded-md border px-3">
                  {APPROVAL_STAGES.map(({ stage, label }) => (
                    <StageRow key={stage} stage={stage} label={label} request={request} />
                  ))}
                </div>
              </DocumentSection>

              {showCorrectionContext && supersededRejection && (
                <>
                  <Separator />
                  <DocumentSection title="Rejection / Correction Context">
                    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 flex items-start gap-3 text-amber-900">
                      <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                      <p className="text-sm">
                        This request was previously rejected at the{' '}
                        <strong>{stageLabel(supersededRejection.stage)}</strong> stage and has
                        since been corrected and resubmitted.
                        {supersededRejection.reason && (
                          <>
                            {' '}
                            Original reason: &ldquo;{supersededRejection.reason}&rdquo;
                          </>
                        )}
                      </p>
                    </div>
                  </DocumentSection>
                </>
              )}

              {showProcurement && (
                <>
                  <Separator />
                  <DocumentSection title="Procurement">
                    <DocumentFieldGrid>
                      <DocumentField
                        label="Status"
                        value={procurementStatusLabel(request.status)}
                      />
                      {request.processed_at && (
                        <DocumentField
                          label="Date Processed"
                          value={formatDate(request.processed_at)}
                        />
                      )}
                    </DocumentFieldGrid>
                  </DocumentSection>
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

        {!isLoading && request && actions && (
          <div className="flex-shrink-0 pt-3 border-t space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Actions
            </h3>
            {actions}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestDetail;
