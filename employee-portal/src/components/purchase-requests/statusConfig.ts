import type {
  PurchaseRequest,
  PurchaseRequestDecision,
  PurchaseRequestDecisionStage,
  PurchaseRequestStatus,
} from '@/types/purchase-request.types';

/**
 * Employee-facing framing of each backend status (F13 Slice 1).
 *
 * The backend tells us what state the request is in; this module tells the
 * employee what that means and whether they need to do anything - approved
 * copy, treated as the source of truth. No CTA/editing capability is implied
 * by any of this - Slice 1 is presentation only. See PurchaseRequestCard and
 * PurchaseRequestDetail for where "no fake CTA" is actually enforced.
 */
export const STATUS_LABELS: Record<PurchaseRequestStatus, string> = {
  DRAFT: 'Not Submitted',
  PENDING_DEPARTMENT_HEAD: 'Awaiting Department Head',
  PENDING_ACCOUNTS: 'Awaiting Accounts Verification',
  PENDING_GM: 'Awaiting General Manager',
  PENDING_DIRECTOR: 'Awaiting Director Approval',
  PENDING_PROCUREMENT: 'Being Processed',
  PROCESSED: 'Completed',
  REJECTED: 'Correction Required',
};

/**
 * One-line explanation of what that status means, in plain language. For
 * REJECTED this is only the fallback shown when the backend didn't return a
 * reason - callers should prefer the real reason from findRejection() first.
 */
export const STATUS_MESSAGES: Record<PurchaseRequestStatus, string> = {
  DRAFT: "This request is saved but hasn't been sent for approval yet.",
  PENDING_DEPARTMENT_HEAD:
    'Submitted — your department head is reviewing it. No action needed from you.',
  PENDING_ACCOUNTS:
    'Approved by your department head — Accounts is now verifying the budget.',
  PENDING_GM: 'Verified by Accounts — the General Manager is reviewing it next.',
  PENDING_DIRECTOR:
    'Recommended by the General Manager — the Director is giving final approval.',
  PENDING_PROCUREMENT: 'Fully approved — Procurement is now sourcing/ordering the items.',
  PROCESSED: 'This request has been fully approved and processed.',
  REJECTED: 'This request was rejected and returned for correction.',
};

const NO_ACTION_NEEDED_LINE = 'No action needed from you.';

/**
 * A short reassurance line for "waiting" cards/heroes, distinct from
 * STATUS_MESSAGES so the two aren't duplicated when a status message already
 * ends with it (PENDING_DEPARTMENT_HEAD's approved copy already does).
 */
export function getWaitingHelperLine(status: PurchaseRequestStatus): string | null {
  if (getActionBucket(status) !== 'waiting') return null;
  return STATUS_MESSAGES[status].endsWith(NO_ACTION_NEEDED_LINE) ? null : NO_ACTION_NEEDED_LINE;
}

export type StatusBadgeTone = 'amber' | 'slate' | 'green' | 'red';

/**
 * amber = the employee's own unfinished business (DRAFT).
 * red = an external decision that needs the employee's attention (REJECTED).
 * slate = calm, normal, nothing to do (every PENDING_* stage).
 * green = done (PROCESSED).
 */
export function statusTone(status: PurchaseRequestStatus): StatusBadgeTone {
  switch (status) {
    case 'DRAFT':
      return 'amber';
    case 'PROCESSED':
      return 'green';
    case 'REJECTED':
      return 'red';
    default:
      return 'slate';
  }
}

/** The three buckets the "action required" grouping is built from. */
export type ActionBucket = 'needs_action' | 'waiting' | 'completed';

/** True only for DRAFT and REJECTED - a pure UI classification, not a new backend concept. */
export function isActionRequired(status: PurchaseRequestStatus): boolean {
  return status === 'DRAFT' || status === 'REJECTED';
}

export function getActionBucket(status: PurchaseRequestStatus): ActionBucket {
  if (isActionRequired(status)) return 'needs_action';
  if (status === 'PROCESSED') return 'completed';
  return 'waiting';
}

const APPROVAL_STEP: Partial<Record<PurchaseRequestStatus, number>> = {
  PENDING_DEPARTMENT_HEAD: 1,
  PENDING_ACCOUNTS: 2,
  PENDING_GM: 3,
  PENDING_DIRECTOR: 4,
};

const APPROVAL_STEP_COUNT = 4;

/** "Step 2 of 4" for the four approval-pipeline stages; null everywhere else. */
export function getProgressLabel(status: PurchaseRequestStatus): string | null {
  const step = APPROVAL_STEP[status];
  return step ? `Step ${step} of ${APPROVAL_STEP_COUNT}` : null;
}

/** Approval stages shown in Section C, in workflow order. */
export const APPROVAL_STAGES: { stage: PurchaseRequestDecisionStage; label: string }[] = [
  { stage: 'DEPARTMENT_HEAD', label: 'Department Head' },
  { stage: 'ACCOUNTS', label: 'Accounts Verification' },
  { stage: 'GM', label: 'GM Recommendation' },
  { stage: 'DIRECTOR', label: 'Director Approval' },
];

const STAGE_PENDING_STATUS: Record<PurchaseRequestDecisionStage, PurchaseRequestStatus> = {
  DEPARTMENT_HEAD: 'PENDING_DEPARTMENT_HEAD',
  ACCOUNTS: 'PENDING_ACCOUNTS',
  GM: 'PENDING_GM',
  DIRECTOR: 'PENDING_DIRECTOR',
};

export type StageInfo =
  | { kind: 'decided'; decision: PurchaseRequestDecision }
  | { kind: 'pending' }
  | { kind: 'not_reached' }
  | { kind: 'not_submitted' };

/**
 * Read-only presentation of one approval stage, derived entirely from the
 * request's own status and decision history - no approval logic lives here.
 */
export function getStageInfo(
  stage: PurchaseRequestDecisionStage,
  request: PurchaseRequest
): StageInfo {
  const decision = request.decisions.find((d) => d.stage === stage);
  if (decision) {
    return { kind: 'decided', decision };
  }
  if (request.status === 'DRAFT') {
    return { kind: 'not_submitted' };
  }
  if (request.status === STAGE_PENDING_STATUS[stage]) {
    return { kind: 'pending' };
  }
  return { kind: 'not_reached' };
}

const DECISION_LABELS: Record<string, string> = {
  APPROVED: 'Approved',
  VERIFIED: 'Verified',
  RECOMMENDED: 'Recommended',
  REJECTED: 'Rejected',
};

/**
 * Label for one historical decision record. Deliberately still says
 * "Rejected" for a REJECTED decision - that's describing what actually
 * happened at that stage, not the request's current employee-facing status
 * (which uses "Correction Required" instead - see STATUS_LABELS).
 */
export function decisionLabel(decision: PurchaseRequestDecision): string {
  return DECISION_LABELS[decision.decision] ?? decision.decision;
}

/** The rejection decision, if this request was rejected. */
export function findRejection(request: PurchaseRequest): PurchaseRequestDecision | undefined {
  if (request.status !== 'REJECTED') return undefined;
  return request.decisions.find((d) => d.decision === 'REJECTED');
}
