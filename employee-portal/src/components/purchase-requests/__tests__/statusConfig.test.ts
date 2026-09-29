import { describe, expect, it } from 'vitest';
import {
  APPROVAL_STAGES,
  STATUS_LABELS,
  STATUS_MESSAGES,
  findRejection,
  getActionBucket,
  getEditCtaLabel,
  getProgressLabel,
  getStageInfo,
  getStatusHeroLabel,
  getStatusHeroMessage,
  getSupersededRejection,
  getWaitingHelperLine,
  hasCorrectionHistory,
  isActionRequired,
  isCorrectedResubmission,
  stageLabel,
  statusTone,
} from '../statusConfig';
import type {
  PurchaseRequest,
  PurchaseRequestDecision,
  PurchaseRequestDecisionStage,
  PurchaseRequestStatus,
} from '@/types/purchase-request.types';

const ALL_STATUSES: PurchaseRequestStatus[] = [
  'DRAFT',
  'PENDING_DEPARTMENT_HEAD',
  'PENDING_ACCOUNTS',
  'PENDING_GM',
  'PENDING_DIRECTOR',
  'PENDING_PROCUREMENT',
  'PROCESSED',
  'REJECTED',
];

describe('STATUS_LABELS - approved human-friendly mapping', () => {
  it.each([
    ['DRAFT', 'Not Submitted'],
    ['PENDING_DEPARTMENT_HEAD', 'Awaiting Department Head'],
    ['PENDING_ACCOUNTS', 'Awaiting Accounts Verification'],
    ['PENDING_GM', 'Awaiting General Manager'],
    ['PENDING_DIRECTOR', 'Awaiting Director Approval'],
    ['PENDING_PROCUREMENT', 'Being Processed'],
    ['PROCESSED', 'Completed'],
    ['REJECTED', 'Correction Required'],
  ] satisfies [PurchaseRequestStatus, string][])('%s -> %s', (status, label) => {
    expect(STATUS_LABELS[status]).toBe(label);
  });

  it('defines a label and a message for every backend status', () => {
    for (const status of ALL_STATUSES) {
      expect(STATUS_LABELS[status]).toBeTruthy();
      expect(STATUS_MESSAGES[status]).toBeTruthy();
    }
  });
});

describe('isActionRequired', () => {
  it('is true only for DRAFT and REJECTED', () => {
    for (const status of ALL_STATUSES) {
      const expected = status === 'DRAFT' || status === 'REJECTED';
      expect(isActionRequired(status)).toBe(expected);
    }
  });

  it('is false for every PENDING_* status', () => {
    const pendingStatuses: PurchaseRequestStatus[] = [
      'PENDING_DEPARTMENT_HEAD',
      'PENDING_ACCOUNTS',
      'PENDING_GM',
      'PENDING_DIRECTOR',
      'PENDING_PROCUREMENT',
    ];
    for (const status of pendingStatuses) {
      expect(isActionRequired(status)).toBe(false);
    }
  });

  it('is false for PROCESSED', () => {
    expect(isActionRequired('PROCESSED')).toBe(false);
  });
});

describe('getActionBucket', () => {
  it('buckets DRAFT and REJECTED as needs_action', () => {
    expect(getActionBucket('DRAFT')).toBe('needs_action');
    expect(getActionBucket('REJECTED')).toBe('needs_action');
  });

  it('buckets every PENDING_* status as waiting', () => {
    expect(getActionBucket('PENDING_DEPARTMENT_HEAD')).toBe('waiting');
    expect(getActionBucket('PENDING_ACCOUNTS')).toBe('waiting');
    expect(getActionBucket('PENDING_GM')).toBe('waiting');
    expect(getActionBucket('PENDING_DIRECTOR')).toBe('waiting');
    expect(getActionBucket('PENDING_PROCUREMENT')).toBe('waiting');
  });

  it('buckets PROCESSED as completed', () => {
    expect(getActionBucket('PROCESSED')).toBe('completed');
  });
});

describe('statusTone', () => {
  it('uses amber for DRAFT, red for REJECTED, green for PROCESSED, slate for every waiting status', () => {
    expect(statusTone('DRAFT')).toBe('amber');
    expect(statusTone('REJECTED')).toBe('red');
    expect(statusTone('PROCESSED')).toBe('green');
    expect(statusTone('PENDING_DEPARTMENT_HEAD')).toBe('slate');
    expect(statusTone('PENDING_ACCOUNTS')).toBe('slate');
    expect(statusTone('PENDING_GM')).toBe('slate');
    expect(statusTone('PENDING_DIRECTOR')).toBe('slate');
    expect(statusTone('PENDING_PROCUREMENT')).toBe('slate');
  });
});

describe('getProgressLabel', () => {
  it('returns a step count only for the four approval-pipeline stages', () => {
    expect(getProgressLabel('PENDING_DEPARTMENT_HEAD')).toBe('Step 1 of 4');
    expect(getProgressLabel('PENDING_ACCOUNTS')).toBe('Step 2 of 4');
    expect(getProgressLabel('PENDING_GM')).toBe('Step 3 of 4');
    expect(getProgressLabel('PENDING_DIRECTOR')).toBe('Step 4 of 4');
  });

  it('returns null for every other status, including PENDING_PROCUREMENT', () => {
    expect(getProgressLabel('DRAFT')).toBeNull();
    expect(getProgressLabel('PENDING_PROCUREMENT')).toBeNull();
    expect(getProgressLabel('PROCESSED')).toBeNull();
    expect(getProgressLabel('REJECTED')).toBeNull();
  });
});

describe('getEditCtaLabel', () => {
  it('returns "Continue Editing" for DRAFT and "Review & Correct" for REJECTED', () => {
    expect(getEditCtaLabel('DRAFT')).toBe('Continue Editing');
    expect(getEditCtaLabel('REJECTED')).toBe('Review & Correct');
  });

  it('returns null for every non-action-required status', () => {
    const nonActionable: PurchaseRequestStatus[] = [
      'PENDING_DEPARTMENT_HEAD',
      'PENDING_ACCOUNTS',
      'PENDING_GM',
      'PENDING_DIRECTOR',
      'PENDING_PROCUREMENT',
      'PROCESSED',
    ];
    for (const status of nonActionable) {
      expect(getEditCtaLabel(status)).toBeNull();
    }
  });
});

describe('getWaitingHelperLine', () => {
  it('returns null for non-waiting statuses', () => {
    expect(getWaitingHelperLine('DRAFT')).toBeNull();
    expect(getWaitingHelperLine('REJECTED')).toBeNull();
    expect(getWaitingHelperLine('PROCESSED')).toBeNull();
  });

  it('is not duplicated when the canonical message already ends with it', () => {
    // PENDING_DEPARTMENT_HEAD's approved message already ends with
    // "No action needed from you." - the helper must not repeat it.
    expect(STATUS_MESSAGES.PENDING_DEPARTMENT_HEAD.endsWith('No action needed from you.')).toBe(
      true
    );
    expect(getWaitingHelperLine('PENDING_DEPARTMENT_HEAD')).toBeNull();
  });

  it('is provided for waiting statuses whose message does not already include it', () => {
    expect(getWaitingHelperLine('PENDING_ACCOUNTS')).toBe('No action needed from you.');
    expect(getWaitingHelperLine('PENDING_GM')).toBe('No action needed from you.');
    expect(getWaitingHelperLine('PENDING_DIRECTOR')).toBe('No action needed from you.');
    expect(getWaitingHelperLine('PENDING_PROCUREMENT')).toBe('No action needed from you.');
  });

  it('F19: defaults to the requester perspective when no viewerRole is passed', () => {
    expect(getWaitingHelperLine('PENDING_DEPARTMENT_HEAD')).toBeNull();
    expect(getWaitingHelperLine('PENDING_DEPARTMENT_HEAD', 'requester')).toBeNull();
  });

  it('F19: never says "No action needed" to a department head reviewing PENDING_DEPARTMENT_HEAD', () => {
    expect(getWaitingHelperLine('PENDING_DEPARTMENT_HEAD', 'department_head')).toBeNull();
  });

  it('F19: a department head viewer is unaffected for every other status', () => {
    expect(getWaitingHelperLine('PENDING_ACCOUNTS', 'department_head')).toBe(
      'No action needed from you.'
    );
    expect(getWaitingHelperLine('DRAFT', 'department_head')).toBeNull();
  });
});

/**
 * Regression coverage for the "stale decision" bug: a stage decided more
 * than once (rejected, corrected/resubmitted, then decided again) must
 * report its LATEST decision, not the first one recorded. The backend
 * guarantees `decisions` arrives oldest-first, so these fixtures list
 * decisions in that same chronological order.
 */
function decision(
  stage: PurchaseRequestDecisionStage,
  type: PurchaseRequestDecision['decision'],
  created_at: string,
  reason = ''
): PurchaseRequestDecision {
  return { id: 0, stage, decision: type, actor_id: 1, reason, created_at };
}

function requestWithDecisions(
  status: PurchaseRequestStatus,
  decisions: PurchaseRequestDecision[]
): PurchaseRequest {
  return {
    id: 1,
    requisition_number: 'PR-0001',
    requester_id: 1,
    requester_name: 'Test Requester',
    department_id: 1,
    department_name: 'IT Department',
    designation: 'Officer',
    contact: '+263771234567',
    status,
    total_estimated_cost: '100.00',
    items: [],
    decisions,
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };
}

/**
 * F19 follow-up: status hero copy must be written from the current
 * viewer's perspective. Requester copy (the default, and every other
 * status) must be completely unaffected - only a department head looking
 * at PENDING_DEPARTMENT_HEAD gets different wording, and a corrected
 * resubmission (decisions already present) gets a third variant on top of
 * that, all without any new backend field.
 */
describe('getStatusHeroLabel / getStatusHeroMessage / isCorrectedResubmission', () => {
  it('defaults to the requester-oriented STATUS_LABELS/STATUS_MESSAGES when no viewerRole is passed', () => {
    const request = requestWithDecisions('PENDING_DEPARTMENT_HEAD', []);

    expect(getStatusHeroLabel(request)).toBe(STATUS_LABELS.PENDING_DEPARTMENT_HEAD);
    expect(getStatusHeroMessage(request)).toBe(STATUS_MESSAGES.PENDING_DEPARTMENT_HEAD);
  });

  it('keeps requester-oriented copy for a requester viewer explicitly', () => {
    const request = requestWithDecisions('PENDING_DEPARTMENT_HEAD', []);

    expect(getStatusHeroLabel(request, 'requester')).toBe(STATUS_LABELS.PENDING_DEPARTMENT_HEAD);
    expect(getStatusHeroMessage(request, 'requester')).toBe(
      STATUS_MESSAGES.PENDING_DEPARTMENT_HEAD
    );
  });

  it('uses reviewer-oriented copy for a department head viewing a first-time PENDING_DEPARTMENT_HEAD request', () => {
    const request = requestWithDecisions('PENDING_DEPARTMENT_HEAD', []);

    expect(isCorrectedResubmission(request)).toBe(false);
    expect(getStatusHeroLabel(request, 'department_head')).toBe('Awaiting Your Review');
    expect(getStatusHeroMessage(request, 'department_head')).toBe(
      'This request requires your review and approval.'
    );
    // Must never say either of these to the person who can act right now.
    expect(getStatusHeroMessage(request, 'department_head')).not.toMatch(/no action needed/i);
    expect(getStatusHeroMessage(request, 'department_head')).not.toMatch(
      /your department head is reviewing/i
    );
  });

  it('uses corrected-resubmission copy for a department head viewing a request with prior decision history', () => {
    const request = requestWithDecisions('PENDING_DEPARTMENT_HEAD', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T09:00:00Z'),
      decision('ACCOUNTS', 'REJECTED', '2025-01-01T10:00:00Z', 'Category needs revisiting'),
    ]);

    expect(isCorrectedResubmission(request)).toBe(true);
    expect(getStatusHeroLabel(request, 'department_head')).toBe('Correction Requires Your Review');
    expect(getStatusHeroMessage(request, 'department_head')).toMatch(/corrected and resubmitted/i);
  });

  it('is not corrected-resubmission for a request with decisions at any other status', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T09:00:00Z'),
    ]);

    expect(isCorrectedResubmission(request)).toBe(false);
  });

  it('does not change copy for a department head viewer at any status other than PENDING_DEPARTMENT_HEAD', () => {
    for (const status of ['DRAFT', 'PENDING_ACCOUNTS', 'REJECTED', 'PROCESSED'] as const) {
      const request = requestWithDecisions(status, []);
      expect(getStatusHeroLabel(request, 'department_head')).toBe(STATUS_LABELS[status]);
      expect(getStatusHeroMessage(request, 'department_head')).toBe(STATUS_MESSAGES[status]);
    }
  });
});

/**
 * F20: the same reviewer-perspective override pattern F19 built for
 * department_head, generalized to accounts/gm/director/procurement. Each
 * role only differs from the requester's STATUS_LABELS/STATUS_MESSAGES at
 * the one status it actually reviews.
 */
describe('getStatusHeroLabel / getStatusHeroMessage - F20 reviewer roles', () => {
  it('uses Accounts reviewer-oriented copy only at PENDING_ACCOUNTS', () => {
    const pending = requestWithDecisions('PENDING_ACCOUNTS', []);
    expect(getStatusHeroLabel(pending, 'accounts')).toBe('Awaiting Your Verification');
    expect(getStatusHeroMessage(pending, 'accounts')).toBe(
      'This request has been approved by the Department Head and requires your budget verification.'
    );

    for (const status of ['DRAFT', 'PENDING_DEPARTMENT_HEAD', 'REJECTED', 'PROCESSED'] as const) {
      const request = requestWithDecisions(status, []);
      expect(getStatusHeroLabel(request, 'accounts')).toBe(STATUS_LABELS[status]);
      expect(getStatusHeroMessage(request, 'accounts')).toBe(STATUS_MESSAGES[status]);
    }
  });

  it('uses GM reviewer-oriented copy only at PENDING_GM', () => {
    const pending = requestWithDecisions('PENDING_GM', []);
    expect(getStatusHeroLabel(pending, 'gm')).toBe('Awaiting Your Recommendation');
    expect(getStatusHeroMessage(pending, 'gm')).toBe('This request requires your recommendation.');
  });

  it('uses Director reviewer-oriented copy only at PENDING_DIRECTOR', () => {
    const pending = requestWithDecisions('PENDING_DIRECTOR', []);
    expect(getStatusHeroLabel(pending, 'director')).toBe('Awaiting Your Approval');
    expect(getStatusHeroMessage(pending, 'director')).toBe('This request requires your approval.');
  });

  it('uses Procurement reviewer-oriented copy only at PENDING_PROCUREMENT', () => {
    const pending = requestWithDecisions('PENDING_PROCUREMENT', []);
    expect(getStatusHeroLabel(pending, 'procurement')).toBe('Awaiting Processing');
    expect(getStatusHeroMessage(pending, 'procurement')).toBe(
      'This request is ready for procurement processing.'
    );
  });

  it('never suppresses "No action needed" incorrectly - only the reviewing role loses it at their own stage', () => {
    expect(getWaitingHelperLine('PENDING_ACCOUNTS', 'accounts')).toBeNull();
    expect(getWaitingHelperLine('PENDING_ACCOUNTS', 'gm')).toBe('No action needed from you.');
    expect(getWaitingHelperLine('PENDING_GM', 'gm')).toBeNull();
    expect(getWaitingHelperLine('PENDING_DIRECTOR', 'director')).toBeNull();
    expect(getWaitingHelperLine('PENDING_PROCUREMENT', 'procurement')).toBeNull();
  });

  it('leaves the requester\'s own copy at every status completely unaffected by any reviewer role existing', () => {
    for (const status of ALL_STATUSES) {
      const request = requestWithDecisions(status, []);
      expect(getStatusHeroLabel(request)).toBe(STATUS_LABELS[status]);
      expect(getStatusHeroMessage(request)).toBe(STATUS_MESSAGES[status]);
    }
  });
});

describe('stageLabel', () => {
  it('returns the human-readable label for each pipeline stage', () => {
    expect(stageLabel('DEPARTMENT_HEAD')).toBe('Department Head');
    expect(stageLabel('ACCOUNTS')).toBe('Accounts Verification');
    expect(stageLabel('GM')).toBe('GM Recommendation');
    expect(stageLabel('DIRECTOR')).toBe('Director Approval');
  });
});

/**
 * F20: surfaces a rejection that the stage-by-stage Approval Workflow
 * section can no longer show on its own (getStageInfo only ever reports the
 * LATEST decision per stage), so "this was rejected and corrected" stays
 * understandable even after the request has moved well past that point.
 */
describe('getSupersededRejection / hasCorrectionHistory', () => {
  it('returns undefined for a request that has never been rejected', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T09:00:00Z'),
    ]);
    expect(getSupersededRejection(request)).toBeUndefined();
    expect(hasCorrectionHistory(request)).toBe(false);
  });

  it('finds the rejection once a later decision has superseded it', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T09:00:00Z', 'Wrong model'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-02T09:00:00Z'),
    ]);
    const superseded = getSupersededRejection(request);
    expect(superseded?.reason).toBe('Wrong model');
    expect(hasCorrectionHistory(request)).toBe(true);
  });

  it('does not treat the CURRENTLY active rejection (nothing after it) as superseded', () => {
    const request = requestWithDecisions('REJECTED', [
      decision('ACCOUNTS', 'REJECTED', '2025-01-01T09:00:00Z', 'Budget code inactive'),
    ]);
    expect(getSupersededRejection(request)).toBeUndefined();
    expect(hasCorrectionHistory(request)).toBe(false);
  });

  it('still finds an earlier superseded rejection even while a later, different rejection is currently active', () => {
    const request = requestWithDecisions('REJECTED', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T09:00:00Z', 'Wrong model'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-02T09:00:00Z'),
      decision('ACCOUNTS', 'REJECTED', '2025-01-03T09:00:00Z', 'Budget code inactive'),
    ]);
    const superseded = getSupersededRejection(request);
    expect(superseded?.reason).toBe('Wrong model');
    expect(hasCorrectionHistory(request)).toBe(true);
  });

  it('finds the rejection for a department head re-reviewing a just-corrected request (only one decision exists)', () => {
    const request = requestWithDecisions('PENDING_DEPARTMENT_HEAD', [
      decision('ACCOUNTS', 'REJECTED', '2025-01-01T09:00:00Z', 'Category needs revisiting'),
    ]);
    expect(hasCorrectionHistory(request)).toBe(true);
  });
});

const PIPELINE_STAGES: PurchaseRequestDecisionStage[] = [
  'DEPARTMENT_HEAD',
  'ACCOUNTS',
  'GM',
  'DIRECTOR',
];

describe('getStageInfo', () => {
  it('reports a first-time approval as decided', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T10:00:00Z'),
    ]);

    const info = getStageInfo('DEPARTMENT_HEAD', request);

    expect(info.kind).toBe('decided');
    expect(info.kind === 'decided' && info.decision.decision).toBe('APPROVED');
  });

  it('reports a first-time rejection as decided', () => {
    const request = requestWithDecisions('REJECTED', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z', 'Missing quote'),
    ]);

    const info = getStageInfo('DEPARTMENT_HEAD', request);

    expect(info.kind).toBe('decided');
    expect(info.kind === 'decided' && info.decision.decision).toBe('REJECTED');
  });

  it.each(PIPELINE_STAGES)(
    '%s: a later approval wins over an earlier rejection at the same stage',
    (stage) => {
      const request = requestWithDecisions('PENDING_ACCOUNTS', [
        decision(stage, 'REJECTED', '2025-01-01T10:00:00Z', 'Needs correction'),
        decision(stage, 'APPROVED', '2025-01-01T11:00:00Z'),
      ]);

      const info = getStageInfo(stage, request);

      expect(info.kind).toBe('decided');
      expect(info.kind === 'decided' && info.decision.decision).not.toBe('REJECTED');
      expect(info.kind === 'decided' && info.decision.created_at).toBe('2025-01-01T11:00:00Z');
    }
  );

  it('wins with the latest of three or more decisions at the same stage', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z', 'First pass'),
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T11:00:00Z', 'Second pass'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T12:00:00Z'),
    ]);

    const info = getStageInfo('DEPARTMENT_HEAD', request);

    expect(info.kind).toBe('decided');
    expect(info.kind === 'decided' && info.decision.created_at).toBe('2025-01-01T12:00:00Z');
  });

  it('does not mutate or reorder request.decisions while resolving the latest one', () => {
    const decisions = [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T11:00:00Z'),
    ];
    const request = requestWithDecisions('PENDING_ACCOUNTS', decisions);
    const before = [...request.decisions];

    getStageInfo('DEPARTMENT_HEAD', request);

    expect(request.decisions).toEqual(before);
    expect(request.decisions).toHaveLength(2);
  });

  it('a Department Head reject/re-approve cycle does not affect other stages (single-decision behavior unchanged)', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T11:00:00Z'),
    ]);

    expect(getStageInfo('ACCOUNTS', request)).toEqual({ kind: 'pending' });
    expect(getStageInfo('GM', request)).toEqual({ kind: 'not_reached' });
    expect(getStageInfo('DIRECTOR', request)).toEqual({ kind: 'not_reached' });
  });

  it('leaves Procurement out of the decision-based timeline entirely (processed_by/processed_at are read separately)', () => {
    // Full happy-path history through all four pipeline stages, now
    // PROCESSED - APPROVAL_STAGES has no PROCUREMENT entry, and every
    // pipeline stage must still resolve to its own single decision.
    const request = requestWithDecisions('PROCESSED', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T10:00:00Z'),
      decision('ACCOUNTS', 'VERIFIED', '2025-01-01T11:00:00Z'),
      decision('GM', 'RECOMMENDED', '2025-01-01T12:00:00Z'),
      decision('DIRECTOR', 'APPROVED', '2025-01-01T13:00:00Z'),
    ]);
    request.processed_by = 42;
    request.processed_at = '2025-01-01T14:00:00Z';

    expect(APPROVAL_STAGES.some((s) => (s.stage as string) === 'PROCUREMENT')).toBe(false);
    for (const stage of PIPELINE_STAGES) {
      expect(getStageInfo(stage, request).kind).toBe('decided');
    }
  });
});

describe('findRejection', () => {
  it('returns undefined when the request is not currently REJECTED', () => {
    const request = requestWithDecisions('PENDING_ACCOUNTS', [
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T10:00:00Z'),
    ]);

    expect(findRejection(request)).toBeUndefined();
  });

  it('returns the rejection reason on a first-time rejection', () => {
    const rejection = decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z', 'Missing quote');
    const request = requestWithDecisions('REJECTED', [rejection]);

    expect(findRejection(request)).toBe(rejection);
  });

  it('returns the most recent rejection across stages, not the first one ever recorded', () => {
    const staleRejection = decision(
      'DEPARTMENT_HEAD',
      'REJECTED',
      '2025-01-01T10:00:00Z',
      'Old reason - already corrected'
    );
    const currentRejection = decision(
      'ACCOUNTS',
      'REJECTED',
      '2025-01-01T12:00:00Z',
      'Budget code no longer active'
    );
    const request = requestWithDecisions('REJECTED', [
      staleRejection,
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T11:00:00Z'),
      currentRejection,
    ]);

    const result = findRejection(request);

    expect(result).toBe(currentRejection);
    expect(result?.stage).toBe('ACCOUNTS');
    expect(result?.reason).toBe('Budget code no longer active');
  });

  it('preserves the older, superseded rejection in request.decisions rather than dropping it', () => {
    const request = requestWithDecisions('REJECTED', [
      decision('DEPARTMENT_HEAD', 'REJECTED', '2025-01-01T10:00:00Z', 'Old reason'),
      decision('DEPARTMENT_HEAD', 'APPROVED', '2025-01-01T11:00:00Z'),
      decision('ACCOUNTS', 'REJECTED', '2025-01-01T12:00:00Z', 'Current reason'),
    ]);

    findRejection(request);

    expect(request.decisions).toHaveLength(3);
    expect(
      request.decisions.some(
        (d) => d.stage === 'DEPARTMENT_HEAD' && d.decision === 'REJECTED' && d.reason === 'Old reason'
      )
    ).toBe(true);
  });
});
