export interface DraftItem {
  key: string;
  description: string;
  quantity: string;
  expected_delivery_period: string;
  estimated_cost: string;
  category_id: string;
}

export type DraftItemErrors = Partial<Record<keyof Omit<DraftItem, 'key'>, string>>;

export function createEmptyItem(): DraftItem {
  const key =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `item-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return {
    key,
    description: '',
    quantity: '1',
    expected_delivery_period: '',
    estimated_cost: '',
    category_id: '',
  };
}

/** Cents to avoid the float-rounding problems raw dollar math would produce. */
export function lineTotalCents(item: DraftItem): number | null {
  const qty = Number.parseInt(item.quantity, 10);
  const cost = Number.parseFloat(item.estimated_cost);
  if (!Number.isFinite(qty) || qty <= 0 || !Number.isFinite(cost) || cost < 0) {
    return null;
  }
  return Math.round(cost * 100) * qty;
}

export function formatCents(cents: number): string {
  return `$${(cents / 100).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}
