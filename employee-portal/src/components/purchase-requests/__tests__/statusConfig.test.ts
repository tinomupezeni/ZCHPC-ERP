import { describe, expect, it } from 'vitest';
import {
  STATUS_LABELS,
  STATUS_MESSAGES,
  getActionBucket,
  getEditCtaLabel,
  getProgressLabel,
  getWaitingHelperLine,
  isActionRequired,
  statusTone,
} from '../statusConfig';
import type { PurchaseRequestStatus } from '@/types/purchase-request.types';

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
});
