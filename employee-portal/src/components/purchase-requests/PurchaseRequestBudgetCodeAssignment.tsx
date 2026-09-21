import type { BudgetCode, PurchaseRequest } from '@/types/purchase-request.types';

interface PurchaseRequestBudgetCodeAssignmentProps {
  request: PurchaseRequest;
  /** The approved assignable codes; null while loading, never filtered here. */
  budgetCodes: BudgetCode[] | null;
  loadError?: string | null;
  /** Item currently being saved, so its selector can be disabled. */
  savingItemId?: number | null;
  onAssign: (itemId: number, budgetCodeId: number) => void;
}

/**
 * F25: Accounts assigns the authoritative budget code per item.
 *
 * The employee's category is shown for context only - it never decides the
 * code. The selector lists exactly what the backend returned from the
 * Accounts-only budget-codes endpoint (Revenue / Other Income / Other
 * Expense); this component does no filtering of its own. The backend
 * remains authoritative for every rule.
 */
export function PurchaseRequestBudgetCodeAssignment({
  request,
  budgetCodes,
  loadError = null,
  savingItemId = null,
  onAssign,
}: PurchaseRequestBudgetCodeAssignmentProps) {
  const codesById = new Map((budgetCodes ?? []).map((code) => [code.id, code]));

  return (
    <div className="space-y-2 text-left" data-testid="budget-code-assignment">
      <div>
        <h3 className="text-sm font-semibold">Budget codes</h3>
        <p className="text-xs text-muted-foreground">
          Assign an accounting code to every item before verifying.
        </p>
      </div>

      {loadError && (
        <p role="alert" className="text-sm text-destructive">
          {loadError}
        </p>
      )}

      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr className="text-left">
              <th className="px-3 py-2 font-medium text-muted-foreground">Item</th>
              <th className="px-3 py-2 font-medium text-muted-foreground text-right">Qty</th>
              <th className="px-3 py-2 font-medium text-muted-foreground">Category</th>
              <th className="px-3 py-2 font-medium text-muted-foreground">Budget code</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {request.items.map((item) => {
              const current =
                item.budget_code_id != null ? codesById.get(item.budget_code_id) : undefined;
              const selectId = `budget-code-${item.id}`;
              return (
                <tr key={item.id}>
                  <td className="px-3 py-2 align-top font-medium">{item.description}</td>
                  <td className="px-3 py-2 align-top text-right tabular-nums">{item.quantity}</td>
                  <td className="px-3 py-2 align-top text-muted-foreground">
                    {item.category?.name ?? '—'}
                  </td>
                  <td className="px-3 py-2 align-top">
                    <label htmlFor={selectId} className="sr-only">
                      Budget code for {item.description}
                    </label>
                    <select
                      id={selectId}
                      className="w-full min-w-[14rem] rounded-md border bg-background px-2 py-1.5 text-sm"
                      value={item.budget_code_id ?? ''}
                      disabled={budgetCodes === null || savingItemId === item.id}
                      onChange={(event) => {
                        const value = Number(event.target.value);
                        if (value) onAssign(item.id, value);
                      }}
                    >
                      <option value="" disabled>
                        {budgetCodes === null ? 'Loading budget codes...' : 'Select budget code'}
                      </option>
                      {/* An already-assigned code outside the approved list (e.g. legacy
                          data) is still shown, not silently blanked. */}
                      {item.budget_code_id != null && !current && (
                        <option value={item.budget_code_id}>
                          Assigned code (not in the approved list)
                        </option>
                      )}
                      {(budgetCodes ?? []).map((code) => (
                        <option key={code.id} value={code.id}>
                          {code.code} — {code.name}
                        </option>
                      ))}
                    </select>
                    {current && (
                      <div className="mt-1 text-xs text-muted-foreground">
                        Assigned: {current.code} — {current.name}
                      </div>
                    )}
                    {item.budget_code_id == null && (
                      <div className="mt-1 text-xs text-amber-700">Not assigned</div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
