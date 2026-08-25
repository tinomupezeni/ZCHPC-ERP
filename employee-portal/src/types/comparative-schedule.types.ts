export interface ComparativeItem { description: string; quantity: string; quotation_one_unit: string; quotation_one_total: string; quotation_two_unit: string; quotation_two_total: string; }
export interface ComparativeSchedule { id: number; schedule_number: string; compliance: Record<string, string>; items: ComparativeItem[]; recommendation: string; status: string; rejection_reason: string; procurement_submitted_at: string; }
export interface CreateComparativeScheduleData { compliance: Record<string, string>; items: ComparativeItem[]; recommendation: string; }
