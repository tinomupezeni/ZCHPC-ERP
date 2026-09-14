import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { toast } from 'sonner';
import { PurchaseRequestForm } from '../PurchaseRequestForm';
import type { Employee } from '@/types/auth.types';
import type { PurchaseRequest } from '@/types/purchase-request.types';

vi.mock('@/components/ui/select', () => import('@/test/mocks/ui-select'));

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('@/services/purchase-request.service', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/services/purchase-request.service')>();
  return {
    ...actual,
    purchaseRequestService: {
      getCategories: vi.fn(),
      getMyRequests: vi.fn(),
      getRequest: vi.fn(),
      createRequest: vi.fn(),
      submitRequest: vi.fn(),
    },
  };
});

const { purchaseRequestService } = await import('@/services/purchase-request.service');

const employee: Employee = {
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

const categories = [
  { id: 1, name: 'IT Consumables' },
  { id: 2, name: 'Stationery & Printing' },
];

function baseRequest(overrides: Partial<PurchaseRequest> = {}): PurchaseRequest {
  return {
    id: 100,
    requisition_number: 'PR-0100',
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
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

async function fillFirstItem(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Item Description'), 'Laptop');
  const quantity = screen.getByLabelText('Quantity');
  await user.clear(quantity);
  await user.type(quantity, '2');
  await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
  await user.type(screen.getByLabelText('Estimated Cost (USD)'), '400');
  await user.selectOptions(screen.getByLabelText('Category'), '1');
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(purchaseRequestService.getCategories).mockResolvedValue(categories);
});

describe('PurchaseRequestForm - category loading', () => {
  it('loads and displays categories from the F11-A endpoint', async () => {
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);

    await waitFor(() =>
      expect(purchaseRequestService.getCategories).toHaveBeenCalledTimes(1)
    );
    expect(await screen.findByRole('option', { name: 'IT Consumables' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Stationery & Printing' })).toBeInTheDocument();
  });

  it('shows a useful error and lets the employee retry when the category API fails', async () => {
    const user = userEvent.setup();
    vi.mocked(purchaseRequestService.getCategories).mockReset();
    vi.mocked(purchaseRequestService.getCategories)
      .mockRejectedValueOnce({ response: { data: { detail: 'Service unavailable' } } })
      .mockResolvedValueOnce(categories);

    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);

    expect(await screen.findByText('Service unavailable')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() =>
      expect(purchaseRequestService.getCategories).toHaveBeenCalledTimes(2)
    );
    expect(await screen.findByRole('option', { name: 'IT Consumables' })).toBeInTheDocument();
  });
});

describe('PurchaseRequestForm - requester identity', () => {
  it('shows read-only requester info with no editable requester field', async () => {
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    expect(await screen.findByText('Richard Matsika')).toBeInTheDocument();
    expect(screen.queryByLabelText(/requested by/i)).not.toBeInTheDocument();
  });
});

describe('PurchaseRequestForm - line items', () => {
  it('starts with exactly one item and supports adding/removing items independently', async () => {
    const user = userEvent.setup();
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });

    expect(screen.getAllByLabelText('Item Description')).toHaveLength(1);

    await user.click(screen.getByRole('button', { name: /add item/i }));
    expect(screen.getAllByLabelText('Item Description')).toHaveLength(2);

    const descriptions = screen.getAllByLabelText('Item Description');
    await user.type(descriptions[0], 'Laptop');
    await user.type(descriptions[1], 'Mouse');
    expect((descriptions[0] as HTMLInputElement).value).toBe('Laptop');
    expect((descriptions[1] as HTMLInputElement).value).toBe('Mouse');
  });
});

describe('PurchaseRequestForm - validation', () => {
  const cases: { name: string; break: (user: ReturnType<typeof userEvent.setup>) => Promise<void> }[] = [
    {
      name: 'missing description',
      break: async (user) => {
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '2');
        await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
        await user.type(screen.getByLabelText('Estimated Cost (USD)'), '400');
        await user.selectOptions(screen.getByLabelText('Category'), '1');
      },
    },
    {
      name: 'quantity <= 0',
      break: async (user) => {
        await user.type(screen.getByLabelText('Item Description'), 'Laptop');
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '0');
        await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
        await user.type(screen.getByLabelText('Estimated Cost (USD)'), '400');
        await user.selectOptions(screen.getByLabelText('Category'), '1');
      },
    },
    {
      name: 'missing expected delivery period',
      break: async (user) => {
        await user.type(screen.getByLabelText('Item Description'), 'Laptop');
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '2');
        await user.type(screen.getByLabelText('Estimated Cost (USD)'), '400');
        await user.selectOptions(screen.getByLabelText('Category'), '1');
      },
    },
    {
      name: 'missing estimated cost',
      break: async (user) => {
        await user.type(screen.getByLabelText('Item Description'), 'Laptop');
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '2');
        await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
        await user.selectOptions(screen.getByLabelText('Category'), '1');
      },
    },
    {
      name: 'negative estimated cost',
      break: async (user) => {
        await user.type(screen.getByLabelText('Item Description'), 'Laptop');
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '2');
        await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
        await user.type(screen.getByLabelText('Estimated Cost (USD)'), '-5');
        await user.selectOptions(screen.getByLabelText('Category'), '1');
      },
    },
    {
      name: 'missing category',
      break: async (user) => {
        await user.type(screen.getByLabelText('Item Description'), 'Laptop');
        await user.clear(screen.getByLabelText('Quantity'));
        await user.type(screen.getByLabelText('Quantity'), '2');
        await user.type(screen.getByLabelText('Expected Delivery Period'), '2 weeks');
        await user.type(screen.getByLabelText('Estimated Cost (USD)'), '400');
      },
    },
  ];

  for (const testCase of cases) {
    it(`blocks submission and does not call the create API when ${testCase.name}`, async () => {
      const user = userEvent.setup();
      render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
      await screen.findByRole('option', { name: 'IT Consumables' });

      await testCase.break(user);
      await user.click(screen.getByRole('button', { name: /submit purchase requisition/i }));

      expect(purchaseRequestService.createRequest).not.toHaveBeenCalled();
    });
  }

  it('blocks submission of a pristine form with no usable line item filled in', async () => {
    const user = userEvent.setup();
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });

    await user.click(screen.getByRole('button', { name: /submit purchase requisition/i }));

    expect(purchaseRequestService.createRequest).not.toHaveBeenCalled();
    expect(screen.getByText('Description is required')).toBeInTheDocument();
  });
});

describe('PurchaseRequestForm - totals', () => {
  it('computes quantity x estimated cost per line without floating-point artifacts', async () => {
    const user = userEvent.setup();
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });

    const quantity = screen.getByLabelText('Quantity');
    await user.clear(quantity);
    await user.type(quantity, '3');
    await user.type(screen.getByLabelText('Estimated Cost (USD)'), '0.10');

    const lineTotalLabel = await screen.findByText('Line total:');
    expect(lineTotalLabel.closest('div')).toHaveTextContent('$0.30');
  });

  it('sums multiple items into a correct grand total', async () => {
    const user = userEvent.setup();
    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });

    await fillFirstItem(user); // 2 x 400 = 800

    await user.click(screen.getByRole('button', { name: /add item/i }));
    const descriptions = screen.getAllByLabelText('Item Description');
    const quantities = screen.getAllByLabelText('Quantity');
    const costs = screen.getAllByLabelText('Estimated Cost (USD)');

    await user.type(descriptions[1], 'Mouse');
    await user.clear(quantities[1]);
    await user.type(quantities[1], '5');
    await user.type(costs[1], '10'); // 5 x 10 = 50

    expect(
      screen.getByText('Total Estimated Cost').closest('div')
    ).toHaveTextContent('$850.00');
  });
});

describe('PurchaseRequestForm - create payload', () => {
  it('sends category_id and never budget_code_id', async () => {
    const user = userEvent.setup();
    vi.mocked(purchaseRequestService.createRequest).mockResolvedValue(baseRequest());
    vi.mocked(purchaseRequestService.submitRequest).mockResolvedValue(
      baseRequest({ status: 'PENDING_DEPARTMENT_HEAD' })
    );

    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });
    await fillFirstItem(user);

    await user.click(screen.getByRole('button', { name: /submit purchase requisition/i }));

    await waitFor(() => expect(purchaseRequestService.createRequest).toHaveBeenCalledTimes(1));
    const payload = vi.mocked(purchaseRequestService.createRequest).mock.calls[0][0];
    expect(payload.items[0]).toMatchObject({ category_id: 1 });
    expect(payload.items[0]).not.toHaveProperty('budget_code_id');
  });
});

describe('PurchaseRequestForm - create then submit', () => {
  it('calls create before submit, in order, and reports success', async () => {
    const user = userEvent.setup();
    const created = baseRequest();
    const submitted = baseRequest({ status: 'PENDING_DEPARTMENT_HEAD' });
    vi.mocked(purchaseRequestService.createRequest).mockResolvedValue(created);
    vi.mocked(purchaseRequestService.submitRequest).mockResolvedValue(submitted);
    const onSubmitted = vi.fn();

    render(<PurchaseRequestForm employee={employee} onSubmitted={onSubmitted} />);
    await screen.findByRole('option', { name: 'IT Consumables' });
    await fillFirstItem(user);
    await user.click(screen.getByRole('button', { name: /submit purchase requisition/i }));

    await waitFor(() => expect(onSubmitted).toHaveBeenCalledWith(submitted));

    const createOrder = vi.mocked(purchaseRequestService.createRequest).mock.invocationCallOrder[0];
    const submitOrder = vi.mocked(purchaseRequestService.submitRequest).mock.invocationCallOrder[0];
    expect(createOrder).toBeLessThan(submitOrder);
    expect(purchaseRequestService.submitRequest).toHaveBeenCalledWith(created.id);
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining(submitted.requisition_number));
  });
});

describe('PurchaseRequestForm - submit failure recovery', () => {
  it('does not claim success, preserves the draft reference, and retries without re-creating', async () => {
    const user = userEvent.setup();
    const created = baseRequest();
    vi.mocked(purchaseRequestService.createRequest).mockResolvedValue(created);
    vi.mocked(purchaseRequestService.submitRequest)
      .mockRejectedValueOnce(new Error('network error'))
      .mockResolvedValueOnce(baseRequest({ status: 'PENDING_DEPARTMENT_HEAD' }));

    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });
    await fillFirstItem(user);
    await user.click(screen.getByRole('button', { name: /submit purchase requisition/i }));

    await waitFor(() =>
      expect(screen.getByText(/was created but has not been submitted/i)).toBeInTheDocument()
    );
    expect(toast.success).not.toHaveBeenCalled();
    expect(screen.getByText(new RegExp(created.requisition_number))).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /retry submission/i }));

    await waitFor(() =>
      expect(purchaseRequestService.submitRequest).toHaveBeenCalledTimes(2)
    );
    expect(purchaseRequestService.createRequest).toHaveBeenCalledTimes(1);
  });
});

describe('PurchaseRequestForm - double submission', () => {
  it('does not create the request twice when the submit control is triggered rapidly', async () => {
    const user = userEvent.setup();
    let resolveCreate: (value: PurchaseRequest) => void = () => {};
    vi.mocked(purchaseRequestService.createRequest).mockReturnValue(
      new Promise((resolve) => {
        resolveCreate = resolve;
      })
    );

    render(<PurchaseRequestForm employee={employee} onSubmitted={vi.fn()} />);
    await screen.findByRole('option', { name: 'IT Consumables' });
    await fillFirstItem(user);

    const submitButton = screen.getByRole('button', { name: /submit purchase requisition/i });
    await user.click(submitButton);
    await user.click(submitButton);
    await user.click(submitButton);

    expect(purchaseRequestService.createRequest).toHaveBeenCalledTimes(1);
    resolveCreate(baseRequest());
  });
});
