import { describe, expect, it } from 'vitest';
import { availabilityFor, HIDDEN_PATHS } from '../navAvailability';

describe('availabilityFor', () => {
  it('covers a listed path and its sub-paths only', () => {
    expect(availabilityFor('/portal/employees')).toBe('hidden');
    expect(availabilityFor('/portal/employees/12')).toBe('hidden');
    expect(availabilityFor('/portal/leave')).toBe('not-available');
    expect(availabilityFor('/portal/leave/requests')).toBe('not-available');
    expect(availabilityFor('/portal/payslips')).toBeUndefined();
    expect(availabilityFor('/portal/attendance')).toBeUndefined();
    expect(availabilityFor('/portal/leave-archive')).toBeUndefined();
    expect(availabilityFor('/portal')).toBeUndefined();
  });

  it('gives only the hidden links a fallback route', () => {
    expect(HIDDEN_PATHS).toHaveLength(9);
    expect(HIDDEN_PATHS).not.toContain('/portal/leave');
    expect(HIDDEN_PATHS).not.toContain('/portal/payslips');
  });
});
