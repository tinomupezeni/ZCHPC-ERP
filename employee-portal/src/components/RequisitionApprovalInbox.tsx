import { useState } from 'react';
import { Check, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { FuelRequisition } from '@/types/fuel-requisition.types';
import type { StoresRequisition } from '@/types/stores-requisition.types';

type Requisition = FuelRequisition | StoresRequisition;
type RequisitionKind = 'fuel' | 'stores';

const stageNames: Record<string, string> = {
  PENDING_DEPARTMENT: 'Department approval',
  PENDING_RECIPIENT: 'Recipient / driver confirmation',
  PENDING_PROCUREMENT: 'Procurement / stores review',
  PENDING_ACCOUNTS: 'Accounts / finance review',
  PENDING_FINANCE: 'Finance / General Manager review',
  PENDING_GENERAL_MANAGER: 'General Manager approval',
  PENDING_DIRECTOR: 'Director approval',
  PENDING_ADMIN: 'Administration processing',
};

function formatRequestDate(value: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(value));
}

interface Props {
  kind: RequisitionKind;
  requests: Requisition[];
  busyId: number | null;
  onApprove: (id: number) => void;
  onReject: (id: number, reason: string) => void;
}

export function RequisitionApprovalInbox({ kind, requests, busyId, onApprove, onReject }: Props) {
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [reason, setReason] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const beginReject = (id: number) => {
    setRejectingId(id);
    setReason('');
  };

  const submitRejection = (id: number) => {
    if (!reason.trim()) return;
    onReject(id, reason.trim());
    setRejectingId(null);
    setReason('');
  };

  return (
    <section className="requisition-inbox" aria-labelledby={`${kind}-inbox-heading`}>
      <div className="requisition-inbox-heading">
        <div>
          <p className="eyebrow">APPROVAL QUEUE</p>
          <h2 id={`${kind}-inbox-heading`}>Awaiting your action</h2>
        </div>
        <span>{requests.length} pending</span>
      </div>
      {requests.length === 0 ? (
        <p className="requisition-inbox-empty">No requests are currently assigned to your approval stage.</p>
      ) : (
        <div className="requisition-inbox-list">
          {requests.map((request) => {
            const requestLabel = kind === 'fuel'
              ? `FR-${request.id}`
              : (request as StoresRequisition).requisition_number;
            const fuelRequest = request as FuelRequisition;
            const storesRequest = request as StoresRequisition;
            const expanded = expandedId === request.id;
            return (
              <article className="requisition-inbox-item" key={request.id}>
                <div className="requisition-inbox-summary">
                  <div>
                    <strong>{requestLabel}</strong>
                    <p>{request.requester_name || request.requester_email} · {request.department}</p>
                    <span className="requisition-stage">{stageNames[request.status] ?? request.status}</span>
                  </div>
                  <div className="requisition-item-actions">
                    <Button type="button" variant="outline" size="sm" onClick={() => setExpandedId(expanded ? null : request.id)}>
                      {expanded ? 'Hide details' : 'View details'}
                    </Button>
                    <Button type="button" size="sm" disabled={busyId === request.id} onClick={() => onApprove(request.id)} aria-label={`Approve ${requestLabel}`}>
                      {busyId === request.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="mr-1 h-4 w-4" />}
                      Approve
                    </Button>
                    <Button type="button" variant="destructive" size="sm" disabled={busyId === request.id} onClick={() => beginReject(request.id)} aria-label={`Reject ${requestLabel}`}>
                      <X className="mr-1 h-4 w-4" />Reject
                    </Button>
                  </div>
                </div>
                {rejectingId === request.id && (
                  <div className="requisition-reject-panel">
                    <label htmlFor={`reject-reason-${request.id}`}>Reason for rejection</label>
                    <textarea id={`reject-reason-${request.id}`} rows={2} value={reason} onChange={(event) => setReason(event.target.value)} />
                    <div>
                      <Button type="button" variant="outline" size="sm" onClick={() => setRejectingId(null)}>Cancel</Button>
                      <Button type="button" variant="destructive" size="sm" disabled={!reason.trim() || busyId === request.id} onClick={() => submitRejection(request.id)}>Confirm rejection</Button>
                    </div>
                  </div>
                )}
                {expanded && (
                  <dl className="requisition-detail-grid">
                    {kind === 'fuel' ? (
                      <>
                        <div><dt>Requested by</dt><dd>{request.requester_name}</dd></div>
                        <div><dt>Employee code</dt><dd>{request.requester_employee_id}</dd></div>
                        <div><dt>Requester email</dt><dd><a href={`mailto:${request.requester_email}`}>{request.requester_email}</a></dd></div>
                        <div><dt>Department</dt><dd>{request.department}</dd></div>
                        <div><dt>Recipient / driver</dt><dd>{fuelRequest.recipient_driver}</dd></div>
                        <div><dt>Vehicle</dt><dd>{fuelRequest.vehicle_registration}</dd></div>
                        <div><dt>Destination</dt><dd>{fuelRequest.destination}</dd></div>
                        <div><dt>Diesel requested</dt><dd>{fuelRequest.diesel_quantity} L {fuelRequest.diesel_quantity_words && `(${fuelRequest.diesel_quantity_words})`}</dd></div>
                        <div><dt>Petrol requested</dt><dd>{fuelRequest.petrol_quantity} L {fuelRequest.petrol_quantity_words && `(${fuelRequest.petrol_quantity_words})`}</dd></div>
                        <div className="detail-wide"><dt>Purpose</dt><dd>{fuelRequest.purpose}</dd></div>
                      </>
                    ) : (
                      <>
                        <div><dt>Requested by</dt><dd>{request.requester_name}</dd></div>
                        <div><dt>Employee code</dt><dd>{request.requester_employee_id}</dd></div>
                        <div><dt>Requester email</dt><dd><a href={`mailto:${request.requester_email}`}>{request.requester_email}</a></dd></div>
                        <div><dt>Department</dt><dd>{request.department}</dd></div>
                        <div><dt>Items requested</dt><dd>{storesRequest.items.length}</dd></div>
                        <div className="detail-wide"><dt>Request details</dt><dd>{storesRequest.items.map((item, index) => `${index + 1}. ${item.description} · Qty ${item.quantity_required} · Budget ${item.budget_code} · Needed ${item.required_by}`).join('\n')}</dd></div>
                      </>
                    )}
                    <div><dt>Submitted</dt><dd>{formatRequestDate(request.created_at)}</dd></div>
                  </dl>
                )}
                {expanded && (
                  <section className="inbox-approval-history" aria-label="Approval history">
                    <h3>Approval history</h3>
                    <ol>
                      {(kind === 'fuel' ? [
                        { office: 'Head of Department', approver: fuelRequest.department_approved_by, date: fuelRequest.department_approved_at },
                        { office: 'Recipient / driver', approver: fuelRequest.recipient_approved_by, date: fuelRequest.recipient_approved_at },
                        { office: 'Finance / General Manager', approver: fuelRequest.finance_approved_by, date: fuelRequest.finance_approved_at },
                        { office: 'Director', approver: fuelRequest.director_approved_by, date: fuelRequest.director_approved_at },
                        { office: 'Administration', approver: fuelRequest.admin_approved_by, date: fuelRequest.admin_approved_at },
                      ] : [
                        { office: 'Head of Department', approver: storesRequest.department_approved_by, date: storesRequest.department_approved_at },
                        { office: 'Procurement / Stores', approver: storesRequest.procurement_approved_by, date: storesRequest.procurement_approved_at },
                        { office: 'Accounts / Finance', approver: storesRequest.accounts_approved_by, date: storesRequest.accounts_approved_at },
                        { office: 'General Manager', approver: storesRequest.general_manager_approved_by, date: storesRequest.general_manager_approved_at },
                        { office: 'Director', approver: storesRequest.director_approved_by, date: storesRequest.director_approved_at },
                        { office: 'Administration', approver: storesRequest.admin_approved_by, date: storesRequest.admin_approved_at },
                      ]).map((approval) => (
                        <li key={approval.office} className={approval.approver ? 'approval-recorded' : ''}>
                          <strong>{approval.office}</strong>
                          <span>{approval.approver || 'Pending'}</span>
                          <time>{approval.date ? formatRequestDate(approval.date) : 'Not approved'}</time>
                        </li>
                      ))}
                    </ol>
                    {request.status === 'REJECTED' && (
                      <p className="inbox-rejection-note">Rejected at {kind === 'fuel' ? (stageNames[fuelRequest.rejected_at_stage] ?? fuelRequest.rejected_at_stage) : (stageNames[storesRequest.rejected_at_stage] ?? storesRequest.rejected_at_stage)}: {request.rejection_reason}</p>
                    )}
                  </section>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
