import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { toast } from 'sonner';
import type { Employee } from '@/types/auth.types';
import type { PurchaseRequestListItem } from '@/types/purchase-request.types';

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ employee: fakeEmployee }),
}));

// The create/edit form is exercised extensively elsewhere (its own test
// suite); stubbing it out here keeps this page's tests focused on the list
// + delete-confirmation flow and avoids needing a real getCategories() call.
vi.mock('@/components/purchase-requests', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/components/purchase-requests')>();
  return { ...actual, PurchaseRequestForm: () => null };
});

vi.mock('@/services/purchase-request.service', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/services/purchase-request.service')>();
  return {
    ...actual,
    purchaseRequestService: {
      getMyRequests: vi.fn(),
      getCategories: vi.fn(),
      getRequest: vi.fn(),
      createRequest: vi.fn(),
      submitRequest: vi.fn(),
      updateItems: vi.fn(),
      deleteRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');
const { PurchaseRequestsPage } = await import('../PurchaseRequestsPage');

const fakeEmployee: Employee = {
  id: 1,
  employee_id: 'EMP001',
  first_name: 'Richard',
  surname: 'Matsika',
  full_name: 'Richard Matsika',
  email: 'richard@zchpc.test',
  phone: '+263771234567',
  gender: 'M',
  date_of_birth: null,
  date_joined: '2024-01-01',
  department_name: 'IT Department',
  position_title: 'Systems Administrator',
  role_name: 'REGULAR_STAFF',
  role_display_name: 'Regular Staff',
  employee_type: 'FULL_TIME',
  is_active: true,
  leave_days_entitled: 21,
};

function draftRequest(overrides: Partial<PurchaseRequestListItem> = {}): PurchaseRequestListItem {
  return {
    id: 1,
    requisition_number: 'PR-0001',
    requester_id: 1,
    requester_name: 'Richard Matsika',
    department_id: 1,
    department_name: 'IT Department',
    status: 'DRAFT',
    total_estimated_cost: '800.00',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PurchaseRequestsPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(purchaseRequestService.getCategories).mockResolvedValue([]);
});

describe('PurchaseRequestsPage - delete draft confirmation', () => {
  it('opens a confirmation dialog naming the draft before deleting anything', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([draftRequest()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('PR-0001');

    // Anchored: the card itself has role="button" too, and its accessible
    // name is derived from all of its text content (including this CTA's
    // own label), so an unanchored match would be ambiguous - the same
    // reason PurchaseRequestsList.test.tsx anchors its CTA queries.
    await user.click(screen.getByRole('button', { name: /^delete draft$/i }));

    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText('Delete draft?')).toBeInTheDocument();
    expect(within(dialog).getByText('PR-0001')).toBeInTheDocument();
    expect(purchaseRequestService.deleteRequest).not.toHaveBeenCalled();
  });

  it('cancelling the dialog does not call the delete API and leaves the request in place', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([draftRequest()]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('PR-0001');

    await user.click(screen.getByRole('button', { name: /^delete draft$/i }));
    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(purchaseRequestService.deleteRequest).not.toHaveBeenCalled();
    expect(screen.getByText('PR-0001')).toBeInTheDocument();
  });
});

describe('PurchaseRequestsPage - successful deletion', () => {
  it('calls the delete API, removes the request from the list, and shows a success toast', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([
      draftRequest({ id: 1, requisition_number: 'PR-0001' }),
      draftRequest({ id: 2, requisition_number: 'PR-0002', status: 'PENDING_DEPARTMENT_HEAD' }),
    ]);
    vi.mocked(purchaseRequestService.deleteRequest).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('PR-0001');

    await user.click(screen.getByRole('button', { name: /^delete draft$/i }));
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: /^delete draft$/i }));

    await waitFor(() => expect(purchaseRequestService.deleteRequest).toHaveBeenCalledWith(1));
    await waitFor(() => expect(screen.queryByText('PR-0001')).not.toBeInTheDocument());
    expect(screen.getByText('PR-0002')).toBeInTheDocument();
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('PR-0001'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestsPage - failed deletion', () => {
  it('shows an error toast and leaves the request visible when the delete call fails', async () => {
    vi.mocked(purchaseRequestService.getMyRequests).mockResolvedValue([draftRequest()]);
    vi.mocked(purchaseRequestService.deleteRequest).mockRejectedValue({
      response: { data: { error: 'Cannot delete a request in status DRAFT', code: 'NOT_DELETABLE' } },
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('PR-0001');

    await user.click(screen.getByRole('button', { name: /^delete draft$/i }));
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: /^delete draft$/i }));

    await waitFor(() => expect(purchaseRequestService.deleteRequest).toHaveBeenCalledTimes(1));
    expect(toast.error).toHaveBeenCalledWith('Cannot delete a request in status DRAFT');
    expect(screen.getByText('PR-0001')).toBeInTheDocument();
  });
});
