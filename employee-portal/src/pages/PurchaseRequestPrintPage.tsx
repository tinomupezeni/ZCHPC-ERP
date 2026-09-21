import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Loader2, Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { purchaseRequestService, getPurchaseRequestErrorMessage } from '@/services/purchase-request.service';
import type { PurchaseRequest, PurchaseRequestDecision, PurchaseRequestDecisionStage } from '@/types/purchase-request.types';
import { format, parseISO } from 'date-fns';

/**
 * F23: the final printable Purchase Requisition.
 *
 * A dedicated, standalone route (no MainLayout/sidebar - see App.tsx) that
 * reproduces the physical ZCHPC Purchase Requisition paper form's structure
 * (Sections A-D), not the corporate on-screen document PurchaseRequestDetail
 * already renders for reviewers. Only reachable/meaningful once a request is
 * PROCESSED - the physical form's Section D (Procurement Use Only) is where
 * the final record belongs, and printing an in-flight request would show a
 * half-finished paper trail.
 *
 * Two data gaps, deliberately not papered over with invented data:
 *  - The API only ever records who approved a stage as `actor_id`, never a
 *    display name (PurchaseRequestDecisionSerializer) - so each approval
 *    line below prints the recorded decision and date, not a name, leaving
 *    the physical form's signature blank for wet-ink signing/filing.
 *
 * The "Budget Code to be charged" column prints the AccountChart code Accounts
 * actually assigned to the item (item.budget_code.code, F25) - never the
 * employee's category, which only describes the need. An item with no
 * assigned code prints a blank cell rather than any substitute value.
 */
function formatDate(value: string | null): string {
  if (!value) return '';
  return format(parseISO(value), 'd MMM yyyy');
}

function lineTotal(item: { quantity: number; estimated_cost: string }): number {
  const unitCostCents = Math.round(Number.parseFloat(item.estimated_cost) * 100);
  return (unitCostCents * item.quantity) / 100;
}

function formatMoney(value: number | string): string {
  const amount = typeof value === 'number' ? value : Number.parseFloat(value);
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const DECISION_TEXT: Record<string, string> = {
  APPROVED: 'Approved',
  VERIFIED: 'Verified',
  RECOMMENDED: 'Recommended',
  REJECTED: 'Rejected',
};

/**
 * The physical form has several blank rows for handwritten entries - a
 * request with only one or two items must not collapse the table down to a
 * one-row sliver. Real items always fill the first rows; anything beyond
 * that is a genuinely empty row (no fabricated data), matching the paper
 * form's own blank space. Requests with more items than this simply get
 * more rows - nothing is ever truncated.
 */
const MIN_ITEM_ROWS = 7;

function latestDecision(
  decisions: PurchaseRequestDecision[],
  stage: PurchaseRequestDecisionStage
): PurchaseRequestDecision | undefined {
  for (let i = decisions.length - 1; i >= 0; i--) {
    if (decisions[i].stage === stage) return decisions[i];
  }
  return undefined;
}

export function PurchaseRequestPrintPage() {
  const { id } = useParams<{ id: string }>();
  const [request, setRequest] = useState<PurchaseRequest | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    purchaseRequestService
      .getRequest(Number(id))
      .then((result) => {
        if (!cancelled) setRequest(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getPurchaseRequestErrorMessage(err, 'Failed to load purchase request'));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (isLoading) {
    return (
      <div className="pr-print-status">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="pr-print-status">
        <p>{error || 'Purchase request not found.'}</p>
      </div>
    );
  }

  if (request.status !== 'PROCESSED') {
    return (
      <div className="pr-print-status">
        <p>
          The final Purchase Requisition print form becomes available once Procurement has
          finished processing this request. Current status:{' '}
          <strong>{request.status.replace(/_/g, ' ')}</strong>.
        </p>
      </div>
    );
  }

  const deptHead = latestDecision(request.decisions, 'DEPARTMENT_HEAD');
  const accounts = latestDecision(request.decisions, 'ACCOUNTS');
  const gm = latestDecision(request.decisions, 'GM');
  const director = latestDecision(request.decisions, 'DIRECTOR');

  return (
    <div className="pr-print-page">
      <div className="pr-print-actions">
        <Button type="button" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Print
        </Button>
      </div>

      <div className="pr-print-paper">
        <div className="pr-print-letterhead">
          <header className="pr-print-header">
            <img src="/CourtofArms.png" alt="Zimbabwe Coat of Arms" className="pr-print-crest" />
            <h1>PURCHASE REQUISITION</h1>
            <img src="/logo.png" alt="ZCHPC" />
          </header>
          <div className="pr-print-no">
            No: <span className="pr-print-fill">{request.requisition_number}</span>
          </div>
        </div>

        <h2>Section A: Details of Officer Requesting</h2>
        <div className="pr-print-row">
          <div>
            <span className="pr-print-label">Requested By:</span>
            <span className="pr-print-fill">{request.requester_name}</span>
          </div>
          <div>
            <span className="pr-print-label">Designation:</span>
            <span className="pr-print-fill">{request.designation}</span>
          </div>
        </div>
        <div className="pr-print-row">
          <div>
            <span className="pr-print-label">Contact:</span>
            <span className="pr-print-fill">{request.contact}</span>
          </div>
          <div>
            <span className="pr-print-label">Department:</span>
            <span className="pr-print-fill">{request.department_name}</span>
          </div>
        </div>

        <h2>Section B: Item(s) Requested</h2>
        <table className="pr-print-table">
          <thead>
            <tr>
              <th>Item Description</th>
              <th>Qty</th>
              <th>Expected Delivery Period</th>
              <th>Estimated Cost</th>
              <th>Budget Code to be charged</th>
            </tr>
          </thead>
          <tbody>
            {request.items.map((item) => (
              <tr key={item.id}>
                <td>{item.description}</td>
                <td className="pr-print-num">{item.quantity}</td>
                <td>{item.expected_delivery_period}</td>
                <td className="pr-print-num">{formatMoney(lineTotal(item))}</td>
                <td>{item.budget_code?.code ?? ''}</td>
              </tr>
            ))}
            {Array.from({ length: Math.max(0, MIN_ITEM_ROWS - request.items.length) }).map(
              (_, index) => (
                <tr key={`blank-${index}`} className="pr-print-blank-row">
                  <td>&nbsp;</td>
                  <td>&nbsp;</td>
                  <td>&nbsp;</td>
                  <td>&nbsp;</td>
                  <td>&nbsp;</td>
                </tr>
              )
            )}
            <tr className="pr-print-total-row">
              <td colSpan={3}>Total Estimated Costs</td>
              <td className="pr-print-num">{formatMoney(request.total_estimated_cost)}</td>
              <td />
            </tr>
          </tbody>
        </table>
        <p className="pr-print-note">
          N/B Please attach detailed specifications for the requirement.
        </p>

        <h2>Section C: Approvals</h2>
        <div className="pr-print-row">
          <div className="pr-print-approval-line">
            <span className="pr-print-label">Department Head:</span>
            <span className="pr-print-fill">
              {deptHead ? DECISION_TEXT[deptHead.decision] : ''}
            </span>
            <span className="pr-print-label">Date:</span>
            <span className="pr-print-fill">{deptHead ? formatDate(deptHead.created_at) : ''}</span>
          </div>
          <div className="pr-print-approval-line">
            <span className="pr-print-label">Accounts Verification:</span>
            <span className="pr-print-fill">
              {accounts ? DECISION_TEXT[accounts.decision] : ''}
            </span>
            <span className="pr-print-label">Date:</span>
            <span className="pr-print-fill">{accounts ? formatDate(accounts.created_at) : ''}</span>
          </div>
        </div>

        <div className="pr-print-approval-line pr-print-full">
          <span className="pr-print-label">GM/Recommended/Not Recommended:</span>
          <span className="pr-print-fill">{gm ? DECISION_TEXT[gm.decision] : ''}</span>
          <span className="pr-print-label">Date:</span>
          <span className="pr-print-fill">{gm ? formatDate(gm.created_at) : ''}</span>
        </div>
        <div className="pr-print-approval-line pr-print-full">
          <span className="pr-print-label">Reasons for Not Recommending:</span>
          <span className="pr-print-fill">{gm?.decision === 'REJECTED' ? gm.reason : ''}</span>
        </div>

        <div className="pr-print-approval-line pr-print-full">
          <span className="pr-print-label">Director/Approved/Not Approved:</span>
          <span className="pr-print-fill">{director ? DECISION_TEXT[director.decision] : ''}</span>
          <span className="pr-print-label">Date:</span>
          <span className="pr-print-fill">{director ? formatDate(director.created_at) : ''}</span>
        </div>
        <div className="pr-print-approval-line pr-print-full">
          <span className="pr-print-label">Reasons for Not Approving:</span>
          <span className="pr-print-fill">
            {director?.decision === 'REJECTED' ? director.reason : ''}
          </span>
        </div>

        <h2>Section D: Procurement Use Only</h2>
        <div className="pr-print-row">
          <div>
            <span className="pr-print-label">Procurement Officer:</span>
            <span className="pr-print-fill" />
          </div>
          <div>
            <span className="pr-print-label">Date Processed:</span>
            <span className="pr-print-fill">{formatDate(request.processed_at)}</span>
          </div>
        </div>
        <div className="pr-print-row">
          <div>
            <span className="pr-print-label">Purchase Order No.:</span>
            <span className="pr-print-fill">{request.purchase_order_number}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PurchaseRequestPrintPage;
