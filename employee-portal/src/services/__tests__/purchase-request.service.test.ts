import { describe, expect, it, vi, beforeEach } from 'vitest';

const getMock = vi.fn();
const postMock = vi.fn();
const patchMock = vi.fn();
const deleteMock = vi.fn();

vi.mock('../api', () => ({
  default: {
    get: (...args: unknown[]) => getMock(...args),
    post: (...args: unknown[]) => postMock(...args),
    patch: (...args: unknown[]) => patchMock(...args),
    delete: (...args: unknown[]) => deleteMock(...args),
  },
}));

// Imported after the mock so the service binds to the mocked axios instance.
const { purchaseRequestService, getPurchaseRequestErrorMessage } = await import(
  '../purchase-request.service'
);

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  patchMock.mockReset();
  deleteMock.mockReset();
});

describe('purchaseRequestService', () => {
  it('fetches categories from the F11-A category endpoint', async () => {
    getMock.mockResolvedValue({ data: [{ id: 1, name: 'IT Consumables' }] });

    const result = await purchaseRequestService.getCategories();

    expect(getMock).toHaveBeenCalledWith('/procurement/purchase-request-categories/');
    expect(result).toEqual([{ id: 1, name: 'IT Consumables' }]);
  });

  it('lists only the caller\'s own requests via scope=mine', async () => {
    getMock.mockResolvedValue({ data: [] });

    await purchaseRequestService.getMyRequests();

    expect(getMock).toHaveBeenCalledWith('/procurement/requests/', {
      params: { scope: 'mine' },
    });
  });

  it('fetches a single request by id', async () => {
    getMock.mockResolvedValue({ data: { id: 42 } });

    await purchaseRequestService.getRequest(42);

    expect(getMock).toHaveBeenCalledWith('/procurement/requests/42/');
  });

  it('creates a request against /procurement/requests/', async () => {
    postMock.mockResolvedValue({ data: { id: 7 } });

    await purchaseRequestService.createRequest({
      items: [
        {
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });

    expect(postMock).toHaveBeenCalledWith('/procurement/requests/', {
      items: [
        {
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });
  });

  it('never sends budget_code_id in the create payload shape', async () => {
    postMock.mockResolvedValue({ data: { id: 7 } });

    await purchaseRequestService.createRequest({
      items: [
        {
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });

    const [, body] = postMock.mock.calls[0] as [string, { items: object[] }];
    for (const item of body.items) {
      expect(item).not.toHaveProperty('budget_code_id');
    }
  });

  it('submits a request against requests/{id}/submit/', async () => {
    postMock.mockResolvedValue({ data: { id: 7, status: 'PENDING_DEPARTMENT_HEAD' } });

    await purchaseRequestService.submitRequest(7);

    expect(postMock).toHaveBeenCalledWith('/procurement/requests/7/submit/');
  });

  it('deletes a draft via DELETE requests/{id}/ (Slice 4)', async () => {
    deleteMock.mockResolvedValue({ data: undefined });

    await purchaseRequestService.deleteRequest(7);

    expect(deleteMock).toHaveBeenCalledWith('/procurement/requests/7/');
  });

  it('propagates a failed delete rather than swallowing it', async () => {
    const error = { response: { data: { error: 'Cannot delete', code: 'NOT_DELETABLE' } } };
    deleteMock.mockRejectedValue(error);

    await expect(purchaseRequestService.deleteRequest(7)).rejects.toBe(error);
  });

  it('replaces item collection via PATCH requests/{id}/ (Slice 2 edit)', async () => {
    patchMock.mockResolvedValue({ data: { id: 7, status: 'DRAFT' } });

    await purchaseRequestService.updateItems(7, {
      items: [
        {
          id: 1,
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });

    expect(patchMock).toHaveBeenCalledWith('/procurement/requests/7/', {
      items: [
        {
          id: 1,
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });
  });

  it('lists the department-head review queue via scope=pending-department-head (F17)', async () => {
    getMock.mockResolvedValue({ data: [] });

    await purchaseRequestService.getPendingDepartmentHeadRequests();

    expect(getMock).toHaveBeenCalledWith('/procurement/requests/', {
      params: { scope: 'pending-department-head' },
    });
  });

  it('propagates a failed queue load (e.g. a 403) rather than swallowing it (F17)', async () => {
    const error = { response: { status: 403, data: { code: 'PERMISSION_DENIED' } } };
    getMock.mockRejectedValue(error);

    await expect(purchaseRequestService.getPendingDepartmentHeadRequests()).rejects.toBe(error);
  });

  it('approves a request as department head via POST .../department-head/approve/ (F17)', async () => {
    postMock.mockResolvedValue({ data: { id: 7, status: 'PENDING_ACCOUNTS' } });

    await purchaseRequestService.approveByDepartmentHead(7);

    expect(postMock).toHaveBeenCalledWith('/procurement/requests/7/department-head/approve/');
  });

  it('rejects a request with a reason via POST .../reject/ (F17)', async () => {
    postMock.mockResolvedValue({ data: { id: 7, status: 'REJECTED' } });

    await purchaseRequestService.rejectRequest(7, 'Budget code no longer active');

    expect(postMock).toHaveBeenCalledWith('/procurement/requests/7/reject/', {
      reason: 'Budget code no longer active',
    });
  });

  it('never sends budget_code_id in the update payload shape', async () => {
    patchMock.mockResolvedValue({ data: { id: 7, status: 'DRAFT' } });

    await purchaseRequestService.updateItems(7, {
      items: [
        {
          description: 'Laptop',
          quantity: 1,
          expected_delivery_period: '2 weeks',
          estimated_cost: '800.00',
          category_id: 3,
        },
      ],
    });

    const [, body] = patchMock.mock.calls[0] as [string, { items: object[] }];
    for (const item of body.items) {
      expect(item).not.toHaveProperty('budget_code_id');
    }
  });
});

describe('getPurchaseRequestErrorMessage', () => {
  it('prefers the domain error shape { error, code }', () => {
    const message = getPurchaseRequestErrorMessage(
      { response: { data: { error: 'Category is inactive', code: 'CATEGORY_INACTIVE' } } },
      'fallback'
    );
    expect(message).toBe('Category is inactive');
  });

  it('falls back to DRF { detail } errors', () => {
    const message = getPurchaseRequestErrorMessage(
      { response: { data: { detail: 'Authentication credentials were not provided.' } } },
      'fallback'
    );
    expect(message).toBe('Authentication credentials were not provided.');
  });

  it('extracts a message from DRF field-validation error arrays', () => {
    const message = getPurchaseRequestErrorMessage(
      { response: { data: { description: ['This field may not be blank.'] } } },
      'fallback'
    );
    expect(message).toBe('This field may not be blank.');
  });

  it('returns the fallback for a network error with no response body', () => {
    const message = getPurchaseRequestErrorMessage(new Error('Network Error'), 'fallback');
    expect(message).toBe('fallback');
  });
});
