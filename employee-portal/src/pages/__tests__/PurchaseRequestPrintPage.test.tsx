import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import type { PurchaseRequest } from '@/types/purchase-request.types';

vi.mock('@/services/purchase-request.service', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/services/purchase-request.service')>();
  return {
    ...actual,
    purchaseRequestService: {
      getRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestPrintPage } = await import('../PurchaseRequestPrintPage');

function processedRequest(overrides: Partial<PurchaseRequest> = {}): PurchaseRequest {
  return {
    id: 43,
    requisition_number: 'PR-0043',
    requester_id: 3,
    requester_name: 'Riley Requester',
    department_id: 2,
    department_name: 'IT Department',
    designation: 'Systems Developer',
    contact: '+263771111111',
    status: 'PROCESSED',
    total_estimated_cost: '2400.00',
    items: [
      {
        id: 1,
        description: 'Laptop',
        quantity: 2,
        expected_delivery_period: '2 weeks',
        estimated_cost: '1200.00',
        budget_code_id: 42,
        category: { id: 5, name: 'IT Equipment', is_active: true },
      },
    ],
    decisions: [
      { id: 1, stage: 'DEPARTMENT_HEAD', decision: 'APPROVED', actor_id: 11, reason: '', created_at: '2025-01-01T09:00:00Z' },
      { id: 2, stage: 'ACCOUNTS', decision: 'VERIFIED', actor_id: 12, reason: '', created_at: '2025-01-01T10:00:00Z' },
      { id: 3, stage: 'GM', decision: 'RECOMMENDED', actor_id: 13, reason: '', created_at: '2025-01-01T11:00:00Z' },
      { id: 4, stage: 'DIRECTOR', decision: 'APPROVED', actor_id: 14, reason: '', created_at: '2025-01-01T12:00:00Z' },
    ],
    processed_by: 15,
    processed_at: '2025-01-02T09:00:00Z',
    purchase_order_number: 'PO-2026-00777',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T09:00:00Z',
    ...overrides,
  };
}

function renderAt(id: number) {
  return render(
    <MemoryRouter initialEntries={[`/portal/purchase-requests/${id}/print`]}>
      <Routes>
        <Route path="/portal/purchase-requests/:id/print" element={<PurchaseRequestPrintPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('PurchaseRequestPrintPage', () => {
  it('shows the requisition number in the form header', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    expect(await screen.findByText('PR-0043')).toBeInTheDocument();
  });

  it('shows requester details from Section A', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    expect(screen.getByText('Riley Requester')).toBeInTheDocument();
    expect(screen.getByText('Systems Developer')).toBeInTheDocument();
    expect(screen.getByText('+263771111111')).toBeInTheDocument();
    expect(screen.getByText('IT Department')).toBeInTheDocument();
  });

  it('shows item description, quantity, delivery period, line total and the grand total', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    const row = screen.getByText('Laptop').closest('tr')!;
    expect(within(row).getByText('2')).toBeInTheDocument();
    expect(within(row).getByText('2 weeks')).toBeInTheDocument();
    expect(within(row).getByText('2,400.00')).toBeInTheDocument(); // 2 x 1200.00 line total
    const totalRow = screen.getByText('Total Estimated Costs').closest('tr')!;
    expect(within(totalRow).getByText('2,400.00')).toBeInTheDocument();
  });

  it('pads the item table to the minimum number of rows for a single-item request', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    const table = screen.getByText('Item Description').closest('table')!;
    const bodyRows = within(table).getAllByRole('row').slice(1); // drop the header row
    // 7 minimum item rows (1 real + 6 blank) + the Total row.
    expect(bodyRows.length).toBe(8);
  });

  it('does not pad away real items when there are more than the minimum row count', async () => {
    const manyItems = Array.from({ length: 9 }, (_, i) => ({
      id: i + 1,
      description: `Item ${i + 1}`,
      quantity: 1,
      expected_delivery_period: '1 week',
      estimated_cost: '10.00',
      budget_code_id: 1,
      category: null,
    }));
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      processedRequest({ items: manyItems, total_estimated_cost: '90.00' })
    );
    renderAt(43);

    await screen.findByText('PR-0043');
    expect(screen.getByText('Item 9')).toBeInTheDocument();
    const table = screen.getByText('Item Description').closest('table')!;
    const bodyRows = within(table).getAllByRole('row').slice(1);
    expect(bodyRows.length).toBe(10); // 9 real rows + the Total row, no blank padding
  });

  it('shows the employee-facing category, never a fabricated GL/budget code, in the Budget Code column', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    expect(screen.getByText('IT Equipment')).toBeInTheDocument();
    // No plausible-looking fabricated GL code format anywhere on the page.
    expect(screen.queryByText(/\d{5}\/\d{2}\/\d{3}/)).not.toBeInTheDocument();
  });

  it('shows the real Purchase Order number and processed date in Section D', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    expect(screen.getByText('PO-2026-00777')).toBeInTheDocument();
    expect(screen.getByText('2 Jan 2025')).toBeInTheDocument();
  });

  it('shows the full approval history (Department Head through Director)', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(processedRequest());
    renderAt(43);

    await screen.findByText('PR-0043');
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Recommended')).toBeInTheDocument();
    expect(screen.getAllByText('Approved').length).toBe(2); // Department Head + Director
  });

  it('shows a not-yet-available message instead of the form for a request that has not been processed', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockResolvedValue(
      processedRequest({ status: 'PENDING_PROCUREMENT', purchase_order_number: null, processed_at: null })
    );
    renderAt(43);

    expect(
      await screen.findByText(/becomes available once Procurement has finished processing/i)
    ).toBeInTheDocument();
    expect(screen.queryByText('Section A: Details of Officer Requesting')).not.toBeInTheDocument();
  });

  it('shows an error message when the request fails to load', async () => {
    vi.mocked(purchaseRequestService.getRequest).mockRejectedValue(new Error('Network Error'));
    renderAt(43);

    expect(await screen.findByText('Failed to load purchase request')).toBeInTheDocument();
  });
});
