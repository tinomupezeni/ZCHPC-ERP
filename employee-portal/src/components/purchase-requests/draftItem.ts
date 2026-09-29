import type { PurchaseRequest } from '@/types/purchase-request.types';

export interface DraftItem {
  key: string;
  /** The persisted item id this draft corresponds to (Slice 2 edit mode). Undefined for a new, not-yet-saved item. */
  id?: number;
  description: string;
  quantity: string;
  expected_delivery_period: string;
  estimated_cost: string;
  category_id: string;
}

export type DraftItemErrors = Partial<Record<keyof Omit<DraftItem, 'key' | 'id'>, string>>;

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

/**
 * Seed draft items from an existing request's items (Slice 2 edit mode).
 *
 * A category is only pre-selected when it's still active - the picker only
 * ever offers active categories, so pre-filling an inactive one would select
 * a value the dropdown doesn't actually list. Left blank instead, so the
 * employee picks a currently-valid category rather than the form silently
 * carrying forward a retired one.
 */
export function itemsFromExistingRequest(request: PurchaseRequest): DraftItem[] {
  if (request.items.length === 0) return [createEmptyItem()];
  return request.items.map((item) => ({
    ...createEmptyItem(),
    id: item.id,
    description: item.description,
    quantity: String(item.quantity),
    expected_delivery_period: item.expected_delivery_period,
    estimated_cost: item.estimated_cost,
    category_id: item.category?.is_active ? String(item.category.id) : '',
  }));
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
