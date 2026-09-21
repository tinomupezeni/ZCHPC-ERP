import { describe, expect, it } from 'vitest';
import {
  createEmptyItem,
  formatCents,
  itemsFromExistingRequest,
  lineTotalCents,
  type DraftItem,
} from '../draftItem';
import type { PurchaseRequest } from '@/types/purchase-request.types';

function item(overrides: Partial<DraftItem> = {}): DraftItem {
  return { ...createEmptyItem(), ...overrides };
}

function baseRequest(overrides: Partial<PurchaseRequest> = {}): PurchaseRequest {
  return {
    id: 1,
    requisition_number: 'PR-0001',
    requester_id: 1,
    requester_name: 'Richard Matsika',
    department_id: 1,
    department_name: 'IT Department',
    designation: 'Systems Administrator',
    contact: '+263771234567',
    status: 'DRAFT',
    total_estimated_cost: '800.00',
    items: [],
    decisions: [],
    processed_by: null,
    processed_at: null,
    purchase_order_number: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('itemsFromExistingRequest', () => {
  it('maps each item field, carrying the item id and category id forward as strings for the form', () => {
    const request = baseRequest({
      items: [
        {
          id: 55,
          description: 'Laptop',
          quantity: 2,
          expected_delivery_period: '1 week',
          estimated_cost: '400.00',
          budget_code_id: 9,
          category: { id: 3, name: 'IT Consumables', is_active: true },
        },
      ],
    });

    const [item] = itemsFromExistingRequest(request);

    expect(item.id).toBe(55);
    expect(item.description).toBe('Laptop');
    expect(item.quantity).toBe('2');
    expect(item.expected_delivery_period).toBe('1 week');
    expect(item.estimated_cost).toBe('400.00');
    expect(item.category_id).toBe('3');
  });

  it('leaves category_id blank when the item has no category', () => {
    const request = baseRequest({
      items: [
        {
          id: 55,
          description: 'Laptop',
          quantity: 2,
          expected_delivery_period: '1 week',
          estimated_cost: '400.00',
          budget_code_id: 9,
          category: null,
        },
      ],
    });

    const [item] = itemsFromExistingRequest(request);
    expect(item.category_id).toBe('');
  });

  it('leaves category_id blank when the item\'s category is no longer active', () => {
    const request = baseRequest({
      items: [
        {
          id: 55,
          description: 'Laptop',
          quantity: 2,
          expected_delivery_period: '1 week',
          estimated_cost: '400.00',
          budget_code_id: 9,
          category: { id: 3, name: 'Retired Category', is_active: false },
        },
      ],
    });

    const [item] = itemsFromExistingRequest(request);
    expect(item.category_id).toBe('');
  });

  it('maps multiple items in order, each with its own key', () => {
    const request = baseRequest({
      items: [
        {
          id: 1,
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '1 week',
          estimated_cost: '400.00',
          budget_code_id: 9,
          category: { id: 3, name: 'IT Consumables', is_active: true },
        },
        {
          id: 2,
          description: 'Mouse',
          quantity: 5,
          expected_delivery_period: '2 weeks',
          estimated_cost: '10.00',
          budget_code_id: 9,
          category: { id: 3, name: 'IT Consumables', is_active: true },
        },
      ],
    });

    const items = itemsFromExistingRequest(request);
    expect(items).toHaveLength(2);
    expect(items[0].description).toBe('Laptop');
    expect(items[1].description).toBe('Mouse');
    expect(items[0].key).not.toBe(items[1].key);
  });

  it('falls back to a single empty item when the request has no items', () => {
    const request = baseRequest({ items: [] });
    const items = itemsFromExistingRequest(request);
    expect(items).toHaveLength(1);
    expect(items[0].id).toBeUndefined();
    expect(items[0].description).toBe('');
    expect(items[0].category_id).toBe('');
  });
});

describe('lineTotalCents (regression: quantity x estimated unit cost)', () => {
  // estimated_cost is a per-unit price - the create/edit form's own
  // line-total math has always multiplied by quantity here (this predates
  // the "Estimated Unit Cost" label). This suite locks that in, since the
  // backend's total_estimated_cost and PurchaseRequestDetail's line display
  // were separately found to skip the multiplication entirely.
  it('multiplies quantity by unit cost: qty 10 x $1.00 = $10.00 (1000 cents)', () => {
    const cents = lineTotalCents(item({ quantity: '10', estimated_cost: '1.00' }));
    expect(cents).toBe(1000);
    expect(formatCents(cents!)).toBe('$10.00');
  });

  it('computes each line independently for items with different quantities and costs', () => {
    const laptop = lineTotalCents(item({ quantity: '2', estimated_cost: '2000.00' }));
    const mouse = lineTotalCents(item({ quantity: '5', estimated_cost: '150.00' }));
    expect(laptop).toBe(400_000);
    expect(mouse).toBe(75_000);
    expect(formatCents(laptop! + mouse!)).toBe('$4,750.00');
  });

  it('returns 0 for a zero-cost item with a valid quantity, not null', () => {
    expect(lineTotalCents(item({ quantity: '3', estimated_cost: '0.00' }))).toBe(0);
  });

  it('returns null (not a $0 total) when quantity is zero or missing', () => {
    expect(lineTotalCents(item({ quantity: '0', estimated_cost: '1.00' }))).toBeNull();
    expect(lineTotalCents(item({ quantity: '', estimated_cost: '1.00' }))).toBeNull();
  });

  it('returns null when the cost is negative, empty, or not a number', () => {
    expect(lineTotalCents(item({ quantity: '10', estimated_cost: '-1.00' }))).toBeNull();
    expect(lineTotalCents(item({ quantity: '10', estimated_cost: '' }))).toBeNull();
    expect(lineTotalCents(item({ quantity: '10', estimated_cost: 'abc' }))).toBeNull();
  });
});
