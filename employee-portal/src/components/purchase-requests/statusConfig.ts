import type {
  PurchaseRequest,
  PurchaseRequestDecision,
  PurchaseRequestDecisionStage,
  PurchaseRequestStatus,
} from '@/types/purchase-request.types';

export const STATUS_LABELS: Record<PurchaseRequestStatus, string> = {
  DRAFT: 'Draft',
  PENDING_DEPARTMENT_HEAD: 'Pending Department Head',
  PENDING_ACCOUNTS: 'Pending Accounts',
  PENDING_GM: 'Pending GM',
  PENDING_DIRECTOR: 'Pending Director',
  PENDING_PROCUREMENT: 'Pending Procurement',
  PROCESSED: 'Processed',
  REJECTED: 'Rejected',
};

export type StatusBadgeTone = 'gray' | 'orange' | 'green' | 'red';

export function statusTone(status: PurchaseRequestStatus): StatusBadgeTone {
  switch (status) {
    case 'DRAFT':
      return 'gray';
    case 'PROCESSED':
      return 'green';
    case 'REJECTED':
      return 'red';
    default:
      return 'orange';
  }
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

export function decisionLabel(decision: PurchaseRequestDecision): string {
  return DECISION_LABELS[decision.decision] ?? decision.decision;
}

/** The rejection decision, if this request was rejected. */
export function findRejection(request: PurchaseRequest): PurchaseRequestDecision | undefined {
  if (request.status !== 'REJECTED') return undefined;
  return request.decisions.find((d) => d.decision === 'REJECTED');
}
