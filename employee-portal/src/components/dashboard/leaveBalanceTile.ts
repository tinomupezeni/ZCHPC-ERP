import { availabilityFor } from '@/components/layout/navAvailability';
import type { Employee } from '@/types/auth.types';
import type { DashboardSummary } from '@/types/dashboard.types';

export const NOT_AVAILABLE_UNIT = 'Not available';

/**
 * Value and unit of a role dashboard's leave-balance tile. While the
 * evaluation marks the tile not available, it shows a dash and "Not
 * available" instead of a figure the API cannot back.
 */
export function leaveBalanceTile(
  data: DashboardSummary | null,
  employee: Employee | null,
  unit: string
): { value: number | string; unit: string } {
  if (availabilityFor('tile:dashboard/leave-balance')) {
    return { value: '—', unit: NOT_AVAILABLE_UNIT };
  }
  return {
    value: data?.leave_balances?.[0]?.available_days ?? employee?.leave_days_entitled ?? 0,
    unit,
  };
}
