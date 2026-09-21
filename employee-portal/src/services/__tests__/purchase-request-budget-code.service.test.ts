import { describe, expect, it, vi, beforeEach } from 'vitest';

vi.mock('../api', () => ({
  default: { get: vi.fn(), put: vi.fn(), post: vi.fn() },
}));

import api from '../api';
import { purchaseRequestService } from '../purchase-request.service';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('purchaseRequestService - budget codes (F25)', () => {
  it('fetches the assignable budget codes from the procurement-scoped endpoint', async () => {
    const codes = [
      { id: 1, code: 'E-1', name: 'Expense', external_account_type: 'Other Expense' },
    ];
    vi.mocked(api.get).mockResolvedValue({ data: codes });

    const result = await purchaseRequestService.getBudgetCodes();

    expect(api.get).toHaveBeenCalledWith('/procurement/budget-codes/');
    expect(result).toEqual(codes);
  });

  it('assigns one item budget code with PUT and only budget_code_id in the body', async () => {
    vi.mocked(api.put).mockResolvedValue({ data: { id: 7 } });

    await purchaseRequestService.assignItemBudgetCode(7, 3, 42);

    expect(api.put).toHaveBeenCalledWith(
      '/procurement/requests/7/items/3/budget-code/',
      { budget_code_id: 42 }
    );
  });
});
