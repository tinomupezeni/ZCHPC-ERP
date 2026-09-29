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
 * Who is looking at this request's status right now (F19, generalized in
 * F20's "role-aware workflow status" follow-up).
 *
 * STATUS_LABELS/STATUS_MESSAGES stay requester-oriented and unchanged - they
 * back PurchaseRequestsPage, by far the more common caller, and every
 * existing test already pins that copy. Each reviewer role gets its own
 * override for the one status it actually reviews (see REVIEWER_STATUS and
 * REVIEWER_COPY below). This is deliberately not a general "which role is
 * this" enum resolved from the logged-in user (that's exactly the kind of
 * role detection useRole() already gets wrong for the seeded test accounts -
 * see F18's investigation) - it's simply which page asked, decided once by
 * that page itself, the same way the `actions` slot already works. GM/
 * Director/Procurement have no review page yet (out of scope - see F17/F18),
 * but are included here so the model doesn't need reshaping when they do.
 */
export type PurchaseRequestViewerRole =
  | 'requester'
  | 'department_head'
  | 'accounts'
  | 'gm'
  | 'director'
  | 'procurement';

type ReviewerRole = Exclude<PurchaseRequestViewerRole, 'requester'>;

/** The one status each reviewer role actually has standing to review. */
const REVIEWER_STATUS: Record<ReviewerRole, PurchaseRequestStatus> = {
  department_head: 'PENDING_DEPARTMENT_HEAD',
  accounts: 'PENDING_ACCOUNTS',
  gm: 'PENDING_GM',
  director: 'PENDING_DIRECTOR',
  procurement: 'PENDING_PROCUREMENT',
};

const DEPARTMENT_HEAD_REVIEW_LABEL = 'Awaiting Your Review';
const DEPARTMENT_HEAD_REVIEW_MESSAGE = 'This request requires your review and approval.';
const DEPARTMENT_HEAD_CORRECTED_LABEL = 'Correction Requires Your Review';
const DEPARTMENT_HEAD_CORRECTED_MESSAGE =
  'This request was corrected and resubmitted after the previous rejection. ' +
  'Please review the updated request before approving or rejecting it.';

/**
 * Reviewer-perspective copy for the roles that don't (yet) have a
 * corrected-resubmission variant of their own - only department_head does,
 * handled separately below, since it's the only stage every resubmission
 * always returns through (see PurchaseRequest.submit() on the backend).
 */
const REVIEWER_COPY: Record<Exclude<ReviewerRole, 'department_head'>, { label: string; message: string }> = {
  accounts: {
    label: 'Awaiting Your Verification',
    message:
      'This request has been approved by the Department Head and requires your budget verification.',
  },
  gm: {
    label: 'Awaiting Your Recommendation',
    message: 'This request requires your recommendation.',
  },
  director: {
    label: 'Awaiting Your Approval',
    message: 'This request requires your approval.',
  },
  procurement: {
    label: 'Awaiting Processing',
    message: 'This request is ready for procurement processing.',
  },
};

/**
 * True only for a request currently at PENDING_DEPARTMENT_HEAD that already
 * carries decision history - the same signal
 * PurchaseRequest.submit() uses on the backend to decide whether to raise
 * PurchaseRequestCorrectedAndResubmitted (F19): decisions only ever
 * accumulate during PENDING_* stages, never while DRAFT, and DRAFT is the
 * only way back to PENDING_DEPARTMENT_HEAD other than a first submission -
 * so non-empty decisions here can only mean a correction, regardless of
 * which stage rejected it or how many times. No new backend field needed;
 * the existing decisions[] the detail response already returns is enough.
 */
export function isCorrectedResubmission(request: PurchaseRequest): boolean {
  return request.status === 'PENDING_DEPARTMENT_HEAD' && request.decisions.length > 0;
}

/** True when this viewer is currently the one with standing to review this request. */
function isReviewingNow(
  status: PurchaseRequestStatus,
  viewerRole: PurchaseRequestViewerRole
): viewerRole is ReviewerRole {
  return viewerRole !== 'requester' && status === REVIEWER_STATUS[viewerRole as ReviewerRole];
}

/**
 * The status hero's title, from the given viewer's perspective. Only a
 * reviewer looking at the one status they themselves review differs from
 * STATUS_LABELS - every other (status, viewer) pair is unaffected, and the
 * requester's own view never changes.
 */
export function getStatusHeroLabel(
  request: PurchaseRequest,
  viewerRole: PurchaseRequestViewerRole = 'requester'
): string {
  if (isReviewingNow(request.status, viewerRole)) {
    if (viewerRole === 'department_head') {
      return isCorrectedResubmission(request)
        ? DEPARTMENT_HEAD_CORRECTED_LABEL
        : DEPARTMENT_HEAD_REVIEW_LABEL;
    }
    return REVIEWER_COPY[viewerRole].label;
  }
  return STATUS_LABELS[request.status];
}

/** The status hero's message, from the given viewer's perspective - see getStatusHeroLabel. */
export function getStatusHeroMessage(
  request: PurchaseRequest,
  viewerRole: PurchaseRequestViewerRole = 'requester'
): string {
  if (isReviewingNow(request.status, viewerRole)) {
    if (viewerRole === 'department_head') {
      return isCorrectedResubmission(request)
        ? DEPARTMENT_HEAD_CORRECTED_MESSAGE
        : DEPARTMENT_HEAD_REVIEW_MESSAGE;
    }
    return REVIEWER_COPY[viewerRole].message;
  }
  return STATUS_MESSAGES[request.status];
}

/**
 * A short reassurance line for "waiting" cards/heroes, distinct from
 * STATUS_MESSAGES so the two aren't duplicated when a status message already
 * ends with it (PENDING_DEPARTMENT_HEAD's requester-facing copy already
 * does). Never shown to a reviewer looking at the status they themselves
 * review: they have Approve/Reject/Verify/etc. controls right there, so "no
 * action needed" would be actively wrong, not just redundant.
 */
export function getWaitingHelperLine(
  status: PurchaseRequestStatus,
  viewerRole: PurchaseRequestViewerRole = 'requester'
): string | null {
  if (isReviewingNow(status, viewerRole)) {
    return null;
  }
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

/**
 * The edit CTA's label for the two action-required statuses (Slice 2 - both
 * now genuinely lead to an edit form, unlike Slice 1's placeholders). null
 * for every other status: waiting/completed requests have no edit action.
 */
export function getEditCtaLabel(status: PurchaseRequestStatus): string | null {
  if (status === 'DRAFT') return 'Continue Editing';
  if (status === 'REJECTED') return 'Review & Correct';
  return null;
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
 * The last element of `items` satisfying `predicate`, or undefined.
 *
 * The backend guarantees `decisions` arrives in chronological ascending
 * order (oldest first - see DjangoPurchaseRequestRepository._to_domain's
 * `.order_by("created_at")`), so "last match" is exactly "most recent
 * match" here - no re-sorting needed. A request corrected and resubmitted
 * after a rejection can carry more than one decision for the same stage
 * (e.g. DEPARTMENT_HEAD REJECTED then later DEPARTMENT_HEAD APPROVED); a
 * plain `.find()` would silently return the oldest one instead of the
 * current one. Deliberately a manual scan rather than `.findLast()`
 * (ES2023) - this project's TS target is ES2022 - and rather than
 * `.filter().at(-1)`, which would allocate an intermediate array.
 */
function lastMatch<T>(items: readonly T[], predicate: (item: T) => boolean): T | undefined {
  for (let i = items.length - 1; i >= 0; i--) {
    if (predicate(items[i])) return items[i];
  }
  return undefined;
}

/**
 * Read-only presentation of one approval stage, derived entirely from the
 * request's own status and decision history - no approval logic lives here.
 */
export function getStageInfo(
  stage: PurchaseRequestDecisionStage,
  request: PurchaseRequest
): StageInfo {
  const decision = lastMatch(request.decisions, (d) => d.stage === stage);
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

/**
 * The rejection decision explaining why this request is currently REJECTED.
 *
 * Must be the most recent rejection, not just the first one ever recorded:
 * a request can be rejected, corrected, resubmitted, and rejected again
 * (at the same stage or a later one) before landing back on REJECTED, and
 * every prior decision - approved or rejected - stays in `decisions`. Only
 * the latest rejection describes what's currently blocking the request.
 */
export function findRejection(request: PurchaseRequest): PurchaseRequestDecision | undefined {
  if (request.status !== 'REJECTED') return undefined;
  return lastMatch(request.decisions, (d) => d.decision === 'REJECTED');
}

/** The stage label shown in Section E (Approval Workflow), e.g. for a superseded rejection. */
export function stageLabel(stage: PurchaseRequestDecisionStage): string {
  return APPROVAL_STAGES.find((s) => s.stage === stage)?.label ?? stage;
}

/**
 * A REJECTED decision from this request's history that is no longer the
 * active blocker (F20) - either because the request has since moved past
 * REJECTED entirely (corrected, resubmitted, and now further along or even
 * PROCESSED), or because it's an earlier, different rejection than the one
 * currently blocking a REJECTED request.
 *
 * This exists because the stage-by-stage Approval Workflow section
 * (getStageInfo) only ever shows the LATEST decision per stage - a prior
 * rejection at a stage that has since been re-approved becomes invisible
 * there. Surfacing it separately is what makes "this request was previously
 * rejected and has been corrected" understandable at a later point in the
 * lifecycle, not just at the exact moment a reviewer is re-reviewing it.
 *
 * Returns undefined for a request that has never been rejected.
 */
export function getSupersededRejection(
  request: PurchaseRequest
): PurchaseRequestDecision | undefined {
  const candidates =
    request.status === 'REJECTED' ? request.decisions.slice(0, -1) : request.decisions;
  return lastMatch(candidates, (d) => d.decision === 'REJECTED');
}

/** Whether the "Rejection / Correction Context" section has anything to show. */
export function hasCorrectionHistory(request: PurchaseRequest): boolean {
  return getSupersededRejection(request) !== undefined;
}
